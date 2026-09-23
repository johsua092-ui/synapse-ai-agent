"""``synapse peerlink`` — connect this Synapse instance to another user's.

Peer Link is **off by default**. Nothing listens until the owner turns it on,
and no peer is ever trusted automatically — every new peer lands in quarantine
and waits for an explicit ``peerlink approve``.

Typical flow:

    synapse peerlink identity                 # show our peer id (share this)
    synapse peerlink mode invite              # open the door, invite-only
    synapse peerlink invite --note "Budi"     # mint a code, send it out of band
    synapse peerlink pending                  # who is waiting
    synapse peerlink approve <peer-id>        # owner says yes — the only path

Exit codes: 0 ok, 1 error, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

#: Default file names inside the peer-link data directory.
IDENTITY_FILENAME = "identity.key"
POLICY_SUBDIR = "policy"


def _data_dir() -> Path:
    """Resolve ``<SYNAPSE_HOME>/peer_link``.

    Resolved lazily on every call rather than at import: the gateway imports
    this module once at boot, and an eagerly-computed path would freeze to
    whatever SYNAPSE_HOME existed at that instant.
    """
    from synapse_constants import get_synapse_dir

    return get_synapse_dir("peer_link", "peer_link")


def _peer_link_config() -> dict:
    """The ``peer_link`` section of ``config.yaml`` (empty dict if absent).

    A behavioural setting belongs in config.yaml, not an environment variable.
    """
    try:
        from synapse_cli.config import load_config

        cfg = load_config() or {}
        section = cfg.get("peer_link") or {}
        return section if isinstance(section, dict) else {}
    except Exception:
        return {}


def _default_base_domain() -> str:
    """Base domain for per-instance addresses, from ``config.yaml``."""
    from gateway.peer_link.endpoint import DEFAULT_BASE_DOMAIN

    value = str(_peer_link_config().get("base_domain") or "").strip()
    return value or DEFAULT_BASE_DOMAIN


def _default_zone_apex() -> str:
    """Registered zone apex, from ``peer_link.zone_apex`` in ``config.yaml``.

    Used only to turn :func:`certificate_note` from "go check this yourself"
    into an exact verdict. Optional: absent is safe, it just asks.
    """
    return str(_peer_link_config().get("zone_apex") or "").strip()


def _default_address_mode() -> str:
    """Addressing mode, from ``peer_link.address_mode`` in ``config.yaml``.

    ``subdomain`` (the default) publishes ``<label>.<base_domain>`` and needs a
    base domain that is a zone apex you control. ``path`` publishes
    ``<base_domain>/peer/<label>`` — one shared hostname, one ordinary
    certificate — for when the base domain is a subdomain of somebody else's
    zone (``synz.zone.id``). An unknown value falls back to the default rather
    than raising, so a typo cannot brick the command.
    """
    from gateway.peer_link.endpoint import DEFAULT_ADDRESS_MODE, validate_address_mode

    value = str(_peer_link_config().get("address_mode") or "").strip().lower()
    return value if validate_address_mode(value) else DEFAULT_ADDRESS_MODE


def _load_identity(create: bool = True):
    """Load (or lazily create) this instance's Ed25519 identity."""
    from gateway.peer_link.identity import PeerIdentity

    path = _data_dir() / IDENTITY_FILENAME
    if create:
        ident, _created = PeerIdentity.load_or_create(path)
        return ident
    if not path.exists():
        return None
    return PeerIdentity.load(path)


def _load_policy(mode: Optional[str] = None):
    """Load the admission policy, optionally overriding the mode."""
    from gateway.peer_link.policy import AdmissionMode, AdmissionPolicy

    data_dir = _data_dir()
    current = AdmissionMode.CLOSED
    mode_file = data_dir / "mode.txt"
    if mode_file.exists():
        try:
            current = AdmissionMode(mode_file.read_text(encoding="utf-8").strip())
        except (ValueError, OSError):
            current = AdmissionMode.CLOSED

    policy = AdmissionPolicy(data_dir / POLICY_SUBDIR, current)
    if mode is not None:
        new_mode = policy.set_mode(mode)
        # Persist the mode so the next process (and the gateway) sees it.
        data_dir.mkdir(parents=True, exist_ok=True)
        mode_file.write_text(new_mode.value, encoding="utf-8")
    return policy


