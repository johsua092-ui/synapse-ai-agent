"""Peer Link — the listener.

Everything up to this module answers "who is this?" and "may they in?". This
module is the thing that actually *listens*, so a peer URL stops being a name
and starts being a service.

Why a listener at all, and why this one:

  * The alternative is to require every user to run a relay or buy a VPS. Most
    people have neither. A listener on the owner's own machine is the only
    shape where "you bring a domain, the software brings the service" is true.
  * It is stdlib ``http.server`` — no new dependency. A framework would add one
    for a service whose entire surface is two POST endpoints.
  * It is **off by default**. ``AdmissionMode.CLOSED`` is the factory default
    and the server refuses to start without an explicit mode, so an install
    that never asked for this feature never opens a port. That is the spec
    principle "AMAN by default — fitur MATI sampai user menyalakan".

Path routing, not subdomains: a peer is addressed as ``/peer/<label>`` on one
shared hostname. A wildcard subdomain needs a wildcard certificate, which needs
either a paid plan or DNS control over the apex — neither is guaranteed. One
hostname plus a path works with a single free certificate.

What this server deliberately does NOT do yet: carry peer *data*. The handshake
establishes a mutually authenticated, replay-resistant channel; sync and barter
ride on top of it and are not implemented. It is honest to say so rather than
to imply more.
"""

from __future__ import annotations

import base64
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from gateway.peer_link import wire
from gateway.peer_link.endpoint import PATH_PREFIX, validate_label
from gateway.peer_link.identity import (
    PeerIdentity,
    peer_id_from_public_key,
    public_key_from_b64,
)
from gateway.peer_link.policy import (
    AdmissionDecision,
    AdmissionMode,
    AdmissionPolicy,
    PeerState,
)

logger = logging.getLogger(__name__)

#: Default port for ``synapse peerlink serve``. 8443 rather than 443 because
#: binding 443 needs root and usually collides with an existing web server;
#: the docs cover fronting this with nginx when 443 is wanted.
DEFAULT_PORT = 8443

#: Endpoint paths. ``/peerlink/health`` is unauthenticated and leaks nothing but
#: liveness.
HEALTH_PATH = "/peerlink/health"

#: How long a ``hello`` stays valid awaiting its ``confirm``. Short, because a
#: handshake is two round trips back to back; a longer window only widens the
#: replay surface and lets abandoned challenges accumulate.
HANDSHAKE_TTL_SECONDS = 120

#: Cap on simultaneous half-open handshakes. Without a bound, a client that
#: sends ``hello`` and never ``confirm`` grows the pending map for free.
MAX_PENDING_HANDSHAKES = 256


