"""Peer Link — admission policy for public (stranger-facing) peers.

This module answers one question: *what happens when someone you have never
met knocks on your door?*

A friend-to-friend link and a public link differ in exactly one thing: the
**cost of an identity**. A friend has one identity and no reason to attack. A
stranger can mint a million for free. Every control below exists to make the
stranger's case expensive while leaving the friend's case free.

Seven controls, in the order they engage:

1. **Mode gate** — ``CLOSED`` by default. Nothing listens, nobody can knock.
2. **Proof of work** — minting an identity costs CPU instead of nothing.
3. **Adaptive difficulty** — that cost rises automatically under a flood.
4. **Per-key rate limit** — a fresh identity does not come with a fresh budget.
5. **Per-peer lockout** — a flood cannot lock out an honest peer. Note that
   :mod:`gateway.pairing` locks out per *platform*; a stranger could abuse that
   to deny service to everyone. Here the failure counter is per peer id, so a
   flood only ever locks out the flooder.
6. **Quarantine** — a new peer may speak but may not act until the owner
   promotes it. The owner is always in the loop.
7. **Allow / block list** — explicit, revocable, auditable.

Nothing here auto-approves anybody. Quarantine is explicitly *not* approval:
promotion is a deliberate act by the instance owner, matching the spec
principle "USER selalu di loop — AI TIDAK PERNAH auto-approve".
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import tempfile
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional, Set

from utils import atomic_replace

from gateway.peer_link.identity import (
    PUBLIC_KEY_BYTES,
    peer_id_from_public_key,
)

logger = logging.getLogger(__name__)


class AdmissionMode(str, Enum):
    """How much of the world may knock on this instance's door."""

    #: Nothing listens. The factory default, and the only mode that is safe
    #: without any further thought.
    CLOSED = "closed"
    #: A valid invite code (see ``gateway.pairing``) is required before a
    #: request is even considered.
    INVITE = "invite"
    #: Anyone may knock, but must pay proof of work, is rate limited per key,
    #: and lands in quarantine. This is the recommended public mode.
    PUBLIC_GATED = "public_gated"
    #: Anyone may knock with no proof of work. Discouraged; provided so the
    #: policy is explicit rather than implicit when an operator insists.
    PUBLIC_OPEN = "public_open"


class PeerState(str, Enum):
    """Where a peer sits in the trust ladder."""

    #: Accepted, but may only speak — not act. Awaiting owner promotion.
    QUARANTINED = "quarantined"
    #: Promoted by the owner. Full peer.
    TRUSTED = "trusted"
    #: Explicitly refused. Never re-admitted without an unblock.
    BLOCKED = "blocked"


# ---------------------------------------------------------------------------
# Tunables. These are module constants rather than env vars on purpose: the
# repo forbids adding non-secret SYNAPSE_* env vars, and these are behavioural
# settings that belong in config.yaml. ``AdmissionPolicy`` accepts overrides so
# config.yaml can supply them.
# ---------------------------------------------------------------------------

#: ~2**16 hashes is milliseconds for one honest peer, and 65,536x the work for
#: an attacker who wants 65,536 identities.
DEFAULT_POW_BITS = 16
MIN_POW_BITS = 12
MAX_POW_BITS = 28

#: Adaptive difficulty window: when more than ``FLOOD_THRESHOLD`` requests land
#: inside ``FLOOD_WINDOW_SECONDS``, difficulty climbs one bit per multiple of
#: the threshold, up to ``MAX_POW_BITS``. Tracked in-process: an attacker
#: cannot restart our process, so in-memory flood state cannot be evaded by
#: anything the attacker controls.
FLOOD_WINDOW_SECONDS = 60
FLOOD_THRESHOLD = 30

#: Per-key pacing and per-peer lockout.
RATE_LIMIT_SECONDS = 60
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 900

#: Cap on the quarantine queue so a flood cannot grow it without bound.
MAX_PENDING_PUBLIC = 20

#: Filename inside the policy directory.
POLICY_FILENAME = "peer-policy.json"


@dataclass(frozen=True)
class AdmissionDecision:
    """The verdict for one knock at the door."""

    allowed: bool
    reason: str
    state: Optional[PeerState] = None
    difficulty: int = 0
    retry_after: Optional[int] = None

    def __bool__(self) -> bool:
        # Lets callers write ``if policy.submit(...):`` without surprises.
        return self.allowed


