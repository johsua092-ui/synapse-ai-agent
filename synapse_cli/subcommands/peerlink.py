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

    share_link = ""
    if getattr(args, "qr", False):
        share_link = _share_link_for(code)

    if getattr(args, "json", False):
        out = {"code": code, "platform": "peerlink"}
        if share_link:
            out["share_link"] = share_link
        print(json.dumps(out, indent=2))
        return 0

    print(f"Invite code: {code}")
    if share_link:
        _print_qr_block(share_link)
    print()
    print("Send this to the other person over a DIFFERENT channel")
    print("(WhatsApp, Signal, in person). It expires in 1 hour.")
    print("It does not grant access on its own — you still approve them.")
    return 0


def _share_link_for(code: str) -> str:
    """Compose our own share link (address + code) for QR rendering.

    Returns ``""`` when we have no address yet — a QR of a bare code would be
    worse than useless, since the scanner would have nothing to dial.
    """
    from gateway.peer_link.client import build_share_link
    from gateway.peer_link.endpoint import EndpointRegistry

    try:
        registry = EndpointRegistry(
            _data_dir(),
            _default_base_domain(),
            _default_address_mode(),
        )
        url = registry.own_url(create=True)
    except Exception:  # noqa: BLE001 - no address yet is a normal state
        return ""
    if not url:
        return ""
    return build_share_link(str(url), code)


def _print_qr_block(share_link: str) -> None:
    """Print the QR when ``qrcode`` is available; stay silent when it is not.

    Silence rather than an error message: the plain link printed by the caller
    is always enough, and a scary warning about an optional renderer would make
    a working command look broken.
    """
    from gateway.peer_link.qr import render_qr

    art = render_qr(share_link)
    if not art:
        return
    print()
    print("Scan this to link (carries the address AND the code):")
    print(art)
    print(f"  {share_link}")


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


