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

**Two addressing modes, because the DNS you own decides which one works:**

  * ``subdomain`` — ``<label>.<base_domain>``. Every peer gets its own name,
    but the free wildcard certificate that covers them reaches exactly ONE
    label below the **zone apex**. ``aikernel.qzz.io`` is a genuine apex, so
    it works; ``synz.zone.id`` is a *hostname inside* the ``zone.id`` zone, so
    ``<label>.synz.zone.id`` is one level too deep and fails TLS validation.
  * ``path`` — ``<base_domain>{PATH_PREFIX}<label>``. All peers share ONE
    hostname and are told apart by the path, so a single ordinary certificate
    is enough. This is the mode that works when you do not own the apex of
    ``base_domain`` (``synz.zone.id``) or when the free plan forbids extra
    subdomains.

Counting labels cannot tell an apex from a hostname inside somebody else's
zone — delegation can, and :func:`certificate_note` says exactly how to check
rather than guessing.
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

#: Default base domain: the operator's own **zone apex**.
#:
#: Peers are published as ``<label>.<base_domain>`` — one label below this name.
#: It must therefore be the apex itself (the name whose NS records are yours),
#: not a hostname inside somebody else's zone. ``synz.zone.id`` is a shared-host
#: CNAME inside ``zone.id``, so it cannot work; ``aikernel.qzz.io`` is a real
#: apex and does. Override per deployment with ``peer_link.base_domain`` in
#: ``config.yaml``.
DEFAULT_BASE_DOMAIN = "aikernel.qzz.io"

#: Path segment that separates the shared hostname from a peer's label in
#: ``path`` mode: ``https://example.com/peer/<label>``. All peers share one
#: hostname, so one ordinary certificate covers every peer — the reason this
#: mode exists. See :func:`public_address`.
PATH_PREFIX = "/peer/"

#: Addressing modes. ``subdomain`` publishes ``<label>.<base_domain>`` and
#: needs the base domain to be a zone apex you control (free wildcard cert);
#: ``path`` publishes ``<base_domain>/peer/<label>`` and needs only one name.
ADDRESS_MODES = ("subdomain", "path")

#: Default mode. ``subdomain`` is the richer shape (a distinct name per peer),
#: so it stays the default; switch to ``path`` in ``config.yaml`` when the base
#: domain is not an apex you own.
DEFAULT_ADDRESS_MODE = "subdomain"


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


def validate_address_mode(mode: object) -> bool:
    """True iff *mode* is a known addressing mode."""
    return isinstance(mode, str) and mode in ADDRESS_MODES


def public_address(
    label: str,
    base_domain: str = DEFAULT_BASE_DOMAIN,
    mode: str = DEFAULT_ADDRESS_MODE,
) -> str:
    """Compose the public address for *label*, honouring the addressing mode.

    ``subdomain`` -> ``<label>.<base_domain>`` — each peer gets its own name.
    ``path``      -> ``<base_domain>{PATH_PREFIX}<label>`` — every peer shares
    the ONE hostname *base_domain* and is told apart by the path, which is what
    makes a single ordinary certificate sufficient.

    The label is validated in both modes, so a corrupted value cannot smuggle a
    ``/``, a ``..`` or a wildcard into the address and redirect a client to
    another authority.
    """
    if not validate_address_mode(mode):
        raise ValueError(f"unknown address mode: {mode!r}")
    if mode == "subdomain":
        return hostname_for(label, base_domain)
    domain = _normalise_domain(base_domain)
    if not validate_label(label):
        raise ValueError(f"unsafe label: {label!r}")
    if not validate_domain(domain):
        raise ValueError(f"unsafe base domain: {base_domain!r}")
    return f"{domain}{PATH_PREFIX}{label}"


def _normalise_domain(value: object) -> str:
    """Lower-case, dot-trimmed DNS name (no other interpretation)."""
    return (str(value) if value is not None else "").strip().strip(".").lower()


