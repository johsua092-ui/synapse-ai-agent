"""Peer Link — web dashboard HTTP handler.

Serves the control panel HTML and a thin JSON REST API that bridges the
CLI commands to the browser.  Mounted alongside the existing handshake
handler so a single ``synapse peerlink serve --dashboard`` flag opens both.

REST endpoints (all prefixed with /dashboard):
    GET  /dashboard             → serves the HTML UI
    GET  /dashboard/api/peerlink/status    → identity + stats
    GET  /dashboard/api/peerlink/peers     → list all peers
    POST /dashboard/api/peerlink/approve   → {peer_id}
    POST /dashboard/api/peerlink/block     → {peer_id}
    DELETE /dashboard/api/peerlink/peers/<id> → revoke
    GET  /dashboard/api/peerlink/inbox     → list messages
    DELETE /dashboard/api/peerlink/inbox   → drain
    POST /dashboard/api/peerlink/send      → {peer_id, text}
    POST /dashboard/api/peerlink/mode      → {mode}
    POST /dashboard/api/peerlink/invite    → {peer}
    POST /dashboard/api/peerlink/debate    → {peer_id, prompt, rounds}
    POST /dashboard/api/peerlink/skill-share → {peer_id, skill}
    GET  /dashboard/api/peerlink/skills    → list local skills

Design: zero new runtime dependencies — stdlib http.server only.
Additive: does not modify server.py, pairing.py, or any existing handler.
"""

from __future__ import annotations

import json
import logging
import pathlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from gateway.peer_link.identity import PeerIdentity
from gateway.peer_link.mailbox import PeerMailbox
from gateway.peer_link.messenger import send_message
from gateway.peer_link.policy import AdmissionMode, AdmissionPolicy
from gateway.peer_link.session import PeerSession, pack_skill

logger = logging.getLogger(__name__)

DASHBOARD_PATH = "/dashboard"
API_PREFIX = "/dashboard/api/peerlink"

# Path to the bundled HTML file (same directory as this module)
_HTML_FILE = pathlib.Path(__file__).parent / "dashboard.html"


