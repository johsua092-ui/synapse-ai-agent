"""Peer Link — invite-code verification, read-only by design.

Why this module exists instead of calling ``PairingStore.approve_code``:

``approve_code`` does two things Peer Link must not do on a stranger-facing
path.

1. It **mutates** state — it consumes the pending entry and writes the
   requester into the *platform* approved-user list. Peer Link's trust model
   is a separate, per-peer quarantine (see :mod:`gateway.peer_link.policy`);
   a valid invite code must prove *possession of an invitation*, not grant
   access to the Telegram/WhatsApp allowlist.
2. It is subject to the **per-platform lockout** in ``gateway.pairing``. On a
   public-facing endpoint that lockout is a denial-of-service vector: anyone
   who can submit bad codes can lock the whole ``peerlink`` platform for
   everyone. Peer Link keys its own rate limit and lockout per *peer id*
   instead, so one flooder can only ever lock itself out.

So verification here reads the pending file, compares in constant time, and
writes nothing. The caller (the owner, via ``peerlink approve``) remains the
only thing that grants trust — consistent with the project rule that the AI
never auto-approves.

Storage is read through :class:`gateway.pairing.PairingStore` so the
legacy/consolidated directory resolution and the hashing scheme stay in one
place; only ``approve_code``'s side effects are avoided.
"""

from __future__ import annotations

import hmac
import json
import time
from pathlib import Path
from typing import Any, Dict, List

#: Platform name Peer Link uses for its invite codes.
PLATFORM = "peerlink"


def _store():
    """Construct the shared PairingStore (lazy import: gateway deps are heavy)."""
    from gateway.pairing import PairingStore

    return PairingStore()


def _pending_entries(store: Any) -> Dict[str, Any]:
    """Read the pending map without going through any mutating helper."""
    path: Path = store._pending_path(PLATFORM)  # noqa: SLF001 - see module docstring
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def verify_invite_code(code: str, *, now: float | None = None) -> bool:
    """Return True iff *code* matches a live, unexpired pending invite.

    Pure read: no pending entry is consumed, no approved-user list is touched,
    and no per-platform failure counter is incremented. A wrong code here
    therefore cannot lock the platform out — the caller applies Peer Link's
    own per-peer rate limit instead.

    Expired entries (older than ``CODE_TTL_SECONDS``) never match. Malformed
    and legacy plaintext entries are skipped rather than raising, matching
    ``approve_code``'s tolerance for pre-upgrade files.
    """
    from gateway.pairing import CODE_TTL_SECONDS, PairingStore

    if not code:
        return False
    candidate = code.upper().strip()
    current = time.time() if now is None else now

    store = _store()
    pending = _pending_entries(store)

    matched = False
    for entry in pending.values():
        if not isinstance(entry, dict):
            continue
        salt_hex = entry.get("salt")
        stored_hash = entry.get("hash")
        created_at = entry.get("created_at")
        if not isinstance(salt_hex, str) or not isinstance(stored_hash, str):
            continue  # legacy/malformed entry: unusable under the hash schema
        if not isinstance(created_at, (int, float)):
            continue
        if (current - created_at) > CODE_TTL_SECONDS:
            continue  # expired
        try:
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            continue
        candidate_hash = PairingStore._hash_code(candidate, salt)  # noqa: SLF001
        # Constant-time compare, and keep scanning after a match so the loop
        # duration does not depend on which entry matched.
        if hmac.compare_digest(candidate_hash, stored_hash):
            matched = True

    return matched


def list_invites(*, now: float | None = None) -> List[Dict[str, Any]]:
    """Describe outstanding invites (never the code itself — only hashes exist)."""
    from gateway.pairing import CODE_TTL_SECONDS

    current = time.time() if now is None else now
    rows: List[Dict[str, Any]] = []
    for entry_id, entry in _pending_entries(_store()).items():
        if not isinstance(entry, dict):
            continue
        created_at = entry.get("created_at")
        if not isinstance(created_at, (int, float)):
            continue
        age = current - created_at
        if age > CODE_TTL_SECONDS:
            continue
        rows.append(
            {
                "entry_id": entry_id,
                "user_id": entry.get("user_id", ""),
                "user_name": entry.get("user_name", ""),
                "created_at": created_at,
                "expires_in": int(CODE_TTL_SECONDS - age),
            }
        )
    return rows