def _cmd_serve(args: argparse.Namespace) -> int:
    """Run the listener. This is the command that makes a peer URL real.

    Everything else in ``peerlink`` composes an address; this is the only
    command that makes something *answer* at it. It blocks until Ctrl-C, so it
    is deliberately not the default action of anything else.

    Refuses to start while the mode is ``closed`` — that refusal lives in
    :class:`PeerLinkServer`, so the CLI cannot bypass it.
    """
    from gateway.peer_link.endpoint import EndpointRegistry
    from gateway.peer_link.server import DEFAULT_PORT, PeerLinkServer

    ident = _load_identity(create=True)
    policy = _load_policy()
    base = getattr(args, "base_domain", None) or _default_base_domain()
    mode = getattr(args, "address_mode", None) or _default_address_mode()
    registry = EndpointRegistry(_data_dir(), base, mode)
    if ident is None:  # create=True, so only reachable if the write failed
        print("peerlink: could not create a peer identity", file=sys.stderr)
        return 1

    host = getattr(args, "host", None) or "0.0.0.0"
    port = getattr(args, "port", None) or DEFAULT_PORT
    # The *label*, not own_hostname(): in path mode the hostname is the shared
    # base domain, and the listener must match on the part that is ours.
    label = registry.own_label(create=True)
    url = registry.own_url(create=False)

    server = PeerLinkServer(ident, policy, host=host, port=port, label=label)
    bound_host, bound_port = server.address
    print(f"Peer Link listening on {bound_host}:{bound_port}")
    print(f"  public url : {url}")
    print(f"  mode       : {policy.mode.value}")
    print(f"  our peer id: {ident.peer_id}")
    print()
    print("  Nothing is trusted automatically — new peers land in quarantine")
    print("  and wait for `synapse peerlink approve <peer-id>`.")
    print()
    # The listener speaks plain HTTP by design: terminating TLS in Python would
    # mean shipping a certificate-loading, cipher-configuring, renewal-tracking
    # server, which nginx already does better. So the warning is unconditional —
    # an https:// public URL in front of a plain listener means someone still
    # has to put a TLS terminator there, and silently implying otherwise is how
    # a peer ends up dialling a name that hands out plaintext.
    print("  NOTE: this listener speaks plain HTTP. The https:// URL above")
    print("  only works once a TLS terminator (nginx, caddy, …) sits in front")
    print("  of it and proxies /peer/<label> to this port.")
    print()
    print("  Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        server.stop()
    return 0


def _cmd_connect(args: argparse.Namespace) -> int:
    """Dial a peer URL and complete the mutual handshake.

    This is the command a stranger runs. It needs nothing but the URL: no
    account, no port forwarding, no domain of their own.
    """
    from gateway.peer_link.client import connect, normalise_peer_url, split_share_link

    raw = getattr(args, "url", None) or ""
    # A share link carries the invite code in its fragment. Split it off before
    # normalising, so the code is sent in the handshake and never in the URL we
    # POST to (a fragment is not transmitted; a query string would be logged).
    raw_url, embedded_code = split_share_link(raw)
    code = getattr(args, "code", None) or embedded_code
    try:
        url = normalise_peer_url(raw_url)
    except ValueError as exc:
        print(f"peerlink: {exc}", file=sys.stderr)
        return 2

    ident = _load_identity(create=True)
    timeout = float(getattr(args, "timeout", None) or 15.0)
    result = connect(ident, url, invite_code=code, timeout=timeout)

    payload = {
        "ok": result.ok,
        "url": url,
        "peer_id": result.peer_id,
        "state": result.state,
        "authenticated": result.authenticated,
        "reason": result.reason,
        "used_invite_code": bool(code),
    }
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if result.ok else 1

    if not result.ok:
        print(f"Could not link with {url}")
        print(f"  reason: {result.reason}")
        return 1

    print(f"Linked with {url}")
    print(f"  their peer id : {result.peer_id}")
    print(f"  authenticated : {result.authenticated}")
    print(f"  state         : {result.state}")
    if code:
        print("  invite code   : accepted")
    if result.state == "quarantined":
        print()
        print("  They still have to approve you on their side before anything")
        print("  can be shared. That decision is theirs, not the AI's.")
    return 0


def _cmd_send(args: argparse.Namespace) -> int:
    """Send a text message to a trusted peer."""
    import json as _json
    from gateway.peer_link.mailbox import PeerMailbox
    from gateway.peer_link.messenger import send_message

    identity = _load_identity(create=False)
    if identity is None:
        print("peerlink: no identity yet — run `synapse peerlink identity` first",
              file=sys.stderr)
        return 1

    # Resolve peer url from trusted list
    policy = _load_policy()
    trusted = policy.list_peers()  # all states; we filter below
    target_url: str = getattr(args, "peer_url", "")
    target_peer_id: str = getattr(args, "peer_id_or_url", "")

    # If the arg looks like a URL use it directly; otherwise treat as peer_id prefix
    if target_peer_id.startswith("http"):
        target_url = target_peer_id
        # derive to_peer_id from trusted list by matching url
        to_peer_id = getattr(args, "to_peer_id", None) or ""
        if not to_peer_id:
            print("peerlink: pass --to <peer_id> when using a raw URL", file=sys.stderr)
            return 1
    else:
        # find peer by id prefix
        matches = [p for p in policy.trusted() if p["peer_id"].startswith(target_peer_id)]
        if not matches:
            print(f"peerlink: no trusted peer matching {target_peer_id!r}", file=sys.stderr)
            print("  Run `synapse peerlink list` to see trusted peers.", file=sys.stderr)
            return 1
        if len(matches) > 1:
            print(f"peerlink: ambiguous prefix {target_peer_id!r} — be more specific",
                  file=sys.stderr)
            return 1
        peer = matches[0]
        to_peer_id = peer["peer_id"]
        target_url = peer.get("address") or peer.get("url") or ""
        if not target_url:
            print(f"peerlink: no address recorded for peer {to_peer_id}", file=sys.stderr)
            print("  Ask the peer to run `synapse peerlink serve` and share their URL.",
                  file=sys.stderr)
            return 1
        # normalise to https URL
        if not target_url.startswith("http"):
            target_url = f"https://{target_url}"

    text = " ".join(args.message)
    if not text.strip():
        print("peerlink: message cannot be empty", file=sys.stderr)
        return 1

    result = send_message(
        identity=identity,
        peer_url=target_url,
        to_peer_id=to_peer_id,
        text=text,
        timeout=getattr(args, "timeout", None) or 15.0,
    )
    payload = {"ok": result.ok, "reason": result.reason}
    if getattr(args, "json", False):
        print(_json.dumps(payload))
        return 0 if result.ok else 1

    if result.ok:
        print(f"✓ Message delivered to {to_peer_id[:20]}...")
    else:
        print(f"✗ Failed: {result.reason}", file=sys.stderr)
    return 0 if result.ok else 1


def _cmd_inbox(args: argparse.Namespace) -> int:
    """Read messages in the local mailbox."""
    import json as _json
    from pathlib import Path
    from gateway.peer_link.mailbox import PeerMailbox

    mailbox_path = _data_dir() / "mailbox.json"
    mailbox = PeerMailbox(mailbox_path)

    peer_filter: str = getattr(args, "peer_id", None) or ""
    drain: bool = getattr(args, "drain", False)

    if drain:
        msgs = mailbox.drain(peer_filter or None)
    else:
        msgs = mailbox.peek(peer_filter or None)

    if getattr(args, "json", False):
        print(_json.dumps([m.to_dict() for m in msgs]))
        return 0

    if not msgs:
        print("Inbox empty." if not peer_filter else f"No messages from {peer_filter}.")
        return 0

    for m in msgs:
        import datetime
        ts_str = datetime.datetime.fromtimestamp(m.ts).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts_str}] from {m.from_peer_id[:20]}...")
        print(f"  {m.text}")
        print()
    if drain:
        print(f"({len(msgs)} message(s) removed from inbox)")
    return 0