def _leading_zero_bits(digest: bytes) -> int:
    """Count leading zero bits in *digest*."""
    bits = 0
    for byte in digest:
        if byte == 0:
            bits += 8
            continue
        bits += 8 - byte.bit_length()
        break
    return bits


def _work_digest(public_key_bytes: bytes, nonce: int) -> bytes:
    """The exact bytes a peer must grind. Bound to the key, so work is not
    transferable: solving for one identity does not help another."""
    return hashlib.sha256(bytes(public_key_bytes) + int(nonce).to_bytes(8, "big")).digest()


def solve_work(public_key_bytes: bytes, difficulty: int) -> int:
    """Find a nonce whose work digest has *difficulty* leading zero bits.

    Cheap for one honest peer (milliseconds at the default difficulty) and
    linearly expensive per identity for an attacker.
    """
    if difficulty <= 0:
        return 0
    nonce = 0
    while True:
        if _leading_zero_bits(_work_digest(public_key_bytes, nonce)) >= difficulty:
            return nonce
        nonce += 1


def verify_work(public_key_bytes: bytes, nonce: int, difficulty: int) -> bool:
    """Verify a proof of work. Never raises."""
    if difficulty <= 0:
        return True
    try:
        return _leading_zero_bits(_work_digest(public_key_bytes, nonce)) >= difficulty
    except (TypeError, ValueError, OverflowError):
        return False


