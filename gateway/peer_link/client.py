"""Peer Link — the client side of the handshake.

This is what runs when someone points their instance at a peer URL. It is the
other half of :mod:`gateway.peer_link.server`, and it exists so that the whole
"connect to a peer" story is one command rather than a curl incantation.

Uses :mod:`urllib.request` from the standard library. That is a deliberate
choice: adding an HTTP client dependency for two POST requests would be a new
dependency the repo does not need, and new dependencies are a PR-rejection risk
(see AGENTS.md). ``urllib`` is unglamorous and entirely sufficient here.

The client verifies the server's signature before trusting anything it says.
That is the point of a mutual handshake: without this check the client would be
talking to whoever controls the DNS record, and would have no way to tell.

Transport note, stated plainly: this module speaks **http://** and **https://**.
Over plain HTTP the handshake is still cryptographically meaningful — the
signatures prove identity regardless of the transport — but the peer's label and
traffic are readable in transit. The docs tell users to prefer https, and
:func:`connect` records which scheme was used so a caller can refuse plain http
if it wants to be strict.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

from gateway.peer_link import wire
from gateway.peer_link.identity import PeerIdentity, peer_id_from_public_key
from gateway.peer_link.policy import solve_work

#: How long to wait for a peer to answer. A peer that cannot complete a
#: handshake in this long is not going to; better to fail than to hang a CLI.
DEFAULT_TIMEOUT = 20.0


@dataclass
class HandshakeResult:
    """What came back from a completed (or failed) handshake."""

    ok: bool
    reason: str
    peer_id: Optional[str] = None
    state: Optional[str] = None
    authenticated: bool = False
    retry_after: Optional[int] = None
    #: True when the URL was https. Callers that insist on confidentiality in
    #: transit check this rather than re-parsing the URL.
    secure_transport: bool = False

    def __bool__(self) -> bool:
        return self.ok


class PeerLinkClient:
    """Talks to one peer address."""

    def __init__(
        self,
        identity: PeerIdentity,
        base_url: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.identity = identity
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)

    @property
    def secure_transport(self) -> bool:
        return self.base_url.lower().startswith("https://")

    # ----- HTTP ---------------------------------------------------------

    def _post(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """POST one handshake message. Returns the parsed reply, or None.

        A non-2xx response is *not* an exception: a refusal is a legitimate
        answer that the caller needs to read (it carries the reason and any
        ``retry_after``), so it is returned rather than raised.
        """
        body = wire.encode_message(payload)
        request = urllib.request.Request(
            self.base_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "User-Agent": "synapse-peerlink/1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read(wire.MAX_BODY_BYTES + 1)
                return wire.decode_message(raw)
        except urllib.error.HTTPError as exc:
            # The body of a 4xx is where the reason lives; read it rather than
            # collapsing every refusal into "HTTP error".
            try:
                raw = exc.read(wire.MAX_BODY_BYTES + 1)
            except Exception:  # noqa: BLE001 - a broken error body is not fatal
                return None
            return wire.decode_message(raw)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            # Unreachable, refused, timed out, bad URL: all "no answer", which
            # the caller reports as a failed handshake rather than a traceback.
            return None

    # ----- the handshake ------------------------------------------------

    def connect(self, *, invite_code: str = "") -> HandshakeResult:
        """Run the full handshake against the peer.

        Never raises: every failure mode is a :class:`HandshakeResult` with
        ``ok=False`` and a reason a human can act on.
        """
        client_challenge = wire.new_challenge()

        hello: Dict[str, Any] = {
            "type": wire.HELLO,
            "version": wire.HANDSHAKE_VERSION,
            "peer_id": self.identity.peer_id,
            "public_key": self.identity.public_key_b64,
            "challenge": client_challenge,
        }
        if invite_code:
            hello["invite_code"] = invite_code

        # Read the difficulty the server currently wants before solving, so the
        # proof is neither wasted nor under-priced when a flood raised it. A
        # probe that fails (older peer, no such route) degrades to difficulty 0,
        # which the server will simply reject — never a crash.
        probe = self._post({"type": wire.CHALLENGE, "version": wire.HANDSHAKE_VERSION}) or {}
        difficulty = int(probe.get("difficulty") or 0)
        hello["nonce"] = solve_work(self.identity.public_key_bytes, difficulty)

        reply = self._post(hello)
        if reply is None:
            return HandshakeResult(False, "no response from peer", secure_transport=self.secure_transport)

        # A refusal before welcome is the normal path for a closed door, a bad
        # invite, or a rate limit — report it with its reason, not as an error.
        if reply.get("type") != wire.WELCOME:
            return HandshakeResult(
                False,
                str(reply.get("reason") or reply.get("error") or "handshake refused"),
                state=reply.get("state"),
                retry_after=reply.get("retry_after"),
                secure_transport=self.secure_transport,
            )

        if not wire.is_supported_version(reply.get("version")):
            return HandshakeResult(False, "peer speaks an unsupported protocol version", secure_transport=self.secure_transport)

        server_public_key = str(reply.get("public_key") or "")
        server_peer_id = str(reply.get("peer_id") or "")
        server_challenge = str(reply.get("challenge") or "")
        if not server_public_key or len(server_challenge) != 64:
            return HandshakeResult(False, "peer sent a malformed welcome", secure_transport=self.secure_transport)

        # Verify the server's signature BEFORE trusting the peer id it claimed.
        # Without this the client would accept any id from whoever holds the
        # address, which is exactly the impersonation the handshake exists to
        # prevent.
        try:
            signature = base64.b64decode(str(reply.get("signature") or ""), validate=True)
            server_key = base64.b64decode(server_public_key, validate=True)
        except Exception:
            return HandshakeResult(False, "peer signature is not valid base64", secure_transport=self.secure_transport)

        transcript = wire.server_transcript(
            client_challenge, self.identity.peer_id, server_peer_id, server_challenge
        )
        if not PeerIdentity.verify(server_key, signature, transcript):
            return HandshakeResult(
                False,
                "peer could not prove it holds the key it claimed",
                secure_transport=self.secure_transport,
            )

        # The server's claimed id must match its key, same rule as ours.
        if peer_id_from_public_key(server_key) != server_peer_id:
            return HandshakeResult(False, "peer id does not match its public key", secure_transport=self.secure_transport)

        confirm_transcript = wire.client_transcript(
            client_challenge, self.identity.peer_id, server_peer_id, server_challenge
        )
        confirm_signature = base64.b64encode(
            self.identity.sign(confirm_transcript)
        ).decode("ascii")

        final = self._post(
            {
                "type": wire.CONFIRM,
                "version": wire.HANDSHAKE_VERSION,
                "peer_id": self.identity.peer_id,
                "public_key": self.identity.public_key_b64,
                "signature": confirm_signature,
            }
        )
        if final is None:
            return HandshakeResult(False, "peer did not answer the confirmation", secure_transport=self.secure_transport)
        if not final.get("authenticated"):
            return HandshakeResult(
                False,
                str(final.get("error") or final.get("reason") or "peer rejected our confirmation"),
                secure_transport=self.secure_transport,
            )

        return HandshakeResult(
            True,
            "mutually authenticated",
            peer_id=server_peer_id,
            state=reply.get("state"),
            authenticated=True,
            secure_transport=self.secure_transport,
        )


def normalise_peer_url(url: str) -> str:
    """Turn what a human pastes into a URL we can POST to.

    Accepts ``host``, ``host/path``, and full URLs with or without a scheme.
    Defaults to **https**, because silently downgrading a user's pasted address
    to plain http would weaken a security-relevant default without telling them.
    """
    text = (url or "").strip()
    if not text:
        raise ValueError("empty peer address")
    if "://" not in text:
        text = "https://" + text
    parsed = urllib.parse.urlparse(text)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"unsupported scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise ValueError(f"no hostname in peer address: {url!r}")
    return text.rstrip("/")


def connect(
    identity: PeerIdentity,
    url: str,
    *,
    invite_code: str = "",
    timeout: float = DEFAULT_TIMEOUT,
) -> HandshakeResult:
    """Convenience wrapper: normalise *url*, then handshake. Never raises on a
    network problem; raises only on a genuinely unusable URL."""
    return PeerLinkClient(
        identity, normalise_peer_url(url), timeout=timeout
    ).connect(invite_code=invite_code)
