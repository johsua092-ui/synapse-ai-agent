"""Peer Link — per-instance endpoint names.

Answers the question: *"can every peer get its own address, and can that
address be unguessable?"*

Yes, and the two halves are solved differently:

  * **Unique per instance** — the label is random, minted once and persisted.
    Two peers never collide, and a peer's address is stable across restarts.
  * **Unguessable** — the label carries no information derived from the public
    peer id. Knowing a peer's *public key* (which is shared freely) must not
    let anyone compute its *address*. A random label achieves that; a label
    derived from the peer id would not, because peer ids are public.

The address is deliberately **not** a secret in the cryptographic sense — DNS
and Certificate Transparency are public systems. What makes it safe is:

  1. the label is random, so it cannot be enumerated; and
  2. knowledge of the address is still not authorisation. The admission policy
     in :mod:`gateway.peer_link.policy` decides who gets in, and an unknown
     address merely fails to resolve.

Do not rely on the label alone as a security boundary — that is exactly the
"security by obscurity" trap. It is a discovery-cost multiplier, not a lock.

**Certificate caveat (matters, and bites people):** a wildcard TLS certificate
``*.example.com`` covers *one* label level only — ``a.example.com`` yes,
``a.b.example.com`` no. Cloudflare's free Universal SSL follows the same rule
unless the apex itself is the registered zone. :func:`certificate_note`
returns the concrete implication for a chosen base domain so the operator finds
out before peers start failing to connect, not after.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from utils import atomic_replace

#: Alphabet for *generated* labels: lowercase alphanumerics with the confusable
#: glyphs removed (no 0/o/1/l), so a human copying an address by hand does not
#: misread it. Generation only — validation must accept real domains, which do
#: contain those letters (``zone``, ``id``).
LABEL_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"  # no 0/o/1/l

#: Characters permitted in a *validated* DNS label. The full set, because a
#: peer's real domain is not ours to choose.
DNS_LABEL_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789-"

#: Label length. 32 chars of a 32-symbol alphabet ≈ 160 bits — far beyond
#: enumeration, and well inside the 63-character DNS label limit.
LABEL_LENGTH = 26

#: Default base domain, matching the operator's own zone.
DEFAULT_BASE_DOMAIN = "synz.zone.id"


def generate_label(length: int = LABEL_LENGTH) -> str:
    """Mint a fresh random DNS label (cryptographically random)."""
    if length < 8:
        raise ValueError("label must be at least 8 characters")
    if length > 63:
        raise ValueError("label exceeds the 63-character DNS limit")
    return "".join(secrets.choice(LABEL_ALPHABET) for _ in range(length))


def validate_label(label: object) -> bool:
    """True iff *label* is a safe single DNS label.

    Rejects anything that could escape its position in the name — dots,
    slashes, wildcards, whitespace, hyphens at the edges — so a stored or
    user-supplied label can never rewrite the hostname it is embedded in.
    """
    if not isinstance(label, str) or not 1 <= len(label) <= 63:
        return False
    if label[0] == "-" or label[-1] == "-":
        return False
    return all(c in DNS_LABEL_CHARS for c in label)


def validate_domain(domain: object) -> bool:
    """True iff *domain* is a safe, plain DNS name (no wildcards/paths).

    Validated separately from the label because the two are concatenated:
    checking only the label would let ``"a.b/c"`` through, where the label is
    fine but the remainder escapes into a path or another authority.
    """
    if not isinstance(domain, str) or not 1 <= len(domain) <= 253:
        return False
    if domain != domain.strip().lower():
        return False
    if any(c not in DNS_LABEL_CHARS + "." for c in domain):
        return False
    if ".." in domain or domain.startswith(".") or domain.endswith("."):
        return False
    labels = domain.split(".")
    return all(validate_label(part) for part in labels)


def hostname_for(label: str, base_domain: str = DEFAULT_BASE_DOMAIN) -> str:
    """Compose ``<label>.<base_domain>``, refusing anything malformed.

    Validating here (rather than trusting the caller) keeps a corrupted
    registry entry from producing a hostname that resolves somewhere else.
    """
    if not validate_label(label):
        raise ValueError(f"unsafe DNS label: {label!r}")
    domain = (base_domain or "").strip().strip(".").lower()
    if not validate_domain(domain):
        raise ValueError(f"unsafe base domain: {base_domain!r}")
    return f"{label}.{domain}"


def certificate_note(base_domain: str = DEFAULT_BASE_DOMAIN) -> str:
    """Explain the TLS-certificate implication of *base_domain*.

    The distinction that decides whether this works for free:

      * If *base_domain* is itself the **registered zone** (its nameservers
        point at Cloudflare), then ``<label>.<base_domain>`` is a *first-level*
        subdomain and the free wildcard ``*.<base_domain>`` covers it.
      * If *base_domain* is only a *hostname inside someone else's zone*
        (e.g. ``synz.zone.id`` while the registered zone is ``zone.id``), then
        ``<label>.synz.zone.id`` is a *second-level* subdomain, which the free
        wildcard does **not** cover — those connections fail certificate
        validation and need Advanced Certificate Manager (paid) or a custom
        certificate.
    """
    domain = (base_domain or "").strip().strip(".").lower()
    labels = [p for p in domain.split(".") if p]
    if len(labels) <= 2:
        return (
            f"'{domain}' looks like a registered zone. "
            f"Free wildcard '*.{domain}' should cover '<label>.{domain}'."
        )
    return (
        f"'{domain}' has {len(labels)} labels, so '<label>.{domain}' is a "
        f"DEEP subdomain. A free wildcard '*.<zone>' covers only ONE label "
        f"level and will NOT cover this. Register '{domain}' as its own zone "
        f"in Cloudflare (recommended, free), or expect a certificate error "
        f"needing a paid advanced certificate. Verify with: "
        f"curl -svI https://<label>.{domain} 2>&1 | grep -i 'subject\\|SSL'"
    )


class EndpointRegistry:
    """Local map of peer id -> this instance's (or a peer's) endpoint.

    Persisted under the Peer Link state directory, written atomically with
    owner-only permissions. Nothing here is transmitted; the address is shared
    out-of-band, exactly like the invite code.
    """

    def __init__(
        self,
        state_dir: "str | os.PathLike[str]",
        base_domain: str = DEFAULT_BASE_DOMAIN,
    ) -> None:
        self._dir = Path(state_dir)
        self._base_domain = base_domain
        self._path = self._dir / "endpoints.json"

    # ----- storage ------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {"self": None, "peers": {}}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"self": None, "peers": {}}
        if not isinstance(data, dict):
            return {"self": None, "peers": {}}
        data.setdefault("self", None)
        data.setdefault("peers", {})
        if not isinstance(data.get("peers"), dict):
            data["peers"] = {}
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        os.chmod(tmp, 0o600)
        atomic_replace(tmp, self._path)

    # ----- our own endpoint ---------------------------------------------

    @property
    def base_domain(self) -> str:
        return self._base_domain

    def own_hostname(self, *, create: bool = True) -> Optional[str]:
        """Return this instance's hostname, minting a label on first call.

        ``create=False`` reads without minting, so read-only commands
        (``peerlink status``) never mutate state as a side effect.
        """
        data = self._load()
        current = data.get("self")
        if isinstance(current, dict):
            label = current.get("label")
            if isinstance(label, str) and validate_label(label):
                return hostname_for(label, self._base_domain)
        if not create:
            return None
        label = generate_label()
        data["self"] = {"label": label, "base_domain": self._base_domain}
        self._save(data)
        return hostname_for(label, self._base_domain)

    def rotate(self) -> str:
        """Mint a new label, invalidating the old address."""
        data = self._load()
        label = generate_label()
        data["self"] = {"label": label, "base_domain": self._base_domain}
        self._save(data)
        return hostname_for(label, self._base_domain)

    # ----- peers' endpoints ---------------------------------------------

    def remember(self, peer_id: str, hostname: str) -> None:
        """Record a peer's advertised hostname (validated before storing).

        Both halves are checked: a valid label with a path or wildcard in the
        remainder (``"a.b/c"``) must be refused, or a stored value could point
        the client at an unintended authority.
        """
        if not peer_id:
            raise ValueError("peer_id is required")
        host = (hostname or "").strip().lower()
        label, _, domain = host.partition(".")
        if not validate_label(label) or not validate_domain(domain):
            raise ValueError(f"unsafe hostname: {hostname!r}")
        data = self._load()
        data["peers"][peer_id] = host
        self._save(data)

    def lookup(self, peer_id: str) -> Optional[str]:
        value = self._load()["peers"].get(peer_id)
        return value if isinstance(value, str) and value else None

    def forget(self, peer_id: str) -> bool:
        data = self._load()
        if peer_id in data["peers"]:
            del data["peers"][peer_id]
            self._save(data)
            return True
        return False

    def peers(self) -> Dict[str, str]:
        return dict(self._load()["peers"])
