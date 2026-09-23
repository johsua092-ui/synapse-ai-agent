"""Tests for Peer Link admission policy — the public-peer door.

The central claim under test: **a stranger cannot harm an honest peer.**
Concretely, the denial-of-service shape that exists in ``gateway.pairing``
(lockout keyed per platform, so 5 bad attempts deny service to everyone) must
not be reproducible here, because the counter is keyed per peer id.

Every test writes only under ``tmp_path``.
"""

from __future__ import annotations

import json
import os
import stat
import time

import pytest

from gateway.peer_link.identity import PeerIdentity
from gateway.peer_link.policy import (
    LOCKOUT_SECONDS,
    MAX_FAILED_ATTEMPTS,
    RATE_LIMIT_SECONDS,
    AdmissionMode,
    AdmissionPolicy,
    PeerState,
    solve_work,
    verify_work,
)


def make_peer():
    """A fresh peer identity plus its raw public key."""
    ident = PeerIdentity.generate()
    return ident, ident.public_key_bytes


class TestModeGate:
    def test_closed_by_default_rejects_everyone(self, tmp_path):
        """The factory default must let nobody in — safe by default."""
        policy = AdmissionPolicy(tmp_path)
        assert policy.mode is AdmissionMode.CLOSED
        _, key = make_peer()
        decision = policy.submit(key)
        assert decision.allowed is False
        assert "closed" in decision.reason

    def test_closed_gate_precedes_everything_else(self, tmp_path):
        """Even a correctly-solved proof of work must not open a closed door."""
        policy = AdmissionPolicy(tmp_path)
        _, key = make_peer()
        # Difficulty is 0 while closed, so any nonce is "valid" work — the
        # mode gate must still refuse.
        assert policy.submit(key, nonce=0).allowed is False

    def test_invite_mode_requires_a_code(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.INVITE)
        _, key = make_peer()
        decision = policy.submit(key)
        assert decision.allowed is False
        assert "invite" in decision.reason

    def test_mode_can_be_changed(self, tmp_path):
        policy = AdmissionPolicy(tmp_path)
        assert policy.set_mode(AdmissionMode.INVITE) is AdmissionMode.INVITE
        assert policy.mode is AdmissionMode.INVITE

    def test_rejects_unknown_mode_string(self, tmp_path):
        with pytest.raises(ValueError):
            AdmissionPolicy(tmp_path, "not-a-mode")