class DashboardHandler(BaseHTTPRequestHandler):
    """Serves the Peer Link web dashboard and JSON API."""

    server_version = "PeerLinkDashboard"
    sys_version = ""

    # Injected by DashboardServer
    identity: PeerIdentity
    policy: AdmissionPolicy
    mailbox: PeerMailbox
    html_path: pathlib.Path

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.info("dashboard %s - %s", self.client_address[0], format % args)

    # ── routing ────────────────────────────────────────────────────────

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == DASHBOARD_PATH or path == DASHBOARD_PATH + "/":
            self._serve_html()
        elif path.startswith(API_PREFIX):
            sub = path[len(API_PREFIX):]
            if sub == "/status":
                self._api_status()
            elif sub == "/peers":
                self._api_list_peers()
            elif sub == "/inbox":
                self._api_inbox()
            elif sub == "/skills":
                self._api_skills()
            else:
                self._json(404, {"error": "not found"})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if not path.startswith(API_PREFIX):
            self._json(404, {"error": "not found"})
            return
        body = self._read_body()
        sub = path[len(API_PREFIX):]
        routes = {
            "/approve": self._api_approve,
            "/block": self._api_block,
            "/send": self._api_send,
            "/mode": self._api_set_mode,
            "/invite": self._api_invite,
            "/debate": self._api_debate,
            "/skill-share": self._api_skill_share,
        }
        handler = routes.get(sub)
        if handler:
            handler(body)
        else:
            self._json(404, {"error": "unknown action"})

    def do_DELETE(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        sub = path[len(API_PREFIX):]
        if sub == "/inbox":
            self.mailbox.drain()
            self._json(200, {"ok": True})
        elif sub.startswith("/peers/"):
            peer_id = sub[len("/peers/"):]
            self.policy.revoke(peer_id)
            self._json(200, {"ok": True})
        else:
            self._json(404, {"error": "not found"})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ── API handlers ───────────────────────────────────────────────────

    def _api_status(self) -> None:
        ep = self._own_endpoint()
        self._json(200, {
            "peer_id": self.identity.peer_id,
            "public_key": self.identity.public_key_b64,
            "mode": self.policy.mode.value,
            "address": ep,
            "trusted": len(self.policy.trusted()),
            "pending": len(self.policy.pending()),
            "blocked": len(self.policy.blocked()),
        })

    def _api_list_peers(self) -> None:
        peers = self.policy.list_peers()
        self._json(200, {"peers": peers})

    def _api_approve(self, body: Dict) -> None:
        peer_id = body.get("peer_id", "")
        ok = self.policy.promote(peer_id)
        self._json(200 if ok else 400, {"ok": ok})

    def _api_block(self, body: Dict) -> None:
        peer_id = body.get("peer_id", "")
        ok = self.policy.block(peer_id)
        self._json(200 if ok else 400, {"ok": ok})

    def _api_inbox(self) -> None:
        msgs = self.mailbox.peek()
        self._json(200, {"messages": [m.to_dict() for m in msgs]})

    def _api_send(self, body: Dict) -> None:
        peer_id = body.get("peer_id", "")
        text = body.get("text", "")
        peer_url = self._peer_url(peer_id)
        if not peer_url:
            self._json(400, {"ok": False, "reason": "peer has no address or is not trusted"})
            return
        result = send_message(self.identity, peer_url, peer_id, text)
        self._json(200 if result.ok else 502, {"ok": result.ok, "reason": result.reason})

    def _api_set_mode(self, body: Dict) -> None:
        mode_str = body.get("mode", "")
        try:
            mode = AdmissionMode(mode_str)
            self.policy.set_mode(mode)
            self._json(200, {"ok": True, "mode": mode.value})
        except ValueError:
            self._json(400, {"ok": False, "reason": f"unknown mode {mode_str!r}"})

    def _api_invite(self, body: Dict) -> None:
        from gateway.pairing import PairingStore
        from gateway.peer_link.client import build_share_link
        peer_label = body.get("peer", "friend")
        store = PairingStore()
        code = store.generate_code("peerlink", peer_label, "")
        if code is None:
            self._json(429, {"ok": False, "reason": "rate limited or queue full"})
            return
        ep = self._own_endpoint() or ""
        link = build_share_link(ep, code) if ep else code
        self._json(200, {"ok": True, "code": code, "share_link": link})

    def _api_debate(self, body: Dict) -> None:
        peer_id = body.get("peer_id", "")
        prompt = body.get("prompt", "")
        rounds = int(body.get("rounds", 3))
        peer_url = self._peer_url(peer_id)
        if not peer_url:
            self._json(400, {"ok": False, "reason": "peer not found or has no address"})
            return
        session = PeerSession(self.identity, peer_id, peer_url, self.mailbox)
        transcript = session.debate(prompt, rounds=rounds)
        self._json(200, {"ok": True, "transcript": transcript})

    def _api_skill_share(self, body: Dict) -> None:
        peer_id = body.get("peer_id", "")
        skill_name = body.get("skill", "")
        peer_url = self._peer_url(peer_id)
        if not peer_url:
            self._json(400, {"ok": False, "reason": "peer not found"})
            return
        session = PeerSession(self.identity, peer_id, peer_url, self.mailbox)
        result = session.send_skill(skill_name)
        self._json(200 if result.ok else 502, {"ok": result.ok, "reason": result.reason})

    def _api_skills(self) -> None:
        skills_root = pathlib.Path.home() / ".synapse" / "skills"
        skills = []
        if skills_root.exists():
            for skill_md in sorted(skills_root.rglob("SKILL.md"))[:50]:
                cat = skill_md.parent.parent.name
                name = skill_md.parent.name
                if name.startswith("peer"):
                    continue
                skills.append({"name": name, "category": cat})
        self._json(200, {"skills": skills})

    # ── HTML serving ───────────────────────────────────────────────────

    def _serve_html(self) -> None:
        html_path = self.html_path
        if html_path.exists():
            body = html_path.read_bytes()
        else:
            # Fallback: minimal redirect page
            body = b"<html><body><p>Dashboard HTML not found. Run from repo root.</p></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # ── plumbing ───────────────────────────────────────────────────────

    def _json(self, status: int, payload: Dict) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > 65536:
                return {}
            raw = self.rfile.read(length)
            return json.loads(raw)
        except Exception:
            return {}

    def _own_endpoint(self) -> Optional[str]:
        try:
            from gateway.peer_link.endpoint import EndpointRegistry
            data_dir = pathlib.Path.home() / ".synapse" / "peer_link"
            reg = EndpointRegistry(data_dir)
            return reg.own_url(create=False)
        except Exception:
            return None

    def _peer_url(self, peer_id: str) -> Optional[str]:
        peers = self.policy.list_peers()
        for p in peers:
            if p.get("peer_id") == peer_id and p.get("state") == "trusted":
                addr = p.get("address") or p.get("url") or ""
                if addr and not addr.startswith("http"):
                    addr = "https://" + addr
                return addr or None
        return None


class DashboardServer:
    """Runs the web dashboard on a separate port from the handshake server."""

    DEFAULT_PORT = 7070

    def __init__(
        self,
        identity: PeerIdentity,
        policy: AdmissionPolicy,
        mailbox: PeerMailbox,
        *,
        host: str = "127.0.0.1",
        port: int = DEFAULT_PORT,
        html_path: Optional[pathlib.Path] = None,
    ) -> None:
        self.identity = identity
        self.policy = policy
        self.mailbox = mailbox
        self.host = host
        self.port = port
        self.html_path = html_path or _HTML_FILE
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, *, background: bool = True) -> "DashboardServer":
        handler = type(
            "BoundDashboardHandler",
            (DashboardHandler,),
            {
                "identity": self.identity,
                "policy": self.policy,
                "mailbox": self.mailbox,
                "html_path": self.html_path,
            },
        )
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._httpd.daemon_threads = True
        self.port = self._httpd.server_address[1]
        if background:
            self._thread = threading.Thread(
                target=self._httpd.serve_forever, daemon=True
            )
            self._thread.start()
        else:
            self._httpd.serve_forever()
        return self

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}{DASHBOARD_PATH}"

    def __repr__(self) -> str:
        return f"DashboardServer(url={self.url!r})"
