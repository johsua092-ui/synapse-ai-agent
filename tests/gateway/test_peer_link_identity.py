"""Tests for Peer Link cryptographic identity.

Every test writes only under ``tmp_path`` — never ``~/.synapse``.
"""

from __future__ import annotations

import os
import stat

import pytest

from gateway.peer_link.identity import (
    PEER_ID_PREFIX,
    PeerIdentity,
    peer_id_from_public_key,
    public_key_from_b64,
)


class TestPeerIdDerivation:
    def test_peer_id_is_deterministic(self):
        """The same key must always yield the same id, on every machine."""
        ident = PeerIdentity.generate()
        assert ident.peer_id == peer_id_from_public_key(ident.public_key_bytes)
        assert ident.peer_id == ident.peer_id

    def test_distinct_keys_yield_distinct_ids(self):
        ids = {PeerIdentity.generate().peer_id for _ in range(50)}
        assert len(ids) == 50

    def test_peer_id_has_expected_shape(self):
        pid = PeerIdentity.generate().peer_id
        assert pid.startswith(PEER_ID_PREFIX)
        # 20 bytes of SHA-256 -> 32 base32 chars, plus the prefix.
        assert len(pid) == len(PEER_ID_PREFIX) + 32
        assert pid == pid.lower()

    def test_public_key_from_b64_round_trips(self):
        ident = PeerIdentity.generate()
        raw = public_key_from_b64(ident.public_key_b64)
        assert raw == ident.public_key_bytes

    @pytest.mark.parametrize(
        "bad",
        ["", "not-base64!!!", "AAAA", "Zm9vYmFy"],
    )
    def test_public_key_from_b64_rejects_malformed(self, bad):
        with pytest.raises(ValueError):
            public_key_from_b64(bad)

    def test_peer_id_rejects_wrong_length_key(self):
        with pytest.raises(ValueError):
            peer_id_from_public_key(b"short")

    def test_peer_id_rejects_non_bytes(self):
        with pytest.raises(ValueError):
            peer_id_from_public_key("a" * 32)  # type: ignore[arg-type]


class TestSignAndVerify:
    def test_signature_verifies(self):
        ident = PeerIdentity.generate()
        data = b"peer-link handshake payload"
        sig = ident.sign(data)
        assert PeerIdentity.verify(ident.public_key_bytes, sig, data) is True

    def test_tampered_payload_fails(self):
        ident = PeerIdentity.generate()
        sig = ident.sign(b"original")
        assert PeerIdentity.verify(ident.public_key_bytes, sig, b"tampered") is False

    def test_other_peer_cannot_impersonate(self):
        """A signature from one identity must not verify under another's key."""
        alice, mallory = PeerIdentity.generate(), PeerIdentity.generate()
        sig = mallory.sign(b"i am alice")
        assert PeerIdentity.verify(alice.public_key_bytes, sig, b"i am alice") is False

    @pytest.mark.parametrize("bad_sig", [b"", b"\x00" * 64, b"short"])
    def test_malformed_signature_returns_false_not_raises(self, bad_sig):
        """Verification must fail closed, never raise into a request path."""
        ident = PeerIdentity.generate()
        assert PeerIdentity.verify(ident.public_key_bytes, bad_sig, b"data") is False


class TestKeyStorage:
    def test_save_and_load_round_trip(self, tmp_path):
        path = tmp_path / "identity.key"
        original = PeerIdentity.generate()
        original.save(path)
        loaded = PeerIdentity.load(path)
        assert loaded.public_key_bytes == original.public_key_bytes
        assert loaded.peer_id == original.peer_id

    def test_private_key_file_is_owner_only(self, tmp_path):
        """The private key must not be world- or group-readable."""
        if os.name == "nt":
            pytest.skip("POSIX permission bits")
        path = tmp_path / "identity.key"
        PeerIdentity.generate().save(path)
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o600, f"expected 0600, got {oct(mode)}"

    def test_save_refuses_to_clobber_existing_identity(self, tmp_path):
        """Overwriting silently would orphan every peer that knows the old key."""
        path = tmp_path / "identity.key"
        first = PeerIdentity.generate()
        first.save(path)
        with pytest.raises(FileExistsError):
            PeerIdentity.generate().save(path)
        # The original must still be intact.
        assert PeerIdentity.load(path).peer_id == first.peer_id

    def test_save_overwrite_is_explicit(self, tmp_path):
        path = tmp_path / "identity.key"
        PeerIdentity.generate().save(path)
        replacement = PeerIdentity.generate()
        replacement.save(path, overwrite=True)
        assert PeerIdentity.load(path).peer_id == replacement.peer_id

    def test_load_or_create_creates_once_then_reuses(self, tmp_path):
        path = tmp_path / "identity.key"
        first, created_first = PeerIdentity.load_or_create(path)
        assert created_first is True
        second, created_second = PeerIdentity.load_or_create(path)
        assert created_second is False
        assert first.peer_id == second.peer_id

    def test_load_rejects_wrong_length_file(self, tmp_path):
        path = tmp_path / "identity.key"
        path.write_bytes(b"too-short")
        with pytest.raises(ValueError):
            PeerIdentity.load(path)

    def test_pem_round_trip(self, tmp_path):
        """A PEM key written by other tooling must load correctly."""
        from cryptography.hazmat.primitives import serialization

        path = tmp_path / "identity.pem"
        ident = PeerIdentity.generate()
        path.write_bytes(
            ident._private_key.private_bytes(  # noqa: SLF001 - test seam
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        assert PeerIdentity.load(path).peer_id == ident.peer_id


class TestNoKeyLeakage:
    def test_repr_does_not_contain_key_material(self):
        """A stray repr() in a log line must never leak a private key."""
        ident = PeerIdentity.generate()
        text = repr(ident)
        assert ident.public_key_b64 not in text
        assert ident.private_key_bytes.hex() not in text
        assert "private" not in text.lower()

    def test_public_bundle_excludes_private_key(self):
        ident = PeerIdentity.generate()
        bundle = ident.public_bundle()
        assert set(bundle) == {"peer_id", "public_key", "scheme"}
        assert ident.private_key_bytes.hex() not in str(bundle)