class _PendingHandshakes:
    """Half-open handshakes, keyed by client peer id.

    This lives on the server, not the handler, because ``http.server`` builds a
    fresh handler instance per request: anything stored on ``self`` inside
    ``hello`` is gone by the time ``confirm`` arrives.

    Bounded in both time and size. A challenge that is never confirmed expires;
    if the map is full, the oldest entry is dropped rather than growing without
    limit. Both bounds are what stop an unauthenticated caller from turning
    this into a memory exhaustion vector.
    """

    def __init__(
        self,
        ttl: float = HANDSHAKE_TTL_SECONDS,
        max_entries: int = MAX_PENDING_HANDSHAKES,
    ) -> None:
        self._ttl = float(ttl)
        self._max = int(max_entries)
        self._lock = threading.Lock()
        self._entries: Dict[str, Dict[str, Any]] = {}

    def _prune(self, now: float) -> None:
        expired = [
            key for key, entry in self._entries.items()
            if now - entry["created_at"] > self._ttl
        ]
        for key in expired:
            del self._entries[key]

    def put(self, peer_id: str, data: Dict[str, Any]) -> None:
        now = time.time()
        with self._lock:
            self._prune(now)
            if len(self._entries) >= self._max and peer_id not in self._entries:
                oldest = min(self._entries, key=lambda k: self._entries[k]["created_at"])
                del self._entries[oldest]
            self._entries[peer_id] = {**data, "created_at": now}

    def take(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """Remove and return the pending entry, so a challenge is single-use.

        Deleting on read is what makes the handshake non-replayable even if an
        attacker captures both messages: the second ``confirm`` finds nothing.
        """
        now = time.time()
        with self._lock:
            self._prune(now)
            entry = self._entries.pop(peer_id, None)
        if entry is None:
            return None
        if now - entry["created_at"] > self._ttl:
            return None
        return entry


def _client_ip(handler: BaseHTTPRequestHandler) -> str:
    """Best-effort client address, for logs and per-IP flood accounting."""
    try:
        return str(handler.client_address[0])
    except (IndexError, TypeError):
        return "unknown"


class PeerLinkHandler(BaseHTTPRequestHandler):
    """Serves the Peer Link handshake for one instance.

    ``server_version`` is generic on purpose: the stock ``BaseHTTPRequestHandler``
    banner advertises the Python version, which is free reconnaissance.
    """

    server_version = "PeerLink"
    sys_version = ""

    # Injected by :class:`PeerLinkServer` when it builds the handler class.
    identity: PeerIdentity
    policy: AdmissionPolicy
    label: Optional[str]
    pending: _PendingHandshakes

    # ----- plumbing -----------------------------------------------------

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - signature fixed by http.server
        """Route access logs through ``logging`` instead of raw stderr."""
        logger.info("peerlink %s - %s", _client_ip(self), format % args)

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = wire.encode_message(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # A handshake is per-request state; caching it would be a replay aid.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> Optional[Dict[str, Any]]:
        """Read and parse the request body, bounded by ``wire.MAX_BODY_BYTES``.

        An over-long ``Content-Length`` is refused *before* reading, so a
        hostile client cannot make the server allocate arbitrarily.
        """
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            return None
        if length <= 0 or length > wire.MAX_BODY_BYTES:
            return None
        try:
            raw = self.rfile.read(length)
        except OSError:
            return None
        return wire.decode_message(raw)

    # ----- routes -------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - http.server's naming
        path = self.path.split("?", 1)[0].rstrip("/")
        if path == HEALTH_PATH:
            # Liveness only. No peer id, no mode, no version: a health endpoint
            # that describes the instance is an enumeration aid.
            self._send_json(200, {"status": "ok"})
            return
        if path == self._peer_path() or path.startswith(PATH_PREFIX):
            # A browser hitting a peer URL should get an explanation, not a
            # bare 404 — the URL is meant to be pasted between humans.
            self._send_json(
                200,
                {
                    "service": "synapse-peerlink",
                    "version": wire.HANDSHAKE_VERSION,
                    "hint": "POST a Peer Link handshake here.",
                },
            )
            return
        self._send_json(404, {"error": "not found"})

    def _peer_path(self) -> str:
        """This instance's own path, e.g. ``/peer/abc123``.

        ``PATH_PREFIX`` already ends in a slash (``/peer/``), so the label is
        appended directly. Joining with an extra slash would produce
        ``/peer//abc``, which nginx and most routers do not normalise.
        """
        return f"{PATH_PREFIX}{self.label}"

    def do_POST(self) -> None:  # noqa: N802 - http.server's naming
        path = self.path.split("?", 1)[0].rstrip("/")

        # The peer label in the path must match ours, when we have one. This is
        # not a secret (see the endpoint module) — it is a routing check, so a
        # request aimed at a different peer is refused rather than mis-served.
        if self.label and path != self._peer_path():
            self._send_json(404, {"error": "unknown peer"})
            return

        message = self._read_body()
        if message is None:
            self._send_json(400, {"error": "malformed request"})
            return

        kind = message.get("type")
        if kind == wire.CHALLENGE:
            self._handle_challenge()
            return
        if kind == wire.HELLO:
            self._handle_hello(message)
            return
        if kind == wire.CONFIRM:
            self._handle_confirm(message)
            return
        self._send_json(400, {"error": "unsupported message type"})

    # ----- handshake ----------------------------------------------------

    def _handle_challenge(self) -> None:
        """Report the proof of work currently required.

        Unauthenticated and cheap. Publishing the difficulty is what lets an
        honest peer price its work correctly instead of guessing; it gives an
        attacker nothing it could not measure by trying.
        """
        self._send_json(200, self.policy.challenge())

    def _handle_hello(self, message: Dict[str, Any]) -> None:
        """Step 1: a stranger introduces itself and pays its proof of work."""
        if not wire.is_supported_version(message.get("version")):
            self._send_json(409, {"error": "unsupported protocol version"})
            return

        try:
            client_key = public_key_from_b64(str(message.get("public_key") or ""))
        except ValueError:
            # Never echo the input back: it may be an attempt to forge a log line.
            self._send_json(400, {"error": "invalid public key"})
            return

        client_peer_id = peer_id_from_public_key(client_key)
        claimed = message.get("peer_id")
        if isinstance(claimed, str) and claimed and claimed != client_peer_id:
            # The id is derived from the key. A mismatch means someone is
            # claiming an identity they do not hold, so refuse before doing any
            # further work.
            self._send_json(403, {"error": "peer id does not match public key"})
            return

        client_challenge = str(message.get("challenge") or "")
        if len(client_challenge) != 64:
            self._send_json(400, {"error": "invalid challenge"})
            return

        try:
            nonce = int(message.get("nonce") or 0)
        except (TypeError, ValueError):
            nonce = -1  # fails verification below; not an exception path

        decision: AdmissionDecision = self.policy.submit(
            client_key, nonce=nonce, invite_code=str(message.get("invite_code") or "")
        )
        if not decision.allowed:
            payload: Dict[str, Any] = {"state": wire.STATE_DENIED, "reason": decision.reason}
            if decision.retry_after:
                payload["retry_after"] = decision.retry_after
            # 403 for a refusal, 429 when the peer should simply wait.
            self._send_json(429 if decision.retry_after else 403, payload)
            return

        server_challenge = wire.new_challenge()
        # Stored on the *server*, because http.server creates a fresh handler
        # per request and `self` does not survive from hello to confirm.
        self.pending.put(
            client_peer_id,
            {
                "client_peer_id": client_peer_id,
                "client_challenge": client_challenge,
                "server_challenge": server_challenge,
            },
        )

        transcript = wire.server_transcript(
            client_challenge, client_peer_id, self.identity.peer_id, server_challenge
        )
        signature = base64.b64encode(self.identity.sign(transcript)).decode("ascii")

        state = (
            wire.STATE_OK
            if decision.state is PeerState.TRUSTED
            else wire.STATE_QUARANTINED
        )
        self._send_json(
            200,
            {
                "type": wire.WELCOME,
                "version": wire.HANDSHAKE_VERSION,
                "state": state,
                "peer_id": self.identity.peer_id,
                "public_key": self.identity.public_key_b64,
                "challenge": server_challenge,
                "signature": signature,
            },
        )

    def _handle_confirm(self, message: Dict[str, Any]) -> None:
        """Step 2: the client proves it holds the key it claimed.

        A ``confirm`` that arrives without a preceding ``hello`` is refused: the
        server challenge it must sign is minted per ``hello``, so there is
        nothing for a bare ``confirm`` to prove.
        """
        try:
            client_key = public_key_from_b64(str(message.get("public_key") or ""))
        except ValueError:
            self._send_json(400, {"error": "invalid public key"})
            return

        client_peer_id = peer_id_from_public_key(client_key)
        # Single-use: taking the entry removes it, so a replayed confirm finds
        # nothing and cannot succeed twice. Keying by peer id also means a
        # confirm signed by a *different* key than the hello cannot find the
        # entry at all — the "identity changed mid-handshake" case is refused
        # by this lookup rather than by a separate comparison.
        pending = self.pending.take(client_peer_id)
        if not pending:
            self._send_json(400, {"error": "no handshake in progress"})
            return

        try:
            signature = base64.b64decode(str(message.get("signature") or ""), validate=True)
        except Exception:
            self._send_json(400, {"error": "invalid signature encoding"})
            return

        transcript = wire.client_transcript(
            pending["client_challenge"],
            client_peer_id,
            self.identity.peer_id,
            pending["server_challenge"],
        )
        if not PeerIdentity.verify(client_key, signature, transcript):
            self._send_json(403, {"error": "signature verification failed"})
            return

        # Mutually authenticated. Record the peer as having completed a
        # handshake so the owner sees it in `peerlink peers`, but grant nothing
        # further: promotion is still the owner's call.
        state = self.policy.mode
        logger.info(
            "peerlink handshake complete peer=%s mode=%s", client_peer_id, state.value
        )
        self._send_json(
            200,
            {
                "state": wire.STATE_OK,
                "peer_id": client_peer_id,
                "server_peer_id": self.identity.peer_id,
                "authenticated": True,
            },
        )


class PeerLinkServer:
    """Owns the listening socket and the handler configuration.

    Kept separate from the handler so tests can drive the handshake through
    :class:`PeerLinkHandler` directly without binding a port.
    """

    def __init__(
        self,
        identity: PeerIdentity,
        policy: AdmissionPolicy,
        *,
        host: str = "0.0.0.0",
        port: int = DEFAULT_PORT,
        label: Optional[str] = None,
    ) -> None:
        if label is not None and not validate_label(label):
            raise ValueError(f"unsafe peer label: {label!r}")
        if policy.mode is AdmissionMode.CLOSED:
            # Refusing here is the safety default made mechanical. A CLOSED
            # policy means "nothing listens", so starting a listener anyway
            # would contradict the mode and surprise the operator.
            raise ValueError(
                "refusing to listen while admission mode is 'closed'; "
                "run `synapse peerlink mode invite` (or public_gated) first"
            )
        self.identity = identity
        self.policy = policy
        self.host = host
        self.port = int(port)
        self.label = label
        self.pending = _PendingHandshakes()
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def address(self) -> Tuple[str, int]:
        """The address actually bound, which differs from the request when
        ``port=0`` asked the OS for a free port."""
        if self._httpd is None:
            return (self.host, self.port)
        host, port = self._httpd.server_address[:2]
        return (str(host), int(port))

    def start(self, *, background: bool = False) -> "PeerLinkServer":
        """Bind and serve. With ``background=True`` returns immediately."""
        # Fresh store per bind: a handshake cannot span a restart, and the
        # challenges are single-use anyway.
        self.pending = _PendingHandshakes()
        handler = type(
            "BoundPeerLinkHandler",
            (PeerLinkHandler,),
            {
                "identity": self.identity,
                "policy": self.policy,
                "label": self.label,
                "pending": self.pending,
            },
        )
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self._httpd.daemon_threads = True
        self.port = self._httpd.server_address[1]
        if background:
            self._thread = threading.Thread(
                target=self._httpd.serve_forever, name="peerlink-serve", daemon=True
            )
            self._thread.start()
        return self

    def serve_forever(self) -> None:
        if self._httpd is None:
            self.start()
        assert self._httpd is not None
        self._httpd.serve_forever()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def __repr__(self) -> str:
        # Key-free, like PeerIdentity.__repr__.
        return f"PeerLinkServer(peer_id={self.identity.peer_id!r}, address={self.address!r})"
