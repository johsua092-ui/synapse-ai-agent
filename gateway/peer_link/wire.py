"""Peer Link — the handshake wire protocol.

Two Synapse instances that have never met must end a conversation knowing, with
certainty, *who they are talking to*. TLS cannot tell them that: a certificate
proves a hostname, not an identity, and it says nothing at all once a relay or
a proxy is in the middle. So Peer Link authenticates with the Ed25519 keys in
:mod:`gateway.peer_link.identity`, on top of whatever transport carries them.

The handshake is three messages:

  ``hello``    client -> server   "here is my key, my proof of work, my challenge"
  ``welcome``  server -> client   "accepted; here is my key, signed"
  ``confirm``  client -> server   "signed with the key I claimed"

Both sides sign a transcript that includes **both** challenges and **both** peer
ids. That binding is what stops the obvious attacks:

  * *Replay* — a captured ``confirm`` is useless against a new challenge, and
    the challenge is 32 bytes of CSPRNG output, fresh per attempt.
  * *Reflection* — the two transcripts are prefixed differently, so a signature
    made for one direction never verifies in the other. Without the prefix,
    an attacker could bounce a server's own ``welcome`` signature back at it.
  * *Impersonation* — a peer id is derived from the public key
    (:func:`gateway.peer_link.identity.peer_id_from_public_key`), so claiming
    someone else's id while holding a different key fails to verify.

This module is deliberately transport-free and dependency-free: it computes
bytes and nothing else, so it is testable without a socket and reusable over
HTTPS, a relay, or a pipe.
"""

from __future__ import annotations

import json
import secrets
from typing import Any, Dict, Optional

#: Bumped when the transcript or message set changes incompatibly. A peer that
#: does not understand a version must refuse rather than guess, so the field is
#: checked before any signature work.
HANDSHAKE_VERSION = 1

#: Message types. Kept as constants so a typo is an AttributeError, not a
#: silently-accepted unknown string.
HELLO = "hello"
WELCOME = "welcome"
CONFIRM = "confirm"
#: Ask what proof of work is currently required, *before* paying it. Without
#: this the client would have to guess a difficulty: too low and the hello is
#: refused, too high and an honest peer burns CPU for nothing. The answer is
#: not a secret — a proof of work nobody can price is not a proof of work.
CHALLENGE = "challenge"

#: Outcome states a server may report.
STATE_OK = "ok"
STATE_QUARANTINED = "quarantined"
STATE_DENIED = "denied"

#: Direction prefixes. These make the two transcripts disjoint, which is what
#: defeats reflection: a signature produced for ``welcome`` can never satisfy a
#: ``confirm`` check even though the fields are otherwise identical.
SERVER_PREFIX = b"peerlink-handshake-server\x00"
CLIENT_PREFIX = b"peerlink-handshake-client\x00"

#: Bound on a single request body. A handshake is a few hundred bytes; anything
#: larger is not a handshake, and refusing early keeps a hostile client from
#: making the server allocate without limit.
MAX_BODY_BYTES = 16 * 1024


def new_challenge() -> str:
    """A fresh 32-byte challenge, hex encoded.

    Each side mints one. Because they are unpredictable and per-attempt, an
    old signature is worthless: replay has nothing to replay into.
    """
    return secrets.token_hex(32)


def _field(value: object, name: str) -> bytes:
    """Encode one transcript field as ``len(name)=len(value)``-free, unambiguous bytes.

    Every field is length-prefixed. Without that, ``("ab", "c")`` and
    ``("a", "bc")`` would hash identically, and an attacker could shift bytes
    between adjacent fields to forge a transcript collision.
    """
    if not isinstance(value, str):
        raise ValueError(f"transcript field {name!r} must be a string")
    raw = value.encode("utf-8")
    return len(raw).to_bytes(4, "big") + raw


def _transcript(prefix: bytes, fields: Dict[str, str]) -> bytes:
    parts = [prefix]
    for name in sorted(fields):
        parts.append(_field(name, "field-name"))
        parts.append(_field(fields[name], name))
    return b"".join(parts)


def server_transcript(
    client_challenge: str,
    client_peer_id: str,
    server_peer_id: str,
    server_challenge: str,
) -> bytes:
    """The bytes the **server** signs in ``welcome``."""
    return _transcript(
        SERVER_PREFIX,
        {
            "client_challenge": client_challenge,
            "client_peer_id": client_peer_id,
            "server_challenge": server_challenge,
            "server_peer_id": server_peer_id,
        },
    )


def client_transcript(
    client_challenge: str,
    client_peer_id: str,
    server_peer_id: str,
    server_challenge: str,
) -> bytes:
    """The bytes the **client** signs in ``confirm``.

    Same fields as :func:`server_transcript` but a different prefix, so the two
    signatures live in disjoint domains.
    """
    return _transcript(
        CLIENT_PREFIX,
        {
            "client_challenge": client_challenge,
            "client_peer_id": client_peer_id,
            "server_challenge": server_challenge,
            "server_peer_id": server_peer_id,
        },
    )


def encode_message(message: Dict[str, Any]) -> bytes:
    """Serialise a handshake message to wire bytes.

    Sorted keys and no whitespace: the encoding is canonical, so two processes
    that agree on the dict agree on the bytes, which matters the moment a
    signature covers any part of it.
    """
    return json.dumps(message, sort_keys=True, separators=(",", ":")).encode("utf-8")


def decode_message(raw: bytes) -> Optional[Dict[str, Any]]:
    """Parse wire bytes, returning ``None`` for anything not a JSON object.

    Returning ``None`` instead of raising keeps a malformed frame from becoming
    a 500: a stranger sending garbage is expected traffic, not a bug.
    """
    if not raw or len(raw) > MAX_BODY_BYTES:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def is_supported_version(value: object) -> bool:
    """True iff *value* is the handshake version this build speaks."""
    return value == HANDSHAKE_VERSION
