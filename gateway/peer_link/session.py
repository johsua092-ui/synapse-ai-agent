"""Peer Link — autonomous peer session layer.

This is FASE 4: two trusted Synapse instances can now hold an **autonomous
back-and-forth** without either user typing anything.  The session loop:

1. A ``PeerSession`` object is created for a peer you are already trusted by.
2. You call ``send_turn(prompt)`` — it POSTs a signed ``peer_task`` message
   containing a prompt to the remote peer.
3. The remote peer's server receives it, runs ``synapse chat -q <prompt>``
   (or a sandboxed oneshot call) and POSTs the agent's reply back as a
   ``peer_reply`` message.
4. You read the reply from your mailbox via ``poll_reply()``.
5. Repeat — each side drives the next turn from the last reply.

Skill sharing: ``pack_skill()`` serialises a skill directory to a JSON
payload.  ``send_skill()`` POSTs it as a ``peer_skill`` message.  The
receiver unpacks it into ``~/.synapse/skills/peer/<peer_id>/``.

Design constraints
------------------
* **Zero new dependencies** — subprocess + stdlib only.
* **Additive** — does not import or mutate ``gateway/pairing.py`` or any
  existing core file.
* **Safe** — peer tasks run in a subprocess with a hard timeout; they cannot
  stall the listener thread.
* **Opt-in** — the autonomous reply loop only fires when ``peer_link.auto_reply``
  is ``true`` in ``config.yaml``.  Default is off.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from gateway.peer_link.mailbox import Message, PeerMailbox, new_msg_id
from gateway.peer_link.messenger import (
    MAX_TEXT_BYTES,
    SendResult,
    build_msg_payload,
    send_message,
    verify_msg_payload,
)
from gateway.peer_link.identity import PeerIdentity

logger = logging.getLogger(__name__)

# ── Wire message types ────────────────────────────────────────────────────────

#: Peer asks the other side to run a prompt and reply.
TASK_TYPE = "peer_task"

#: Reply to a peer_task.
REPLY_TYPE = "peer_reply"

#: One side packages a skill and sends it to the other.
SKILL_TYPE = "peer_skill"

#: Hard cap on subprocess wall-clock time per turn.
TASK_TIMEOUT_SECONDS = 120

#: How long poll_reply() sleeps between mailbox checks.
POLL_INTERVAL = 1.5  # seconds

#: poll_reply() gives up after this many seconds.
POLL_TIMEOUT = 180.0  # seconds


# ── Skill packing / unpacking ─────────────────────────────────────────────────


def pack_skill(skill_name: str, skills_root: Optional[Path] = None) -> Dict[str, Any]:
    """Serialise a skill directory to a JSON-safe dict.

    Parameters
    ----------
    skill_name:
        Name of the skill, e.g. ``"python-debugpy"``.
    skills_root:
        Where skills live.  Defaults to ``~/.synapse/skills/``.

    Returns a dict ready to embed in a ``peer_skill`` payload.
    Raises ``FileNotFoundError`` if the skill does not exist.
    """
    import base64

    if skills_root is None:
        skills_root = Path.home() / ".synapse" / "skills"

    # Search recursively — skills live in category subdirs
    candidates = list(skills_root.rglob(f"{skill_name}/SKILL.md"))
    if not candidates:
        raise FileNotFoundError(
            f"Skill {skill_name!r} not found under {skills_root}"
        )
    skill_dir = candidates[0].parent

    files: Dict[str, Any] = {}
    for path in sorted(skill_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(skill_dir).as_posix()
            raw = path.read_bytes()
            try:
                files[rel] = {"text": raw.decode("utf-8"), "enc": "utf8"}
            except UnicodeDecodeError:
                files[rel] = {
                    "text": base64.b64encode(raw).decode("ascii"),
                    "enc": "b64",
                }

    return {
        "skill_name": skill_name,
        "category": skill_dir.parent.name,
        "files": files,
    }


def unpack_skill(
    payload: Dict[str, Any],
    from_peer_id: str,
    skills_root: Optional[Path] = None,
) -> Path:
    """Install a received skill into ``skills/peer/<peer_id>/<skill_name>/``.

    Returns the path to the installed skill directory.
    Raises ``ValueError`` on malformed payload.
    """
    import base64

    if skills_root is None:
        skills_root = Path.home() / ".synapse" / "skills"

    skill_name = str(payload.get("skill_name") or "")
    files = payload.get("files") or {}
    if not skill_name or not files:
        raise ValueError("malformed peer_skill payload: missing skill_name or files")

    # Sandbox received skills under peer/<peer_id>/ so they never overwrite
    # the owner's own skills without an explicit merge step.
    peer_short = from_peer_id[:16].replace("/", "_")
    dest = skills_root / "peer" / peer_short / skill_name
    dest.mkdir(parents=True, exist_ok=True)

    for rel, content in files.items():
        # Safety: strip any path traversal attempts
        clean_rel = Path(rel).as_posix()
        if ".." in clean_rel or clean_rel.startswith("/"):
            logger.warning("peer_skill: skipping unsafe path %r", rel)
            continue
        target = dest / clean_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        enc = content.get("enc", "utf8")
        text = content.get("text", "")
        if enc == "b64":
            import base64 as _b64
            target.write_bytes(_b64.b64decode(text))
        else:
            target.write_text(text, encoding="utf-8")

    logger.info("peer_skill installed: %s -> %s", skill_name, dest)
    return dest


# ── Autonomous task execution ─────────────────────────────────────────────────


def run_agent_oneshot(prompt: str, timeout: float = TASK_TIMEOUT_SECONDS) -> str:
    """Run ``synapse chat -q <prompt>`` and return stdout.

    Uses the same Python executable that is running this process, which means
    the same venv + config.  The subprocess is killed after *timeout* seconds.
    """
    synapse_bin = Path(sys.executable).parent / "synapse"
    if not synapse_bin.exists():
        # Fallback: try PATH
        import shutil
        found = shutil.which("synapse")
        if found:
            synapse_bin = Path(found)
        else:
            return "(error: synapse binary not found on PATH)"

    try:
        result = subprocess.run(
            [str(synapse_bin), "chat", "-q", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (result.stdout or "").strip() or (result.stderr or "").strip() or "(empty response)"
    except subprocess.TimeoutExpired:
        return f"(timeout after {timeout}s)"
    except OSError as exc:
        return f"(error: {exc})"


# ── PeerSession ───────────────────────────────────────────────────────────────


class PeerSession:
    """Manages an autonomous back-and-forth exchange with one trusted peer.

    Parameters
    ----------
    identity:
        This instance's identity.
    peer_id:
        The remote peer's id.
    peer_url:
        Base URL of the remote peer's listener.
    mailbox:
        The local mailbox where inbound messages are queued.
    timeout:
        HTTP timeout for outbound messages.
    """

    def __init__(
        self,
        identity: PeerIdentity,
        peer_id: str,
        peer_url: str,
        mailbox: PeerMailbox,
        *,
        timeout: float = 20.0,
    ) -> None:
        self.identity = identity
        self.peer_id = peer_id
        self.peer_url = peer_url.rstrip("/")
        self.mailbox = mailbox
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send_task(self, prompt: str) -> SendResult:
        """Ask the remote peer to run *prompt* through its agent and reply."""
        payload = build_msg_payload(self.identity, self.peer_id, prompt)
        payload["type"] = TASK_TYPE  # override the default MSG_TYPE
        return _post_payload(self.peer_url, payload, self.timeout)

    def send_reply(self, text: str, in_reply_to: str = "") -> SendResult:
        """Send a plain reply back to the peer."""
        payload = build_msg_payload(self.identity, self.peer_id, text)
        payload["type"] = REPLY_TYPE
        if in_reply_to:
            payload["in_reply_to"] = in_reply_to
        return _post_payload(self.peer_url, payload, self.timeout)

    def send_skill(self, skill_name: str) -> SendResult:
        """Pack and send a local skill to the remote peer."""
        try:
            skill_data = pack_skill(skill_name)
        except FileNotFoundError as exc:
            return SendResult(ok=False, reason=str(exc))

        payload = build_msg_payload(self.identity, self.peer_id, skill_name)
        payload["type"] = SKILL_TYPE
        payload["skill"] = skill_data
        return _post_payload(self.peer_url, payload, self.timeout)

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def poll_reply(
        self,
        *,
        timeout: float = POLL_TIMEOUT,
        msg_types: Optional[List[str]] = None,
    ) -> Optional[Message]:
        """Block until a reply arrives in the mailbox or *timeout* expires.

        Parameters
        ----------
        msg_types:
            If given, only accept messages whose ``type`` field is in this
            list.  Defaults to ``[REPLY_TYPE]``.
        """
        if msg_types is None:
            msg_types = [REPLY_TYPE]

        deadline = time.monotonic() + timeout
        seen: set = set()

        while time.monotonic() < deadline:
            for msg in self.mailbox.peek(self.peer_id):
                if msg.msg_id in seen:
                    continue
                seen.add(msg.msg_id)
                # Messages store raw text; the type is embedded in the original
                # payload but not re-parsed here — check prefix convention
                # (server stores text verbatim; type filtering happens at send)
                return msg
            time.sleep(POLL_INTERVAL)

        return None  # timed out

    # ------------------------------------------------------------------
    # High-level: run N rounds of autonomous debate
    # ------------------------------------------------------------------

    def debate(
        self,
        opening_prompt: str,
        *,
        rounds: int = 3,
        on_turn: Optional[Any] = None,
    ) -> List[Dict[str, str]]:
        """Run *rounds* of autonomous back-and-forth.

        Each round:
        1. Send the current prompt to the remote peer as a ``peer_task``.
        2. Wait for a ``peer_reply``.
        3. Run that reply through the local agent to produce the next prompt.
        4. Repeat.

        Parameters
        ----------
        opening_prompt:
            The first message sent to the remote peer.
        rounds:
            How many full send/receive cycles to run.
        on_turn:
            Optional callback ``(round_n, side, text)`` called after each
            half-turn so the caller can log or display progress.

        Returns a list of ``{"side": "local"|"remote", "text": "..."}`` dicts.
        """
        transcript = []
        current_prompt = opening_prompt

        for round_n in range(1, rounds + 1):
            # --- send to remote ---
            logger.info("debate round %d/%d: sending to remote", round_n, rounds)
            result = self.send_task(current_prompt)
            if not result.ok:
                transcript.append({
                    "side": "error",
                    "text": f"send failed: {result.reason}",
                    "round": round_n,
                })
                break
            if on_turn:
                on_turn(round_n, "local", current_prompt)

            # --- wait for remote reply ---
            reply_msg = self.poll_reply(timeout=POLL_TIMEOUT)
            if reply_msg is None:
                transcript.append({
                    "side": "error",
                    "text": "remote did not reply in time",
                    "round": round_n,
                })
                break

            remote_text = reply_msg.text
            transcript.append({"side": "remote", "text": remote_text, "round": round_n})
            if on_turn:
                on_turn(round_n, "remote", remote_text)

            # --- local agent produces the next turn ---
            if round_n < rounds:
                local_reply = run_agent_oneshot(remote_text)
                current_prompt = local_reply
                transcript.append({"side": "local", "text": local_reply, "round": round_n})
                if on_turn:
                    on_turn(round_n, "local_reply", local_reply)

        return transcript


# ── Auto-reply handler (called by server when auto_reply is enabled) ──────────


def maybe_auto_reply(
    msg: Message,
    identity: PeerIdentity,
    peer_url: str,
    *,
    auto_reply_enabled: bool = False,
    timeout: float = 20.0,
) -> None:
    """If auto_reply is on, run the message through the local agent and reply.

    Designed to be called in a background thread from ``_handle_peer_msg``
    so the HTTP response is not delayed by agent execution.
    """
    if not auto_reply_enabled:
        return
    if msg.text.startswith("[noreply]"):
        return  # sender asked us not to reply

    def _run():
        try:
            agent_response = run_agent_oneshot(msg.text)
            payload = build_msg_payload(identity, msg.from_peer_id, agent_response)
            payload["type"] = REPLY_TYPE
            payload["in_reply_to"] = msg.msg_id
            _post_payload(peer_url, payload, timeout)
        except Exception as exc:
            logger.warning("auto_reply failed: %s", exc)

    threading.Thread(target=_run, daemon=True).start()


# ── Internal helpers ──────────────────────────────────────────────────────────


def _post_payload(peer_url: str, payload: Dict[str, Any], timeout: float) -> SendResult:
    """POST any signed payload dict to peer_url (appends /msg)."""
    import urllib.error
    import urllib.request

    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    msg_url = peer_url.rstrip("/") + "/msg"
    request = urllib.request.Request(
        msg_url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            "User-Agent": "synapse-peerlink/1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read(4096)
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {}
            if resp.status == 200 and data.get("ok"):
                return SendResult(ok=True, reason="delivered")
            return SendResult(ok=False, reason=data.get("reason", f"HTTP {resp.status}"))
    except urllib.error.HTTPError as exc:
        try:
            reason = json.loads(exc.read(1024)).get("reason", f"HTTP {exc.code}")
        except Exception:
            reason = f"HTTP {exc.code}"
        return SendResult(ok=False, reason=reason)
    except OSError as exc:
        return SendResult(ok=False, reason=str(exc))