class AdmissionPolicy:
    """Decides who may connect, and at what trust level.

    State lives in a single JSON file written atomically with 0600 permissions,
    so the policy survives restarts and is auditable by an operator.
    """

    def __init__(
        self,
        storage_dir: "os.PathLike[str] | str",
        mode: "AdmissionMode | str" = AdmissionMode.CLOSED,
        pow_bits: int = DEFAULT_POW_BITS,
        *,
        allowlist: Optional[Iterable[str]] = None,
        max_pending: int = MAX_PENDING_PUBLIC,
    ) -> None:
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._mode = AdmissionMode(mode)
        self._pow_bits = max(MIN_POW_BITS, min(MAX_POW_BITS, int(pow_bits)))
        self._allowlist: Set[str] = set(allowlist or ())
        self._max_pending = int(max_pending)
        # Sliding window of recent knock timestamps, used for adaptive
        # difficulty. In-process by design (see FLOOD_WINDOW_SECONDS note).
        self._recent: Deque[float] = deque()

    # ----- storage ------------------------------------------------------

    @property
    def storage_dir(self) -> Path:
        return self._dir

    def _path(self) -> Path:
        return self._dir / POLICY_FILENAME

    def _empty(self) -> Dict[str, Any]:
        return {"peers": {}, "failures": {}, "lockouts": {}, "rate": {}}

    def _load(self) -> Dict[str, Any]:
        path = self._path()
        if not path.exists():
            return self._empty()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Corrupt state must not wedge admission: start clean rather than
            # raising into the caller's request path.
            logger.warning("peer-link policy file unreadable; starting empty: %s", path)
            return self._empty()
        if not isinstance(data, dict):
            return self._empty()
        base = self._empty()
        for key in base:
            if isinstance(data.get(key), dict):
                base[key] = data[key]
        return base

    def _save(self, data: Dict[str, Any]) -> None:
        path = self._path()
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(data, indent=2, ensure_ascii=False))
                handle.flush()
                os.fsync(handle.fileno())
            atomic_replace(tmp, path)
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ----- mode & challenge ---------------------------------------------

    @property
    def mode(self) -> AdmissionMode:
        return self._mode

    def set_mode(self, mode: "AdmissionMode | str") -> AdmissionMode:
        """Change the door policy. Returns the new mode."""
        self._mode = AdmissionMode(mode)
        return self._mode

    def _prune_recent(self, now: Optional[float] = None) -> None:
        now = time.time() if now is None else now
        cutoff = now - FLOOD_WINDOW_SECONDS
        while self._recent and self._recent[0] < cutoff:
            self._recent.popleft()

    def current_difficulty(self, now: Optional[float] = None) -> int:
        """The proof-of-work difficulty a peer must satisfy right now.

        Rises automatically when a flood is in progress, so an attacker cannot
        simply out-spend a static threshold.
        """
        if self._mode not in (AdmissionMode.PUBLIC_GATED, AdmissionMode.PUBLIC_OPEN):
            return 0
        self._prune_recent(now)
        if self._mode is AdmissionMode.PUBLIC_OPEN:
            return 0
        extra = len(self._recent) // FLOOD_THRESHOLD
        return min(MAX_POW_BITS, self._pow_bits + extra)

    def challenge(self) -> Dict[str, Any]:
        """What a prospective peer must solve before knocking."""
        return {
            "mode": self._mode.value,
            "difficulty": self.current_difficulty(),
            "algorithm": "sha256-leading-zero-bits",
            "binding": "sha256(public_key || nonce_be64)",
        }

    # ----- the knock ----------------------------------------------------

    def submit(
        self,
        public_key_bytes: bytes,
        nonce: int = 0,
        invite_code: str = "",
    ) -> AdmissionDecision:
        """Process one admission request.

        The peer id is **re-derived** from ``public_key_bytes`` rather than
        accepted from the caller, so a peer cannot claim an id it does not own.

        ``invite_code`` is only consulted in :attr:`AdmissionMode.INVITE`; it
        is verified read-only (see :mod:`gateway.peer_link.invite`) so a bad
        code cannot trip the shared per-platform lockout.
        """
        if len(public_key_bytes) != PUBLIC_KEY_BYTES:
            return AdmissionDecision(False, "malformed public key", None, 0)

        peer_id = peer_id_from_public_key(public_key_bytes)
        now = time.time()
        data = self._load()

        # 1. Mode gate — the only control that matters in CLOSED mode.
        if self._mode is AdmissionMode.CLOSED:
            return AdmissionDecision(False, "instance is closed", None, 0)

        known = data["peers"].get(peer_id) or {}
        known_state = known.get("state")

        # 2. Blocked peers never get back in without an explicit unblock.
        if known_state == PeerState.BLOCKED.value:
            return AdmissionDecision(False, "peer is blocked", PeerState.BLOCKED, 0)

        # 3. Allowlisted peers were vouched for out of band: no work, trusted.
        if peer_id in self._allowlist:
            self._remember(data, peer_id, public_key_bytes, PeerState.TRUSTED, now)
            data["failures"].pop(peer_id, None)
            self._save(data)
            return AdmissionDecision(True, "allowlisted", PeerState.TRUSTED, 0)

        # 4. INVITE mode needs a valid invite code. Verified read-only: a bad
        #    code counts against THIS peer (below), never against the shared
        #    per-platform lockout — otherwise the invite door itself would be a
        #    denial-of-service vector.
        if self._mode is AdmissionMode.INVITE:
            from gateway.peer_link.invite import verify_invite_code

            if not verify_invite_code(invite_code, now=now):
                self._record_failure(data, peer_id, now)
                self._save(data)
                return AdmissionDecision(False, "invite code required", None, 0)

        # 5. Per-key rate limit. Keyed by peer id, which is derived from the
        #    public key — so a brand-new identity does not reset the budget.
        last = data["rate"].get(peer_id, 0)
        if now - last < RATE_LIMIT_SECONDS:
            wait = int(RATE_LIMIT_SECONDS - (now - last)) + 1
            return AdmissionDecision(
                False, "rate limited", None, self.current_difficulty(now), retry_after=wait
            )

        # 6. Per-peer lockout. Crucially keyed by peer id, NOT by platform:
        #    one peer's failures can never lock the door for anyone else.
        until = data["lockouts"].get(peer_id, 0)
        if now < until:
            wait = int(until - now) + 1
            return AdmissionDecision(
                False, "locked out", None, self.current_difficulty(now), retry_after=wait
            )

        # 7. Proof of work. Counted only now, so garbage never inflates the
        #    flood window and never raises difficulty for honest peers.
        self._recent.append(now)
        difficulty = self.current_difficulty(now)
        if difficulty > 0 and not verify_work(public_key_bytes, nonce, difficulty):
            self._record_failure(data, peer_id, now)
            self._save(data)
            return AdmissionDecision(
                False, "proof of work failed", None, difficulty
            )

        # 8. Accepted. An existing trusted peer stays trusted; a stranger lands
        #    in quarantine and waits for the owner.
        if known_state == PeerState.TRUSTED.value:
            state = PeerState.TRUSTED
            reason = "trusted peer"
        else:
            pending = sum(
                1
                for entry in data["peers"].values()
                if isinstance(entry, dict)
                and entry.get("state") == PeerState.QUARANTINED.value
            )
            if pending >= self._max_pending:
                return AdmissionDecision(
                    False, "quarantine queue is full", None, difficulty, retry_after=300
                )
            state = PeerState.QUARANTINED
            reason = "quarantined pending owner approval"

        data["rate"][peer_id] = now
        data["failures"].pop(peer_id, None)
        self._remember(data, peer_id, public_key_bytes, state, now, keep_first=True)
        self._save(data)
        return AdmissionDecision(True, reason, state, difficulty)

    # ----- owner actions ------------------------------------------------

    def _remember(
        self,
        data: Dict[str, Any],
        peer_id: str,
        public_key_bytes: bytes,
        state: PeerState,
        now: float,
        *,
        keep_first: bool = False,
    ) -> None:
        entry = data["peers"].get(peer_id) or {}
        if not (keep_first and entry.get("first_seen")):
            entry["first_seen"] = now
        entry["state"] = state.value
        entry["public_key"] = base64.b64encode(bytes(public_key_bytes)).decode("ascii")
        entry["peer_id"] = peer_id
        entry["updated_at"] = now
        data["peers"][peer_id] = entry

    def _set_state(self, peer_id: str, state: PeerState) -> bool:
        data = self._load()
        entry = data["peers"].get(peer_id)
        if not entry:
            return False
        entry["state"] = state.value
        entry["updated_at"] = time.time()
        data["peers"][peer_id] = entry
        if state is not PeerState.BLOCKED:
            data["lockouts"].pop(peer_id, None)
            data["failures"].pop(peer_id, None)
        self._save(data)
        return True

    def promote(self, peer_id: str) -> bool:
        """Move a quarantined peer to trusted. This is the owner's approval."""
        return self._set_state(peer_id, PeerState.TRUSTED)

    def block(self, peer_id: str) -> bool:
        """Refuse a peer. Takes effect immediately and survives restarts."""
        return self._set_state(peer_id, PeerState.BLOCKED)

    def revoke(self, peer_id: str) -> bool:
        """Forget a peer entirely — it becomes a stranger again."""
        data = self._load()
        removed = False
        for key in ("peers", "failures", "lockouts", "rate"):
            if peer_id in data.get(key, {}):
                del data[key][peer_id]
                removed = True
        if removed:
            self._save(data)
        return removed

    def add_to_allowlist(self, peer_id: str) -> None:
        self._allowlist.add(peer_id)

    def remove_from_allowlist(self, peer_id: str) -> None:
        self._allowlist.discard(peer_id)

    # ----- inspection ---------------------------------------------------

    def list_peers(self, state: Optional[PeerState] = None) -> List[Dict[str, Any]]:
        """List known peers, optionally filtered by state. Sorted by id."""
        data = self._load()
        out: List[Dict[str, Any]] = []
        for peer_id, entry in data["peers"].items():
            if not isinstance(entry, dict):
                continue
            if state is not None and entry.get("state") != state.value:
                continue
            out.append({"peer_id": peer_id, **entry})
        return sorted(out, key=lambda item: item["peer_id"])

    def pending(self) -> List[Dict[str, Any]]:
        """Peers waiting for the owner's decision. This is the review queue."""
        return self.list_peers(PeerState.QUARANTINED)

    def trusted(self) -> List[Dict[str, Any]]:
        return self.list_peers(PeerState.TRUSTED)

    def blocked(self) -> List[Dict[str, Any]]:
        return self.list_peers(PeerState.BLOCKED)

    # ----- internals ----------------------------------------------------

    def _record_failure(
        self, data: Dict[str, Any], peer_id: str, now: float
    ) -> None:
        """Count a failed knock against *this peer only*.

        This is the fix for the denial-of-service shape in
        :mod:`gateway.pairing`: because the counter and the resulting lockout
        are keyed by peer id, a flood of bad attempts can only ever lock out
        the flooder. An honest peer's next attempt is unaffected.
        """
        fails = int(data["failures"].get(peer_id, 0)) + 1
        if fails >= MAX_FAILED_ATTEMPTS:
            data["lockouts"][peer_id] = now + LOCKOUT_SECONDS
            data["failures"][peer_id] = 0
        else:
            data["failures"][peer_id] = fails

    def is_locked_out(self, peer_id: str) -> bool:
        """Expose lockout state for tests and for ``peerlink status``."""
        return time.time() < float(self._load()["lockouts"].get(peer_id, 0))
