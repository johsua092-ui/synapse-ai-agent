"""Peer Link — cryptographic identity.

A Peer Link identity *is* an Ed25519 public key. There is no registry, no
account, and no central authority: two Synapse instances that hold each other's
public key can authenticate each other offline, forever, with no third party in
the loop.

Why a key pair rather than a shared secret:

  * A shared secret has to be transmitted, and whoever transmits it can leak
    it. A key pair never leaves its instance — peers exchange public keys only.
  * Signatures make impersonation and replay *detectable*, not merely unlikely.
  * Revocation is local and instant: forget a public key and that peer is gone.

The private key is written 0600, is never logged, never transmitted, and is
never handed to a peer. :meth:`PeerIdentity.__repr__` is deliberately key-free
so that a stray ``repr()`` in a log line cannot leak key material.
"""

from __future__ import annotations

import base64
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from utils import atomic_replace

#: Human-facing prefix for peer identifiers. Versioned so a future scheme can
#: coexist without ambiguity ("pl1" = Peer Link, scheme 1).
PEER_ID_PREFIX = "pl1"

#: Bytes of SHA-256 folded into a peer id. 20 bytes -> 32 base32 characters.
PEER_ID_DIGEST_BYTES = 20

#: Ed25519 public keys are exactly this long.
PUBLIC_KEY_BYTES = 32


def peer_id_from_public_key(public_key_bytes: bytes) -> str:
    """Derive the stable peer id for an Ed25519 public key.

    The id is a *fingerprint*, not an address: it is derived from the key, so
    two instances computing it from the same key always agree and no registry
    has to assign it. Because it is derived, a caller can never claim someone
    else's id — see :meth:`AdmissionPolicy.submit`, which re-derives the id
    from the supplied key rather than trusting a caller-supplied one.
    """
    if not isinstance(public_key_bytes, (bytes, bytearray)):
        raise ValueError("public key must be bytes")
    if len(public_key_bytes) != PUBLIC_KEY_BYTES:
        raise ValueError(
            f"Ed25519 public key must be exactly {PUBLIC_KEY_BYTES} bytes, "
            f"got {len(public_key_bytes)}"
        )
    digest = hashlib.sha256(bytes(public_key_bytes)).digest()[:PEER_ID_DIGEST_BYTES]
    encoded = base64.b32encode(digest).decode("ascii").rstrip("=").lower()
    return PEER_ID_PREFIX + encoded


def public_key_from_b64(public_key_b64: str) -> bytes:
    """Decode a base64 public key, validating the length.

    Raises ``ValueError`` on anything malformed so callers cannot accidentally
    treat garbage as a key.
    """
    try:
        raw = base64.b64decode(public_key_b64, validate=True)
    except Exception as exc:  # binascii.Error, ValueError
        raise ValueError(f"public key is not valid base64: {exc}") from exc
    if len(raw) != PUBLIC_KEY_BYTES:
        raise ValueError(
            f"Ed25519 public key must be exactly {PUBLIC_KEY_BYTES} bytes, "
            f"got {len(raw)}"
        )
    return raw


class PeerIdentity:
    """An instance's own key pair. One per install, created on first use."""

    def __init__(self, private_key: Ed25519PrivateKey) -> None:
        self._private_key = private_key
        self._public_key = private_key.public_key()

    # ----- construction -------------------------------------------------

    @classmethod
    def generate(cls) -> "PeerIdentity":
        """Mint a fresh identity from the OS CSPRNG."""
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def load(cls, path: "os.PathLike[str] | str") -> "PeerIdentity":
        """Load a private key from *path* (raw 32 bytes, or PEM)."""
        raw = Path(path).read_bytes()
        if b"-----BEGIN" in raw:
            key = serialization.load_pem_private_key(raw, password=None)
            if not isinstance(key, Ed25519PrivateKey):
                raise ValueError("file does not contain an Ed25519 private key")
            return cls(key)
        if len(raw) != 32:
            raise ValueError(
                f"raw Ed25519 private key must be 32 bytes, got {len(raw)}"
            )
        return cls(Ed25519PrivateKey.from_private_bytes(raw))

    @classmethod
    def load_or_create(
        cls, path: "os.PathLike[str] | str"
    ) -> Tuple["PeerIdentity", bool]:
        """Load the identity at *path*, creating it if absent.

        Returns ``(identity, created)``. Creation is atomic and 0600, so a
        crash mid-write can never leave a half-written key behind.
        """
        p = Path(path)
        if p.exists():
            return cls.load(p), False
        ident = cls.generate()
        ident.save(p)
        return ident, True

    def save(self, path: "os.PathLike[str] | str", *, overwrite: bool = False) -> Path:
        """Persist the private key atomically with 0600 permissions.

        Refuses to clobber an existing file unless ``overwrite=True``: silently
        replacing an identity would orphan every peer that knows the old key.
        """
        p = Path(path)
        if p.exists() and not overwrite:
            raise FileExistsError(
                f"refusing to overwrite existing identity at {p} "
                f"(pass overwrite=True to replace it deliberately)"
            )
        p.parent.mkdir(parents=True, exist_ok=True)
        raw = self.private_key_bytes
        fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            atomic_replace(tmp, p)
            try:
                os.chmod(p, 0o600)
            except OSError:
                pass  # Windows does not map POSIX modes the same way
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return p

    # ----- accessors ----------------------------------------------------

    @property
    def private_key_bytes(self) -> bytes:
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

    @property
    def public_key_bytes(self) -> bytes:
        return self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

    @property
    def public_key_b64(self) -> str:
        return base64.b64encode(self.public_key_bytes).decode("ascii")

    @property
    def peer_id(self) -> str:
        return peer_id_from_public_key(self.public_key_bytes)

    # ----- crypto -------------------------------------------------------

    def sign(self, data: bytes) -> bytes:
        """Sign *data* with this instance's private key."""
        return self._private_key.sign(bytes(data))

    @staticmethod
    def verify(public_key_bytes: bytes, signature: bytes, data: bytes) -> bool:
        """Return True only for a genuinely valid signature. Never raises.

        Returning a bool (rather than propagating ``InvalidSignature``) keeps
        callers from accidentally treating an exception path as "trusted".
        """
        try:
            Ed25519PublicKey.from_public_bytes(bytes(public_key_bytes)).verify(
                bytes(signature), bytes(data)
            )
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False

    def public_bundle(self) -> Dict[str, Any]:
        """The shareable half — safe to send to a peer, post, or paste."""
        return {
            "peer_id": self.peer_id,
            "public_key": self.public_key_b64,
            "scheme": "ed25519",
        }

    def __repr__(self) -> str:
        # Key-free on purpose: a stray repr() must never leak key material.
        return f"PeerIdentity(peer_id={self.peer_id!r})"