def _emit(args: argparse.Namespace, payload: Dict[str, Any], text: str) -> int:
    """Print JSON or human text depending on ``--json``."""
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(text)
    return 0


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def _cmd_identity(args: argparse.Namespace) -> int:
    ident = _load_identity(create=not getattr(args, "no_create", False))
    if ident is None:
        print("No identity yet. Run: synapse peerlink identity", file=sys.stderr)
        return 1
    bundle = ident.public_bundle()
    if getattr(args, "json", False):
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
        return 0
    print("Peer Link identity")
    print(f"  peer id    : {bundle['peer_id']}")
    print(f"  public key : {bundle['public_key']}")
    print(f"  scheme     : {bundle['scheme']}")
    print()
    print("Share the peer id with someone you want to link with.")
    print("The private key never leaves this machine.")
    return 0


def _cmd_mode(args: argparse.Namespace) -> int:
    from gateway.peer_link.policy import AdmissionMode

    if not getattr(args, "mode_value", None):
        policy = _load_policy()
        print(f"Current mode: {policy.mode.value}")
        print()
        print("  closed        nothing listens (default, safest)")
        print("  invite        a valid invite code is required")
        print("  public_gated  anyone may knock, but must pay proof of work")
        print("  public_open   anyone may knock, no work required (discouraged)")
        return 0

    try:
        policy = _load_policy(args.mode_value)
    except ValueError as exc:
        print(f"Unknown mode: {exc}", file=sys.stderr)
        return 2

    mode = policy.mode
    if mode is AdmissionMode.CLOSED:
        text = "Mode set to CLOSED — nothing listens, nobody can knock."
    elif mode is AdmissionMode.INVITE:
        text = "Mode set to INVITE — a valid invite code is required to knock."
    elif mode is AdmissionMode.PUBLIC_GATED:
        text = (
            "Mode set to PUBLIC_GATED — anyone may knock, but must solve "
            "proof of work, is rate limited per key, and lands in quarantine."
        )
    else:
        text = (
            "Mode set to PUBLIC_OPEN — anyone may knock with no work. "
            "This is discouraged; quarantine still applies."
        )
    return _emit(args, {"mode": mode.value}, text)


def _cmd_invite(args: argparse.Namespace) -> int:
    """Mint a pairing code via the existing PairingStore (no new mechanism)."""
    from gateway.pairing import PairingStore

    store = PairingStore()
    code = store.generate_code("peerlink", getattr(args, "peer", "") or "unknown", "")
    if code is None:
        print(
            "Could not mint an invite code (rate limited, queue full, or "
            "locked out). Try again later.",
            file=sys.stderr,
        )
        return 1
    if getattr(args, "json", False):
        print(json.dumps({"code": code, "platform": "peerlink"}, indent=2))
        return 0
    print(f"Invite code: {code}")
    print()
    print("Send this to the other person over a DIFFERENT channel")
    print("(WhatsApp, Signal, in person). It expires in 1 hour.")
    print("It does not grant access on its own — you still approve them.")
    return 0


def _cmd_pending(args: argparse.Namespace) -> int:
    policy = _load_policy()
    rows = policy.pending()
    if getattr(args, "json", False):
        print(json.dumps({"pending": rows}, indent=2, ensure_ascii=False))
        return 0
    if not rows:
        print("No peers waiting for approval.")
        return 0
    print(f"{len(rows)} peer(s) waiting for your decision:\n")
    for row in rows:
        print(f"  {row['peer_id']}")
        print(f"      public key : {row.get('public_key', '?')}")
        print(f"      first seen : {row.get('first_seen', '?')}")
    print()
    print("These peers can speak but cannot act until you approve them.")
    print("  synapse peerlink approve <peer-id>")
    print("  synapse peerlink block <peer-id>")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    policy = _load_policy()
    trusted = policy.trusted()
    blocked = policy.blocked()
    if getattr(args, "json", False):
        print(json.dumps({"trusted": trusted, "blocked": blocked}, indent=2,
                         ensure_ascii=False))
        return 0
    print(f"Mode: {policy.mode.value}\n")
    print(f"Trusted peers ({len(trusted)}):")
    for row in trusted:
        print(f"  {row['peer_id']}")
    if not trusted:
        print("  (none)")
    print(f"\nBlocked peers ({len(blocked)}):")
    for row in blocked:
        print(f"  {row['peer_id']}")
    if not blocked:
        print("  (none)")
    return 0