def _resolve_trusted_peer(args: argparse.Namespace, policy):
    """Helper: resolve peer_id_or_url to (to_peer_id, peer_url) from trusted list."""
    target: str = getattr(args, "peer_id_or_url", "")
    if target.startswith("http"):
        to_peer_id = getattr(args, "to_peer_id", None) or ""
        if not to_peer_id:
            return None, None, "pass --to <peer_id> when using a raw URL"
        return to_peer_id, target, None
    matches = [p for p in policy.trusted() if p["peer_id"].startswith(target)]
    if not matches:
        return None, None, f"no trusted peer matching {target!r} — run `synapse peerlink list`"
    if len(matches) > 1:
        return None, None, f"ambiguous prefix {target!r} — be more specific"
    peer = matches[0]
    to_peer_id = peer["peer_id"]
    peer_url = peer.get("address") or peer.get("url") or ""
    if not peer_url:
        return to_peer_id, None, f"no address for peer {to_peer_id} — ask them to share their URL"
    if not peer_url.startswith("http"):
        peer_url = f"https://{peer_url}"
    return to_peer_id, peer_url, None


def _cmd_debate(args: argparse.Namespace) -> int:
    """Run an autonomous N-round debate with a trusted peer."""
    import json as _json
    from pathlib import Path
    from gateway.peer_link.mailbox import PeerMailbox
    from gateway.peer_link.session import PeerSession

    identity = _load_identity(create=False)
    if identity is None:
        print("peerlink: no identity yet", file=sys.stderr)
        return 1

    policy = _load_policy()
    to_peer_id, peer_url, err = _resolve_trusted_peer(args, policy)
    if err:
        print(f"peerlink: {err}", file=sys.stderr)
        return 1

    mailbox_path = _data_dir() / "mailbox.json"
    mailbox = PeerMailbox(mailbox_path)
    session = PeerSession(identity, to_peer_id, peer_url, mailbox,
                          timeout=getattr(args, "timeout", None) or 20.0)

    opening = " ".join(args.prompt)
    rounds = getattr(args, "rounds", 3)
    transcript = []

    def on_turn(round_n, side, text):
        entry = {"round": round_n, "side": side, "text": text}
        transcript.append(entry)
        if not getattr(args, "json", False):
            label = {"local": "You→", "remote": "Peer←",
                     "local_reply": "You→", "error": "ERR "}.get(side, side)
            preview = text[:120].replace("\n", " ")
            print(f"[{round_n}/{rounds}] {label} {preview}")

    result_transcript = session.debate(opening, rounds=rounds, on_turn=on_turn)

    if getattr(args, "json", False):
        print(_json.dumps(result_transcript))
    else:
        print(f"\nDebate complete — {len(result_transcript)} turns.")
    return 0


def _cmd_skill_share(args: argparse.Namespace) -> int:
    """Pack and send a local skill to a trusted peer."""
    import json as _json
    from gateway.peer_link.session import PeerSession
    from gateway.peer_link.mailbox import PeerMailbox

    identity = _load_identity(create=False)
    if identity is None:
        print("peerlink: no identity yet", file=sys.stderr)
        return 1

    policy = _load_policy()
    to_peer_id, peer_url, err = _resolve_trusted_peer(args, policy)
    if err:
        print(f"peerlink: {err}", file=sys.stderr)
        return 1

    mailbox_path = _data_dir() / "mailbox.json"
    mailbox = PeerMailbox(mailbox_path)
    session = PeerSession(identity, to_peer_id, peer_url, mailbox)

    skill_name = args.skill_name
    result = session.send_skill(skill_name)
    payload = {"ok": result.ok, "skill": skill_name, "reason": result.reason}

    if getattr(args, "json", False):
        print(_json.dumps(payload))
        return 0 if result.ok else 1

    if result.ok:
        print(f"✓ Skill {skill_name!r} sent to {to_peer_id[:20]}...")
    else:
        print(f"✗ Failed: {result.reason}", file=sys.stderr)
    return 0 if result.ok else 1


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
    "serve": _cmd_serve,
    "connect": _cmd_connect,
    "send": _cmd_send,
    "inbox": _cmd_inbox,
    "debate": _cmd_debate,
    "skill-share": _cmd_skill_share,
}


