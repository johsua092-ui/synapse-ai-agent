"""Tests for Peer Link invite-code verification (read-only path).

The property under test: verifying a code must never mutate shared pairing
state and must never trip the per-platform lockout in ``gateway.pairing``.
That lockout is the denial-of-service shape this module exists to avoid.

Every test writes only under ``tmp_path`` via a redirected ``SYNAPSE_HOME``.
"""

from __future__ import annotations

import json
import time

import pytest

from gateway.pairing import CODE_TTL_SECONDS, PairingStore
from gateway.peer_link import invite as invite_mod


@pytest.fixture()
def pairing_home(tmp_path, monkeypatch):
    """Point PairingStore at a temp SYNAPSE_HOME so ~/.synapse is untouched."""
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    return tmp_path


class TestVerifyInviteCode:
    def test_valid_code_verifies(self, pairing_home):
        store = PairingStore()
        code = store.generate_code("peerlink", "budi", "Budi")
        assert code
        assert invite_mod.verify_invite_code(code) is True

    def test_code_is_case_and_space_insensitive(self, pairing_home):
        store = PairingStore()
        code = store.generate_code("peerlink", "budi", "Budi")
        assert code
        assert invite_mod.verify_invite_code(f"  {code.lower()}  ") is True

    def test_wrong_code_fails(self, pairing_home):
        store = PairingStore()
        store.generate_code("peerlink", "budi", "Budi")
        assert invite_mod.verify_invite_code("ZZZZZZZZ") is False

    def test_empty_code_fails(self, pairing_home):
        assert invite_mod.verify_invite_code("") is False

    def test_expired_code_fails(self, pairing_home):
        store = PairingStore()
        code = store.generate_code("peerlink", "budi", "Budi")
        assert code
        future = time.time() + CODE_TTL_SECONDS + 10
        assert invite_mod.verify_invite_code(code, now=future) is False

    def test_no_pending_file_fails_cleanly(self, pairing_home):
        """A missing file must return False, not raise."""
        assert invite_mod.verify_invite_code("ABCDEFGH") is False

    def test_corrupt_pending_file_fails_cleanly(self, pairing_home):
        store = PairingStore()
        store.generate_code("peerlink", "budi", "Budi")
        path = store._pending_path("peerlink")  # noqa: SLF001
        path.write_text("{not json", encoding="utf-8")
        assert invite_mod.verify_invite_code("ABCDEFGH") is False

    def test_legacy_plaintext_entry_is_skipped(self, pairing_home):
        """Pre-upgrade entries (no salt/hash) must be ignored, not crash."""
        store = PairingStore()
        path = store._pending_path("peerlink")  # noqa: SLF001
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"old": {"user_id": "x", "created_at": time.time()}}),
            encoding="utf-8",
        )
        assert invite_mod.verify_invite_code("ABCDEFGH") is False


class TestVerifyIsReadOnly:
    """The security property: verification must not change shared state."""

    def test_verification_does_not_consume_the_code(self, pairing_home):
        store = PairingStore()
        code = store.generate_code("peerlink", "budi", "Budi")
        assert code
        assert invite_mod.verify_invite_code(code) is True
        # Still valid on a second call: nothing was consumed.
        assert invite_mod.verify_invite_code(code) is True

    def test_verification_does_not_approve_the_user(self, pairing_home):
        """A valid code must not add anyone to the platform allowlist."""
        store = PairingStore()
        code = store.generate_code("peerlink", "budi", "Budi")
        assert code
        invite_mod.verify_invite_code(code)
        approved = store._load_json(store._approved_path("peerlink"))  # noqa: SLF001
        assert "budi" not in approved

    def test_verification_does_not_trip_platform_lockout(self, pairing_home):
        """THE regression: many bad codes must not lock the platform out.

        This is exactly the failure mode of ``PairingStore.approve_code``,
        which counts failures per platform. Peer Link verifies read-only, so
        the shared counter must stay untouched.
        """
        store = PairingStore()
        store.generate_code("peerlink", "budi", "Budi")
        for _ in range(20):
            invite_mod.verify_invite_code("ZZZZZZZZ")
        # The shared lockout must not have fired...
        assert store._is_locked_out("peerlink") is False  # noqa: SLF001
        # ...and the legitimate code still works, and the owner can still mint.
        assert store.generate_code("peerlink", "wati", "Wati")

    def test_verification_does_not_bump_failure_counter(self, pairing_home):
        store = PairingStore()
        store.generate_code("peerlink", "budi", "Budi")
        before = store._load_json(store._rate_limit_path()).get(  # noqa: SLF001
            "_failed_attempts", {}
        )
        for _ in range(5):
            invite_mod.verify_invite_code("ZZZZZZZZ")
        after = store._load_json(store._rate_limit_path()).get(  # noqa: SLF001
            "_failed_attempts", {}
        )
        assert before == after

    def test_contrast_approve_code_does_lock_out(self, pairing_home):
        """Document the hazard this module avoids — proving the fix is real.

        If this ever stops holding, ``approve_code`` has been made safe and
        the read-only path could be reconsidered.
        """
        store = PairingStore()
        store.generate_code("peerlink", "budi", "Budi")
        for _ in range(5):
            store.approve_code("peerlink", "ZZZZZZZZ")
        assert store._is_locked_out("peerlink") is True  # noqa: SLF001


class TestListInvites:
    def test_lists_live_invite_without_revealing_code(self, pairing_home):
        store = PairingStore()
        code = store.generate_code("peerlink", "budi", "Budi")
        assert code
        rows = invite_mod.list_invites()
        assert len(rows) == 1
        assert rows[0]["user_id"] == "budi"
        assert rows[0]["expires_in"] > 0
        # The code itself is never recoverable from storage.
        assert code not in json.dumps(rows)

    def test_excludes_expired(self, pairing_home):
        store = PairingStore()
        store.generate_code("peerlink", "budi", "Budi")
        future = time.time() + CODE_TTL_SECONDS + 10
        assert invite_mod.list_invites(now=future) == []

    def test_empty_when_no_invites(self, pairing_home):
        assert invite_mod.list_invites() == []