def _cmd_approve(args: argparse.Namespace) -> int:
    policy = _load_policy()
    if not policy.promote(args.peer_id):
        print(f"No such peer: {args.peer_id}", file=sys.stderr)
        return 1
    return _emit(args, {"peer_id": args.peer_id, "state": "trusted"},
                 f"Approved. {args.peer_id} is now a trusted peer.")


def _cmd_block(args: argparse.Namespace) -> int:
    policy = _load_policy()
    if not policy.block(args.peer_id):
        print(f"No such peer: {args.peer_id}", file=sys.stderr)
        return 1
    return _emit(args, {"peer_id": args.peer_id, "state": "blocked"},
                 f"Blocked. {args.peer_id} can no longer connect.")


def _cmd_revoke(args: argparse.Namespace) -> int:
    policy = _load_policy()
    if not policy.revoke(args.peer_id):
        print(f"No such peer: {args.peer_id}", file=sys.stderr)
        return 1
    return _emit(args, {"peer_id": args.peer_id, "state": "forgotten"},
                 f"Revoked. {args.peer_id} is a stranger again.")


def _cmd_status(args: argparse.Namespace) -> int:
    policy = _load_policy()
    ident = _load_identity(create=False)
    payload = {
        "peer_id": ident.peer_id if ident else None,
        "mode": policy.mode.value,
        "difficulty": policy.current_difficulty(),
        "trusted": len(policy.trusted()),
        "pending": len(policy.pending()),
        "blocked": len(policy.blocked()),
    }
    text = (
        f"Peer Link status\n"
        f"  our peer id : {payload['peer_id'] or '(none yet)'}\n"
        f"  mode        : {payload['mode']}\n"
        f"  difficulty  : {payload['difficulty']} bits\n"
        f"  trusted     : {payload['trusted']}\n"
        f"  pending     : {payload['pending']}\n"
        f"  blocked     : {payload['blocked']}"
    )
    return _emit(args, payload, text)


def _cmd_endpoint(args: argparse.Namespace) -> int:
    """Show (or mint) this instance's unguessable address."""
    from gateway.peer_link.endpoint import EndpointRegistry, certificate_note

    base = getattr(args, "base_domain", None) or None
    mode = getattr(args, "address_mode", None) or _default_address_mode()
    registry = EndpointRegistry(_data_dir(), base or _default_base_domain(), mode)
    hostname = registry.own_hostname(create=not getattr(args, "peek", False))
    if hostname is None:
        return _emit(
            args,
            {"hostname": None, "note": "no address minted yet"},
            "No address minted yet. Run 'synapse peerlink endpoint' to create one.",
        )
    address = registry.own_address(create=not getattr(args, "peek", False))
    url = registry.own_url(create=not getattr(args, "peek", False))
    payload = {
        "hostname": hostname,
        "address": address,
        "url": url,
        "address_mode": registry.mode,
        "base_domain": registry.base_domain,
        "certificate": certificate_note(
            registry.base_domain, _default_zone_apex() or None, registry.mode
        ),
    }
    text = (
        f"Your Peer Link address\n"
        f"  url      : {url}\n"
        f"  address  : {address}\n"
        f"  hostname : {hostname}\n"
        f"  mode     : {registry.mode}\n"
        f"  base     : {registry.base_domain}\n"
        f"\n"
        f"  Share the url with the peer you are linking with. The label is\n"
        f"  random, so it cannot be guessed from your peer id — but it is NOT a\n"
        f"  secret lock: admission is still decided by mode + your approval.\n"
        f"\n"
        f"  TLS note : {payload['certificate']}"
    )
    return _emit(args, payload, text)


def _cmd_rotate(args: argparse.Namespace) -> int:
    """Mint a new address, invalidating the old one."""
    from gateway.peer_link.endpoint import EndpointRegistry

    base = getattr(args, "base_domain", None) or _default_base_domain()
    mode = getattr(args, "address_mode", None) or _default_address_mode()
    registry = EndpointRegistry(_data_dir(), base, mode)
    address = registry.rotate()
    url = registry.own_url(create=False)
    return _emit(
        args,
        {"url": url, "address": address, "address_mode": registry.mode},
        f"New address: {url}\nThe previous address no longer resolves.",
    )


_ACTIONS: Dict[str, Callable[[argparse.Namespace], int]] = {
    "identity": _cmd_identity,
    "mode": _cmd_mode,
    "invite": _cmd_invite,
    "pending": _cmd_pending,
    "list": _cmd_list,
    "approve": _cmd_approve,
    "block": _cmd_block,
    "revoke": _cmd_revoke,
    "status": _cmd_status,
    "endpoint": _cmd_endpoint,
    "rotate": _cmd_rotate,
}