def certificate_note(
    base_domain: str = DEFAULT_BASE_DOMAIN,
    zone_apex: Optional[str] = None,
    mode: str = DEFAULT_ADDRESS_MODE,
) -> str:
    """Explain the TLS-certificate implication of *base_domain* for *mode*.

    In ``path`` mode every peer shares the ONE hostname *base_domain*, so a
    single ordinary certificate for that name is enough — the apex question is
    irrelevant, and this says so plainly.

    In ``subdomain`` mode the rule that decides whether it works for free is
    **how many labels *base_domain* sits below the zone apex you registered** —
    not how many labels the name happens to have:

      * ``base_domain == zone_apex`` — ``<label>.<base_domain>`` is one label
        below the apex, so the free wildcard ``*.<zone_apex>`` covers it.
      * ``base_domain`` is itself a subdomain of the apex (``synz.zone.id``
        inside zone ``zone.id``) — ``<label>.<base_domain>`` is two levels
        below, which a one-level wildcard does **not** reach. Use ``path`` mode
        instead, or register ``base_domain`` as its own zone.

    A three-label base domain is therefore not automatically broken:
    ``aikernel.qzz.io`` is a genuine three-label apex and works, while
    ``synz.zone.id`` is a hostname inside ``zone.id`` and does not. Counting
    labels cannot tell them apart, so when *zone_apex* is not supplied this
    returns the exact command to check instead of guessing.
    """
    domain = _normalise_domain(base_domain)
    if not validate_domain(domain):
        return f"'{base_domain}' is not a valid DNS name."

    if mode == "path":
        return (
            f"Path mode: every peer shares the single hostname '{domain}', so "
            f"one ordinary certificate for '{domain}' covers all of them — no "
            f"wildcard and no apex delegation needed. Issue it for exactly "
            f"'{domain}' (e.g. Let's Encrypt HTTP-01) and reverse-proxy "
            f"'{PATH_PREFIX}<label>' to this instance."
        )
    if not validate_address_mode(mode):
        return f"'{mode}' is not a known addressing mode."

    apex = _normalise_domain(zone_apex)
    if not apex:
        return (
            f"Free wildcard '*.{domain}' covers '<label>.{domain}' only if "
            f"'{domain}' is itself a registered zone (its own NS records at your "
            f"DNS provider) — a wildcard reaches exactly ONE label below the "
            f"zone apex. Check which it is with:\n"
            f"    dig +short NS {domain}\n"
            f"  your provider's nameservers -> it is a zone, the wildcard covers "
            f"it;\n"
            f"  a foreign host or empty -> it is a hostname inside someone else's "
            f"zone and '<label>.{domain}' will fail TLS validation.\n"
            f"Set peer_link.zone_apex in config.yaml for an exact verdict."
        )

    if not validate_domain(apex):
        return f"'{zone_apex}' is not a valid DNS name."

    depth = len(domain.split(".")) - len(apex.split("."))
    if depth == 0:
        return (
            f"'{domain}' is the zone apex, so the free wildcard '*.{apex}' covers "
            f"'<label>.{domain}'. No paid certificate needed."
        )
    if depth > 0:
        return (
            f"'{domain}' sits {depth} label(s) below the zone apex '{apex}', so "
            f"'<label>.{domain}' is {depth + 1} level(s) below the apex. A free "
            f"wildcard '*.{apex}' reaches only ONE level and will NOT cover it. "
            f"Fix it either way: switch to path mode "
            f"(peer_link.address_mode: path) so every peer shares the single "
            f"name '{domain}', or publish peers directly under the apex "
            f"('<label>.{apex}'), or register '{domain}' as its own zone."
        )
    return (
        f"'{domain}' is {abs(depth)} label(s) above the zone apex '{apex}' — a "
        f"configuration error: the apex must be '{domain}' or a suffix of it."
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
        mode: str = DEFAULT_ADDRESS_MODE,
    ) -> None:
        if not validate_address_mode(mode):
            raise ValueError(f"unknown address mode: {mode!r}")
        self._dir = Path(state_dir)
        self._base_domain = base_domain
        self._mode = mode
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

    @property
    def mode(self) -> str:
        """Addressing mode: ``subdomain`` or ``path``."""
        return self._mode

    def _minted_label(self, *, create: bool) -> Optional[str]:
        """Return our stored label, minting one when *create* is true."""
        data = self._load()
        current = data.get("self")
        if isinstance(current, dict):
            label = current.get("label")
            if isinstance(label, str) and validate_label(label):
                return label
        if not create:
            return None
        label = generate_label()
        data["self"] = {
            "label": label,
            "base_domain": self._base_domain,
            "mode": self._mode,
        }
        self._save(data)
        return label

    def own_hostname(self, *, create: bool = True) -> Optional[str]:
        """Return the hostname clients dial, minting a label on first call.

        ``subdomain`` mode returns ``<label>.<base_domain>`` — a name unique to
        this instance. ``path`` mode returns *base_domain* itself, because every
        peer shares that one hostname and is separated by the path instead.

        ``create=False`` reads without minting, so read-only commands
        (``peerlink status``) never mutate state as a side effect.
        """
        label = self._minted_label(create=create)
        if label is None:
            return None
        if self._mode == "path":
            return _normalise_domain(self._base_domain)
        return hostname_for(label, self._base_domain)

    def own_address(self, *, create: bool = True) -> Optional[str]:
        """Like :meth:`own_hostname`, but honours the addressing mode.

        In ``path`` mode this is ``<base_domain>/peer/<label>`` rather than a
        bare hostname, so callers that publish an address to a peer should use
        this one. ``own_hostname`` remains the host-only view.
        """
        label = self._minted_label(create=create)
        if label is None:
            return None
        return public_address(label, self._base_domain, self._mode)

    def rotate(self) -> str:
        """Mint a new label, invalidating the old address."""
        data = self._load()
        label = generate_label()
        data["self"] = {
            "label": label,
            "base_domain": self._base_domain,
            "mode": self._mode,
        }
        self._save(data)
        return public_address(label, self._base_domain, self._mode)

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

    def remember_address(self, peer_id: str, address: str) -> None:
        """Record a peer's advertised address, which may include a path.

        Accepts both shapes:

          * ``xyz.example.com``            — subdomain mode
          * ``example.com/peer/<label>``   — path mode

        The host half is validated with :meth:`remember`'s rules; the path half
        must match ``PATH_PREFIX`` followed by a single safe label. Anything
        else is refused, so a stored peer address cannot point a client at an
        unintended authority or escape into a different path.
        """
        if not peer_id:
            raise ValueError("peer_id is required")
        value = (address or "").strip().lower()
        host, sep, path = value.partition("/")
        label, _, domain = host.partition(".")
        if not validate_label(label) or not validate_domain(domain):
            raise ValueError(f"unsafe hostname: {address!r}")
        if sep:
            if not path.startswith(PATH_PREFIX.lstrip("/")):
                raise ValueError(f"unsafe address path: {address!r}")
            tail = path[len(PATH_PREFIX.lstrip("/")):]
            if not validate_label(tail):
                raise ValueError(f"unsafe address label: {address!r}")
            value = f"{host}{PATH_PREFIX}{tail}"
        data = self._load()
        data["peers"][peer_id] = value
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