def cmd_peerlink(args: argparse.Namespace) -> int:
    """Dispatch ``synapse peerlink <action>``."""
    action = getattr(args, "peerlink_action", None)
    handler = _ACTIONS.get(action or "")
    if handler is None:
        print("Usage: synapse peerlink <identity|mode|invite|pending|list|"
              "approve|block|revoke|status|endpoint|rotate|serve|connect>",
              file=sys.stderr)
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
            "  synapse peerlink endpoint\n"
            "  synapse peerlink serve\n"
            "  synapse peerlink invite --peer Budi --qr\n"
            "  synapse peerlink connect <peer-url>\n"
            "  synapse peerlink pending\n"
            "  synapse peerlink approve pl1abc...\n"
            "  synapse peerlink block pl1abc...\n"
            "  synapse peerlink status\n"
            "\n"
            "Modes: closed (default) | invite | public_gated | public_open\n"
            "\n"
            "Set the address base in config.yaml:\n"
            "  peer_link:\n"
            "    base_domain: synz.zone.id\n"
            "    address_mode: path\n"
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
    p_invite.add_argument("--qr", action="store_true",
                          help="Also render a scannable QR of address + code")
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

    p_serve = sub.add_parser(
        "serve", help="Run the listener (makes your peer URL actually answer)")
    p_serve.add_argument("--host", default=None,
                         help="Bind address (default 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=None,
                         help="Bind port (default 8443)")
    p_serve.add_argument("--base-domain", default=None,
                         help="Override the base domain for this call")
    p_serve.add_argument("--address-mode", default=None,
                         choices=["subdomain", "path"],
                         help="Override the addressing mode for this call")

    p_connect = sub.add_parser(
        "connect", help="Link to a peer URL (needs nothing but the URL)")
    p_connect.add_argument("url", help="Peer URL, e.g. https://synz.zone.id/peer/abc")
    p_connect.add_argument("--code", default=None,
                           help="Invite code (auto-read from a share link's #c=)")
    p_connect.add_argument("--timeout", type=float, default=None,
                           help="Per-request timeout in seconds (default 15)")
    p_connect.add_argument("--json", action="store_true")

    p_send = sub.add_parser(
        "send", help="Send a text message to a trusted peer")
    p_send.add_argument(
        "peer_id_or_url",
        help="Peer id prefix (e.g. pl1abc...) or a raw https:// URL",
    )
    p_send.add_argument(
        "message",
        nargs="+",
        help="Message text (all remaining arguments joined with spaces)",
    )
    p_send.add_argument("--to", dest="to_peer_id", default=None,
                        help="Receiver peer id (required when peer_id_or_url is a URL)")
    p_send.add_argument("--timeout", type=float, default=None)
    p_send.add_argument("--json", action="store_true")

    p_inbox = sub.add_parser(
        "inbox", help="Read inbound messages from trusted peers")
    p_inbox.add_argument("--peer", dest="peer_id", default=None,
                         help="Filter by sender peer id prefix")
    p_inbox.add_argument("--drain", action="store_true",
                         help="Remove messages after reading")
    p_inbox.add_argument("--json", action="store_true")

    p_debate = sub.add_parser(
        "debate", help="Run autonomous N-round debate with a trusted peer")
    p_debate.add_argument(
        "peer_id_or_url",
        help="Peer id prefix or https:// peer URL")
    p_debate.add_argument(
        "prompt",
        nargs="+",
        help="Opening prompt sent to the remote peer")
    p_debate.add_argument("--rounds", type=int, default=3,
                          help="Number of full send/receive cycles (default 3)")
    p_debate.add_argument("--timeout", type=float, default=None)
    p_debate.add_argument("--json", action="store_true")

    p_skill_share = sub.add_parser(
        "skill-share", help="Send one of your skills to a trusted peer")
    p_skill_share.add_argument(
        "peer_id_or_url",
        help="Peer id prefix or https:// peer URL")
    p_skill_share.add_argument("skill_name", help="Skill name to share")
    p_skill_share.add_argument("--json", action="store_true")

    parser.set_defaults(func=cmd_peerlink)