def cmd_peerlink(args: argparse.Namespace) -> int:
    """Dispatch ``synapse peerlink <action>``."""
    action = getattr(args, "peerlink_action", None)
    handler = _ACTIONS.get(action or "")
    if handler is None:
        print("Usage: synapse peerlink <identity|mode|invite|pending|list|"
              "approve|block|revoke|status|endpoint|rotate>", file=sys.stderr)
        return 2
    try:
        return handler(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # keep the CLI from dumping a raw traceback
        print(f"peerlink: {exc}", file=sys.stderr)
        return 1


def build_peerlink_parser(subparsers) -> None:
    """Attach the ``peerlink`` subcommand to ``subparsers``."""
    parser = subparsers.add_parser(
        "peerlink",
        help="Link this Synapse instance to another user's (off by default)",
        description=(
            "Connect two Synapse instances belonging to different users. "
            "Disabled by default; nothing listens until you set a mode. "
            "No peer is ever trusted automatically — new peers land in "
            "quarantine and require an explicit 'peerlink approve'."
        ),
        epilog=(
            "Examples:\n"
            "  synapse peerlink identity\n"
            "  synapse peerlink mode invite\n"
            "  synapse peerlink invite --note \"Budi\"\n"
            "  synapse peerlink pending\n"
            "  synapse peerlink approve pl1abc...\n"
            "  synapse peerlink block pl1abc...\n"
            "  synapse peerlink endpoint\n"
            "  synapse peerlink status\n"
            "\n"
            "Modes: closed (default) | invite | public_gated | public_open\n"
            "\n"
            "Set the address base in config.yaml:\n"
            "  peer_link:\n"
            "    base_domain: aikernel.qzz.io\n"
            "Exit codes: 0 ok, 1 error, 2 usage error."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="peerlink_action")

    p_identity = sub.add_parser("identity", help="Show (or create) our peer id")
    p_identity.add_argument("--no-create", action="store_true",
                            help="Fail instead of creating an identity")
    p_identity.add_argument("--json", action="store_true")

    p_mode = sub.add_parser("mode", help="Show or set the admission mode")
    p_mode.add_argument("mode_value", nargs="?", default=None,
                        choices=["closed", "invite", "public_gated", "public_open"],
                        help="New mode (omit to show the current one)")
    p_mode.add_argument("--json", action="store_true")

    p_invite = sub.add_parser("invite", help="Mint an invite code to share")
    p_invite.add_argument("--peer", default="", help="Label for who this is for")
    p_invite.add_argument("--note", default="", help=argparse.SUPPRESS)
    p_invite.add_argument("--json", action="store_true")

    p_pending = sub.add_parser("pending", help="Peers waiting for your decision")
    p_pending.add_argument("--json", action="store_true")

    p_list = sub.add_parser("list", help="List trusted and blocked peers")
    p_list.add_argument("--json", action="store_true")

    for name, helptext in (
        ("approve", "Approve a quarantined peer (owner's decision)"),
        ("block", "Refuse a peer permanently"),
        ("revoke", "Forget a peer entirely"),
    ):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("peer_id", help="Peer id, e.g. pl1abc...")
        p.add_argument("--json", action="store_true")

    p_endpoint = sub.add_parser(
        "endpoint", help="Show (or mint) our unguessable address")
    p_endpoint.add_argument("--peek", action="store_true",
                            help="Read only; never mint a new address")
    p_endpoint.add_argument("--base-domain", default=None,
                            help="Override the base domain for this call")
    p_endpoint.add_argument("--address-mode", default=None,
                            choices=["subdomain", "path"],
                            help="Override the addressing mode for this call")
    p_endpoint.add_argument("--json", action="store_true")

    p_rotate = sub.add_parser(
        "rotate", help="Mint a new address (invalidates the old one)")
    p_rotate.add_argument("--base-domain", default=None)
    p_rotate.add_argument("--address-mode", default=None,
                          choices=["subdomain", "path"])
    p_rotate.add_argument("--json", action="store_true")

    p_status = sub.add_parser("status", help="Show Peer Link status")
    p_status.add_argument("--json", action="store_true")

    parser.set_defaults(func=cmd_peerlink)
