"""Peer Link — connect two Synapse instances belonging to different users.

Additive by design: this package does not modify ``gateway/pairing.py`` or
``synapse_cli/subcommands/peer.py``. It builds beside them so existing
Telegram/WhatsApp pairing and the existing bot-to-bot DM transport keep working
exactly as before.

Layers:

* :mod:`gateway.peer_link.identity` — Ed25519 identity and peer ids.
* :mod:`gateway.peer_link.policy` — admission control for public peers.
* :mod:`gateway.peer_link.invite` — read-only invite-code verification.
* :mod:`gateway.peer_link.endpoint` — per-instance, unguessable hostnames.
"""

from gateway.peer_link.endpoint import (
    DEFAULT_BASE_DOMAIN,
    EndpointRegistry,
    certificate_note,
    generate_label,
    hostname_for,
    validate_domain,
    validate_label,
)
from gateway.peer_link.identity import (
    PEER_ID_PREFIX,
    PeerIdentity,
    peer_id_from_public_key,
    public_key_from_b64,
)
from gateway.peer_link.policy import (
    DEFAULT_POW_BITS,
    AdmissionDecision,
    AdmissionMode,
    AdmissionPolicy,
    PeerState,
    solve_work,
    verify_work,
)

__all__ = [
    "PEER_ID_PREFIX",
    "PeerIdentity",
    "peer_id_from_public_key",
    "public_key_from_b64",
    "AdmissionDecision",
    "AdmissionMode",
    "AdmissionPolicy",
    "PeerState",
    "DEFAULT_POW_BITS",
    "solve_work",
    "verify_work",
    "DEFAULT_BASE_DOMAIN",
    "EndpointRegistry",
    "certificate_note",
    "generate_label",
    "hostname_for",
    "validate_label",
    "validate_domain",
]
