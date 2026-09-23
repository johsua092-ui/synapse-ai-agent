"""Peer Link — send messages to a trusted peer.

This is the client side of peer messaging: given a trusted peer's URL and
your own identity, sign and POST a message.  The server side lives in
:mod:`gateway.peer_link.server` (the ``/msg`` endpoint added there).

Design
------
* **Zero new dependencies** — stdlib urllib only, same as the handshake client.
* **Signed** — every message carries an Ed25519 signature so the receiver can
  confirm it really came from this instance and was not tampered with.
* **Stateless delivery** — fire-and-forget POST.  The peer queues it in its
  :class:`~gateway.peer_link.mailbox.PeerMailbox`.  No acks, no retries at this
  layer (a CLI wrapper can retry if the user wants that).
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

from gateway.peer_link import wire
from gateway.peer_link.identity import PeerIdentity
from gateway.peer_link.mailbox import new_msg_id

#: POST timeout for a send attempt.
DEFAULT_TIMEOUT = 15.0

#: Wire message type for a peer-to-peer text message.
MSG_TYPE = "peer_msg"

#: Maximum text length accepted by the receiver.
MAX_TEXT_BYTES = 8 * 1024  # 8 KB


@dataclass
class SendResult:
    ok: bool
    reason: str

    def __bool__(self) -> bool:
        return self.ok


def _msg_transcript(
    from_peer_id: str,
    to_peer_id: str,
    msg_id: str,
    text: str,
    ts: float,
) -> bytes:
    """Bytes the sender signs.

    Fields are sorted alphabetically and length-prefixed (same scheme as the
    handshake transcript) so the signature is unambiguous and collision-free.
    """
    # reuse the same transcript helper from wire — it length-prefixes each field
    from gateway.peer_link import wire as _wire  # local to avoid circular at module level

    prefix = b"peerlink-msg-v1\x00"
    fields = {
        "from_peer_id": from_peer_id,
        "msg_id": msg_id,
        "text": text,
        "to_peer_id": to_peer_id,
        "ts": f"{ts:.3f}",
    }
    parts = [prefix]
    for name in sorted(fields):
        raw_name = name.encode("utf-8")
        raw_val = fields[name].encode("utf-8")
        parts.append(len(raw_name).to_bytes(4, "big") + raw_name)
        parts.append(len(raw_val).to_bytes(4, "big") + raw_val)
    return b"".join(parts)


def build_msg_payload(
    identity: PeerIdentity,
    to_peer_id: str,
    text: str,
) -> Dict[str, Any]:
    """Construct a signed ``peer_msg`` payload ready to POST."""
    msg_id = new_msg_id()
    ts = time.time()
    transcript = _msg_transcript(
        from_peer_id=identity.peer_id,
        to_peer_id=to_peer_id,
        msg_id=msg_id,
        text=text,
        ts=ts,
    )
    sig = identity.sign(transcript)
    return {
        "type": MSG_TYPE,
        "version": wire.HANDSHAKE_VERSION,
        "from_peer_id": identity.peer_id,
        "to_peer_id": to_peer_id,
        "msg_id": msg_id,
        "ts": round(ts, 3),
        "text": text,
        "public_key": identity.public_key_b64,
        "signature": base64.b64encode(sig).decode("ascii"),
    }


def send_message(
    identity: PeerIdentity,
    peer_url: str,
    to_peer_id: str,
    text: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> SendResult:
    """Sign and POST a message to *peer_url*/msg.

    Parameters
    ----------
    identity:
        This instance's identity (used for signing and the ``from_peer_id``
        field).
    peer_url:
        Base URL of the peer (e.g. ``https://synz.zone.id/peer/abc123``).
        The function appends ``/msg``.
    to_peer_id:
        The receiver's peer id.  The server checks this matches its own id so
        a message routed to the wrong peer is rejected rather than silently
        queued.
    text:
        The message body, at most :data:`MAX_TEXT_BYTES` bytes when UTF-8
        encoded.
    """
    if not text or not text.strip():
        return SendResult(ok=False, reason="empty message")
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        return SendResult(ok=False, reason="message too long")

    payload = build_msg_payload(identity, to_peer_id, text)
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
            return SendResult(ok=False, reason=data.get("reason", f"status {resp.status}"))
    except urllib.error.HTTPError as exc:
        try:
            body_bytes = exc.read(1024)
            data = json.loads(body_bytes)
            reason = data.get("reason", f"HTTP {exc.code}")
        except Exception:
            reason = f"HTTP {exc.code}"
        return SendResult(ok=False, reason=reason)
    except OSError as exc:
        return SendResult(ok=False, reason=str(exc))


def verify_msg_payload(
    payload: Dict[str, Any],
    expected_to_peer_id: str,
) -> Optional[str]:
    """Verify the signature on an inbound ``peer_msg`` payload.

    Returns ``None`` on success, or a string reason on failure.
    """
    from gateway.peer_link.identity import public_key_from_b64, peer_id_from_public_key

    required = {"type", "version", "from_peer_id", "to_peer_id",
                "msg_id", "ts", "text", "public_key", "signature"}
    if not required.issubset(payload):
        return "missing fields"
    if payload["type"] != MSG_TYPE:
        return f"wrong type: {payload['type']!r}"
    if payload["version"] != wire.HANDSHAKE_VERSION:
        return "unsupported version"
    if payload["to_peer_id"] != expected_to_peer_id:
        return "to_peer_id mismatch"

    # Derive peer id from public key and check it matches the claimed from_peer_id
    try:
        pub = public_key_from_b64(payload["public_key"])
    except Exception:
        return "bad public_key"
    derived_id = peer_id_from_public_key(bytes(pub))
    if derived_id != payload["from_peer_id"]:
        return "from_peer_id does not match public_key"

    # Verify signature
    try:
        sig = base64.b64decode(payload["signature"])
    except Exception:
        return "bad signature encoding"
    transcript = _msg_transcript(
        from_peer_id=payload["from_peer_id"],
        to_peer_id=payload["to_peer_id"],
        msg_id=payload["msg_id"],
        text=payload["text"],
        ts=float(payload["ts"]),
    )
    from gateway.peer_link.identity import PeerIdentity as _PI
    if not _PI.verify(pub, sig, transcript):
        return "signature invalid"

    return None  # all good