class TestProofOfWork:
    def test_solve_then_verify(self):
        _, key = make_peer()
        nonce = solve_work(key, 12)
        assert verify_work(key, nonce, 12) is True

    def test_work_is_bound_to_the_key(self):
        """Solving for one identity must not help another — no transferable work."""
        _, key_a = make_peer()
        _, key_b = make_peer()
        nonce = solve_work(key_a, 12)
        assert verify_work(key_b, nonce, 12) is False

    def test_wrong_nonce_fails(self):
        _, key = make_peer()
        nonce = solve_work(key, 14)
        assert verify_work(key, nonce + 1, 14) is False

    def test_zero_difficulty_always_passes(self):
        _, key = make_peer()
        assert verify_work(key, 0, 0) is True

    def test_verify_never_raises_on_garbage(self):
        _, key = make_peer()
        for bad in (None, "x", -1, 2**80):
            assert verify_work(key, bad, 12) is False  # type: ignore[arg-type]

    def test_higher_difficulty_costs_more_work(self):
        """Difficulty must actually be monotonic in effort, or it is not a cost."""
        _, key = make_peer()
        low = solve_work(key, 8)
        high = solve_work(key, 14)
        # Expected work is 2**d, so the harder target needs a strictly larger
        # nonce with overwhelming probability.
        assert high > low

    def test_public_gated_rejects_unsolved_work(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        _, key = make_peer()
        decision = policy.submit(key, nonce=0)
        # nonce=0 has ~1/4096 chance of being valid; treat the general case.
        if not verify_work(key, 0, policy.current_difficulty()):
            assert decision.allowed is False
            assert "proof of work" in decision.reason

    def test_public_gated_accepts_solved_work_into_quarantine(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        _, key = make_peer()
        nonce = solve_work(key, policy.current_difficulty())
        decision = policy.submit(key, nonce=nonce)
        assert decision.allowed is True
        # Accepted is NOT approved — the owner still decides.
        assert decision.state is PeerState.QUARANTINED


class TestAdaptiveDifficulty:
    def test_difficulty_rises_under_flood(self, tmp_path):
        """An attacker cannot out-spend a static threshold: cost scales up."""
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        base = policy.current_difficulty()
        # Simulate a flood by recording many knocks inside the window.
        now = time.time()
        for i in range(200):
            policy._recent.append(now - 0.1 * i)  # noqa: SLF001 - test seam
        assert policy.current_difficulty(now) > base

    def test_difficulty_is_capped(self, tmp_path):
        """Adaptive difficulty must not grow without bound."""
        from gateway.peer_link.policy import MAX_POW_BITS

        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        now = time.time()
        for _ in range(100_000):
            policy._recent.append(now)  # noqa: SLF001 - test seam
        assert policy.current_difficulty(now) == MAX_POW_BITS

    def test_difficulty_falls_back_after_window_passes(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        now = time.time()
        for _ in range(200):
            policy._recent.append(now)  # noqa: SLF001 - test seam
        later = now + 3600
        assert policy.current_difficulty(later) == 12

    def test_failed_work_does_not_inflate_difficulty(self, tmp_path):
        """Garbage must not be able to raise the bar for honest peers."""
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=14)
        _, key = make_peer()
        before = policy.current_difficulty()
        for _ in range(50):
            policy.submit(key, nonce=1)
        # Only requests that reached the work check count, and failures are
        # rate-limited long before 50 of them land.
        assert policy.current_difficulty() <= before + 1


class TestPerKeyRateLimit:
    def test_same_key_is_rate_limited(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_OPEN)
        _, key = make_peer()
        assert policy.submit(key).allowed is True
        second = policy.submit(key)
        assert second.allowed is False
        assert second.retry_after and second.retry_after > 0

    def test_new_identity_does_not_reset_the_budget(self, tmp_path):
        """Rate limiting is per key, so minting identities does not buy budget.

        Each fresh key gets its own first request (unavoidable without a
        global cap), but the point is that a *used* key cannot simply mint a
        replacement to bypass its own limit — the limit follows the key.
        """
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_OPEN)
        _, key_a = make_peer()
        assert policy.submit(key_a).allowed is True
        assert policy.submit(key_a).allowed is False
        # Same key, still limited, after other keys have been seen.
        _, key_b = make_peer()
        policy.submit(key_b)
        assert policy.submit(key_a).allowed is False

    def test_rate_limit_expires(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_OPEN)
        _, key = make_peer()
        assert policy.submit(key).allowed is True
        # Rewind the recorded timestamp past the window.
        data = policy._load()  # noqa: SLF001 - test seam
        for pid in list(data["rate"]):
            data["rate"][pid] = time.time() - RATE_LIMIT_SECONDS - 1
        policy._save(data)  # noqa: SLF001 - test seam
        assert policy.submit(key).allowed is True


class TestPerPeerLockout_NoDenialOfService:
    """The core security claim: one peer's abuse cannot lock out another."""

    def test_lockout_is_keyed_per_peer_not_globally(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        victim, victim_key = make_peer()
        attacker, attacker_key = make_peer()

        # Victim connects legitimately first.
        victim_nonce = solve_work(victim_key, policy.current_difficulty())
        assert policy.submit(victim_key, victim_nonce).allowed is True
        policy.promote(victim.peer_id)
        assert policy.is_locked_out(victim.peer_id) is False

        # Attacker floods with bad proof of work.
        for _ in range(MAX_FAILED_ATTEMPTS + 3):
            policy.submit(attacker_key, nonce=1)

        # The attacker is locked out...
        assert policy.is_locked_out(attacker.peer_id) is True
        # ...and the victim is completely unaffected.
        assert policy.is_locked_out(victim.peer_id) is False

    def test_flood_does_not_block_a_different_peer_from_being_admitted(self, tmp_path):
        """The concrete regression: an honest new peer must still get in."""
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        _, attacker_key = make_peer()
        for _ in range(MAX_FAILED_ATTEMPTS + 3):
            policy.submit(attacker_key, nonce=1)

        honest, honest_key = make_peer()
        nonce = solve_work(honest_key, policy.current_difficulty())
        decision = policy.submit(honest_key, nonce=nonce)
        assert decision.allowed is True, (
            "an attacker's failures must not deny service to an honest peer"
        )

    def test_lockout_expires(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        _, key = make_peer()
        for _ in range(MAX_FAILED_ATTEMPTS):
            policy.submit(key, nonce=1)
        data = policy._load()  # noqa: SLF001 - test seam
        for pid in list(data["lockouts"]):
            data["lockouts"][pid] = time.time() - 1
        policy._save(data)  # noqa: SLF001 - test seam
        from gateway.peer_link.identity import peer_id_from_public_key

        assert policy.is_locked_out(peer_id_from_public_key(key)) is False

    def test_lockout_constant_is_bounded(self):
        """A lockout must expire on a human timescale, not forever."""
        assert 0 < LOCKOUT_SECONDS <= 24 * 3600


class TestQuarantineAndPromotion:
    def test_new_public_peer_lands_in_quarantine(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        _, key = make_peer()
        nonce = solve_work(key, policy.current_difficulty())
        decision = policy.submit(key, nonce=nonce)
        assert decision.state is PeerState.QUARANTINED
        assert len(policy.pending()) == 1

    def test_promotion_moves_peer_to_trusted(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        ident, key = make_peer()
        nonce = solve_work(key, policy.current_difficulty())
        policy.submit(key, nonce=nonce)
        assert policy.promote(ident.peer_id) is True
        assert [p["peer_id"] for p in policy.trusted()] == [ident.peer_id]
        assert policy.pending() == []

    def test_quarantine_is_not_approval(self, tmp_path):
        """Admission must never imply trust — the owner always decides."""
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        _, key = make_peer()
        nonce = solve_work(key, policy.current_difficulty())
        policy.submit(key, nonce=nonce)
        assert policy.trusted() == []
        assert len(policy.pending()) == 1

    def test_trusted_peer_stays_trusted_on_reconnect(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        ident, key = make_peer()
        nonce = solve_work(key, policy.current_difficulty())
        policy.submit(key, nonce=nonce)
        policy.promote(ident.peer_id)

        # Wait out the rate limit, then reconnect.
        data = policy._load()  # noqa: SLF001 - test seam
        for pid in list(data["rate"]):
            data["rate"][pid] = 0
        policy._save(data)  # noqa: SLF001 - test seam
        nonce = solve_work(key, policy.current_difficulty())
        decision = policy.submit(key, nonce=nonce)
        assert decision.allowed is True
        assert decision.state is PeerState.TRUSTED

    def test_quarantine_queue_is_bounded(self, tmp_path):
        """A flood must not be able to grow the review queue without bound."""
        policy = AdmissionPolicy(
            tmp_path, AdmissionMode.PUBLIC_OPEN, max_pending=3
        )
        for _ in range(10):
            _, key = make_peer()
            policy.submit(key)
        assert len(policy.pending()) <= 3


class TestBlockAndAllowlist:
    def test_blocked_peer_is_refused(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        ident, key = make_peer()
        nonce = solve_work(key, policy.current_difficulty())
        policy.submit(key, nonce=nonce)
        assert policy.block(ident.peer_id) is True
        nonce = solve_work(key, policy.current_difficulty())
        decision = policy.submit(key, nonce=nonce)
        assert decision.allowed is False
        assert decision.state is PeerState.BLOCKED

    def test_block_survives_restart(self, tmp_path):
        """Blocking must persist, or it is not a control."""
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        ident, key = make_peer()
        nonce = solve_work(key, policy.current_difficulty())
        policy.submit(key, nonce=nonce)
        policy.block(ident.peer_id)

        reloaded = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        assert reloaded.submit(key).allowed is False

    def test_allowlisted_peer_skips_work_and_is_trusted(self, tmp_path):
        """A peer vouched for out of band should not have to grind."""
        ident = PeerIdentity.generate()
        policy = AdmissionPolicy(
            tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=24, allowlist=[ident.peer_id]
        )
        decision = policy.submit(ident.public_key_bytes, nonce=0)
        assert decision.allowed is True
        assert decision.state is PeerState.TRUSTED
        assert decision.difficulty == 0

    def test_revoke_forgets_the_peer(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        ident, key = make_peer()
        nonce = solve_work(key, policy.current_difficulty())
        policy.submit(key, nonce=nonce)
        assert policy.revoke(ident.peer_id) is True
        assert policy.pending() == []

    def test_promote_unknown_peer_returns_false(self, tmp_path):
        policy = AdmissionPolicy(tmp_path)
        assert policy.promote("pl1doesnotexist") is False


class TestPolicyStorage:
    def test_policy_file_is_owner_only(self, tmp_path):
        if os.name == "nt":
            pytest.skip("POSIX permission bits")
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_OPEN)
        _, key = make_peer()
        policy.submit(key)
        path = policy.storage_dir / "peer-policy.json"
        assert path.exists()
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    def test_corrupt_policy_file_fails_safe_to_closed(self, tmp_path):
        """A corrupt file must not open the door, and must not raise."""
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        _, key = make_peer()
        policy.submit(key)
        (policy.storage_dir / "peer-policy.json").write_text("{not json", encoding="utf-8")

        reloaded = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_GATED, pow_bits=12)
        # Known-peer state is lost (fail safe: treat as stranger), but the
        # call must not raise into a request path.
        decision = reloaded.submit(key, nonce=solve_work(key, 12))
        assert decision.state is PeerState.QUARANTINED

    def test_peer_id_is_rederived_not_trusted_from_caller(self, tmp_path):
        """A peer must not be able to claim an id it does not own."""
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_OPEN)
        victim = PeerIdentity.generate()
        attacker_key = PeerIdentity.generate().public_key_bytes
        policy.submit(attacker_key)
        # The attacker's key produced the attacker's id, never the victim's.
        assert victim.peer_id not in [p["peer_id"] for p in policy.list_peers()]

    def test_malformed_key_is_rejected(self, tmp_path):
        policy = AdmissionPolicy(tmp_path, AdmissionMode.PUBLIC_OPEN)
        assert policy.submit(b"too-short").allowed is False
