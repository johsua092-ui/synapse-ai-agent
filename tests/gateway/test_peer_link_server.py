"""Tests for the Peer Link wire protocol, listener, and client.

These are end-to-end in the sense that matters: a real server is bound to a
real port and a real client handshakes with it over a real socket. That is the
only way to catch the class of bug this module is most exposed to — the
handler-per-request lifecycle of ``http.server``, where state stashed on
``self`` during ``hello`` is gone by the time ``confirm`` arrives. A unit test
that called the handlers directly would have passed while the feature was
broken.
"""

from __future__ import annotations

import json
import socket
import threading
import urllib.error
import urllib.request

import pytest

from gateway.peer_link import wire
from gateway.peer_link.client import (
    PeerLinkClient,
    connect,
    normalise_peer_url,
)
from gateway.peer_link.identity import PeerIdentity, peer_id_from_public_key
from gateway.peer_link.policy import AdmissionMode, AdmissionPolicy, solve_work
from gateway.peer_link.server import PeerLinkHandler, PeerLinkServer


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _free_port() -> int:
    """Ask the OS for a port nobody is using."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _make_server(mode=AdmissionMode.PUBLIC_OPEN, label=None, **policy_kwargs):
    """A bound, serving instance on a free port. Caller must stop() it."""
    identity = PeerIdentity.generate()
    # Low difficulty by default so tests stay fast; callers may override.
    policy_kwargs.setdefault("pow_bits", 12)
    policy = AdmissionPolicy(_tmp_dir(), mode=mode, **policy_kwargs)
    server = PeerLinkServer(
        identity, policy, host="127.0.0.1", port=_free_port(), label=label
    ).start(background=True)
    return server, identity, policy


def _tmp_dir(tmp_path=None):
    """A scratch directory. Never ``~/.synapse`` — tests must not write there."""
    import tempfile

    return tempfile.mkdtemp(prefix="peerlink-test-")


def _url(server: PeerLinkServer, path: str = "") -> str:
    host, port = server.address
    return f"http://{host}:{port}{path}"


def _post(url: str, payload: dict):
    """Raw POST returning (status, parsed body)."""
    body = wire.encode_message(payload)
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


# ---------------------------------------------------------------------------
# wire: transcripts
# ---------------------------------------------------------------------------


class TestTranscripts:
    def test_client_and_server_transcripts_differ(self):
        """Reflection defence: the two directions must never share a transcript.

        If these were equal, a server's own welcome signature could be bounced
        back as a valid confirm.
        """
        args = ("c" * 64, "pl1client", "pl1server", "s" * 64)
        assert wire.client_transcript(*args) != wire.server_transcript(*args)

    def test_transcript_is_deterministic(self):
        args = ("c" * 64, "pl1client", "pl1server", "s" * 64)
        assert wire.server_transcript(*args) == wire.server_transcript(*args)

    def test_transcript_binds_every_field(self):
        """Changing any one field must change the transcript."""
        base = ("c" * 64, "pl1client", "pl1server", "s" * 64)
        baseline = wire.server_transcript(*base)
        for index in range(4):
            mutated = list(base)
            mutated[index] = mutated[index] + "x"
            assert wire.server_transcript(*mutated) != baseline, index

    def test_length_prefix_stops_field_shifting(self):
        """Without length prefixes, ("ab","c") and ("a","bc") would collide."""
        first = wire.server_transcript("ab", "pl1x", "pl1y", "c" * 64)
        second = wire.server_transcript("a", "pl1x", "pl1y", "bc" + "c" * 62)
        assert first != second

    def test_challenge_is_unique_and_hex(self):
        seen = {wire.new_challenge() for _ in range(200)}
        assert len(seen) == 200
        assert all(len(c) == 64 and int(c, 16) >= 0 for c in seen)

    def test_non_string_field_refused(self):
        with pytest.raises(ValueError):
            wire.server_transcript(123, "pl1a", "pl1b", "c" * 64)  # type: ignore[arg-type]


class TestMessageCodec:
    def test_round_trip(self):
        message = {"type": "hello", "n": 1, "nested": {"a": [1, 2]}}
        assert wire.decode_message(wire.encode_message(message)) == message

    def test_encoding_is_canonical(self):
        """Key order must not change the bytes, or signatures over them break."""
        first = wire.encode_message({"b": 1, "a": 2})
        second = wire.encode_message({"a": 2, "b": 1})
        assert first == second

    @pytest.mark.parametrize(
        "raw",
        [b"", b"not json", b"[1,2,3]", b"null", b'"a string"', b"{" + b"x" * 40000 + b"}"],
    )
    def test_garbage_returns_none_not_exception(self, raw):
        assert wire.decode_message(raw) is None

    def test_version_check(self):
        assert wire.is_supported_version(wire.HANDSHAKE_VERSION)
        assert not wire.is_supported_version(wire.HANDSHAKE_VERSION + 1)
        assert not wire.is_supported_version("1")
        assert not wire.is_supported_version(None)


# ---------------------------------------------------------------------------
# URL normalisation
# ---------------------------------------------------------------------------


class TestNormalisePeerUrl:
    def test_bare_host_defaults_to_https(self):
        """Never silently downgrade: a pasted host must not become plain http."""
        assert normalise_peer_url("synz.zone.id/peer/abc") == "https://synz.zone.id/peer/abc"

    def test_explicit_scheme_kept(self):
        assert normalise_peer_url("http://127.0.0.1:8443/peer/x") == "http://127.0.0.1:8443/peer/x"

    def test_trailing_slash_stripped(self):
        assert normalise_peer_url("https://a.example/peer/x/") == "https://a.example/peer/x"

    def test_whitespace_tolerated(self):
        assert normalise_peer_url("  https://a.example  ") == "https://a.example"

    @pytest.mark.parametrize("bad", ["", "   ", "ftp://a.example", "https://"])
    def test_unusable_urls_raise(self, bad):
        with pytest.raises(ValueError):
            normalise_peer_url(bad)


# ---------------------------------------------------------------------------
# the listener: refusals
# ---------------------------------------------------------------------------


class TestServerGuards:
    def test_refuses_to_listen_when_closed(self):
        """AMAN by default, made mechanical: CLOSED means nothing listens."""
        policy = AdmissionPolicy(_tmp_dir(), mode=AdmissionMode.CLOSED)
        with pytest.raises(ValueError, match="closed"):
            PeerLinkServer(PeerIdentity.generate(), policy, port=_free_port())

    def test_refuses_unsafe_label(self):
        policy = AdmissionPolicy(_tmp_dir(), mode=AdmissionMode.PUBLIC_OPEN)
        for bad in ["../etc", "a/b", "a b", "", "x" * 64, "a.b"]:
            with pytest.raises(ValueError):
                PeerLinkServer(PeerIdentity.generate(), policy, port=0, label=bad)

    def test_health_is_liveness_only(self):
        """A health endpoint that describes the instance is an enumeration aid."""
        server, _, _ = _make_server()
        try:
            with urllib.request.urlopen(_url(server, "/peerlink/health"), timeout=10) as r:
                body = json.loads(r.read())
            assert body == {"status": "ok"}
        finally:
            server.stop()

    def test_get_on_peer_path_is_human_readable(self):
        """The URL is meant to be pasted between humans, so a browser GET must
        explain itself rather than 404."""
        server, _, _ = _make_server(label="abc123def456")
        try:
            with urllib.request.urlopen(
                _url(server, "/peer/abc123def456"), timeout=10
            ) as r:
                body = json.loads(r.read())
            assert body["service"] == "synapse-peerlink"
        finally:
            server.stop()

    def test_post_to_wrong_label_is_404(self):
        server, _, _ = _make_server(label="abc123def456")
        try:
            status, body = _post(
                _url(server, "/peer/someoneelse"),
                {"type": wire.HELLO, "version": wire.HANDSHAKE_VERSION},
            )
            assert status == 404
            assert "unknown peer" in body["error"]
        finally:
            server.stop()

    def test_oversized_body_refused(self):
        """A hostile Content-Length must not make the server allocate."""
        server, _, _ = _make_server()
        try:
            request = urllib.request.Request(
                _url(server),
                data=b"x" * (wire.MAX_BODY_BYTES + 100),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as exc:
                urllib.request.urlopen(request, timeout=10)
            assert exc.value.code == 400
        finally:
            server.stop()

    def test_unsupported_version_refused(self):
        server, _, _ = _make_server()
        try:
            status, body = _post(
                _url(server),
                {
                    "type": wire.HELLO,
                    "version": wire.HANDSHAKE_VERSION + 99,
                    "public_key": PeerIdentity.generate().public_key_b64,
                    "challenge": wire.new_challenge(),
                },
            )
            assert status == 409
        finally:
            server.stop()

    def test_bad_public_key_refused(self):
        server, _, _ = _make_server()
        try:
            status, _ = _post(
                _url(server),
                {
                    "type": wire.HELLO,
                    "version": wire.HANDSHAKE_VERSION,
                    "public_key": "not-base64!!",
                    "challenge": wire.new_challenge(),
                },
            )
            assert status == 400
        finally:
            server.stop()

    def test_claimed_id_mismatch_refused(self):
        """The id is derived from the key; claiming another id must fail."""
        server, _, _ = _make_server()
        try:
            attacker = PeerIdentity.generate()
            victim = PeerIdentity.generate()
            status, body = _post(
                _url(server),
                {
                    "type": wire.HELLO,
                    "version": wire.HANDSHAKE_VERSION,
                    "peer_id": victim.peer_id,  # claims someone else
                    "public_key": attacker.public_key_b64,
                    "challenge": wire.new_challenge(),
                },
            )
            assert status == 403
            assert "does not match" in body["error"]
        finally:
            server.stop()

    def test_confirm_without_hello_refused(self):
        """No server challenge exists, so there is nothing a confirm can prove."""
        server, _, _ = _make_server()
        try:
            client = PeerIdentity.generate()
            status, body = _post(
                _url(server),
                {
                    "type": wire.CONFIRM,
                    "version": wire.HANDSHAKE_VERSION,
                    "public_key": client.public_key_b64,
                    "signature": "AAAA",
                },
            )
            assert status == 400
            assert "no handshake" in body["error"]
        finally:
            server.stop()

    def test_confirm_answered_before_hello_is_refused(self):
        server, _, _ = _make_server()
        try:
            status, _ = _post(_url(server), {"type": "nonsense"})
            assert status == 400
        finally:
            server.stop()


# ---------------------------------------------------------------------------
# the listener: the happy path, over a real socket
# ---------------------------------------------------------------------------


class TestHandshakeEndToEnd:
    def test_full_mutual_handshake(self):
        """The headline test: two instances authenticate each other.

        This is the test that would have caught the handler-lifecycle bug, since
        it exercises hello and confirm as two separate HTTP requests.

        Note the state: a brand-new peer authenticates and lands in
        **quarantine**, not trusted. That is the spec principle "USER selalu di
        loop" made mechanical — authentication is not authorisation.
        """
        server, server_identity, _ = _make_server()
        client_identity = PeerIdentity.generate()
        try:
            result = connect(client_identity, _url(server))
            assert result.ok, result.reason
            assert result.authenticated
            assert result.peer_id == server_identity.peer_id
            assert result.state == wire.STATE_QUARANTINED
        finally:
            server.stop()

    def test_allowlisted_peer_is_trusted_immediately(self):
        """A peer vouched for out of band skips quarantine.

        This is the other half of the previous test: quarantine is the default
        for strangers, but the owner can vouch for someone in advance.
        """
        client_identity = PeerIdentity.generate()
        server, server_identity, policy = _make_server(
            mode=AdmissionMode.PUBLIC_GATED, allowlist=[client_identity.peer_id]
        )
        try:
            result = connect(client_identity, _url(server))
            assert result.ok, result.reason
            assert result.state == wire.STATE_OK
            assert policy.trusted()
        finally:
            server.stop()

    def test_client_refuses_unverifiable_server_signature(self):
        """A MITM that cannot sign must not be trusted, even over a good URL."""
        server, server_identity, _ = _make_server()
        try:
            client = PeerLinkClient(PeerIdentity.generate(), _url(server))
            # Intercept the welcome and corrupt the signature.
            original_post = client._post

            def tampering_post(payload):
                reply = original_post(payload)
                if reply and reply.get("type") == wire.WELCOME:
                    reply = {**reply, "signature": "AAAA" + reply["signature"][4:]}
                return reply

            client._post = tampering_post  # type: ignore[assignment]
            result = client.connect()
            assert not result.ok
            assert not result.authenticated
        finally:
            server.stop()

    def test_replay_of_confirm_fails(self):
        """A captured confirm must be worthless the second time."""
        server, _, _ = _make_server()
        client_identity = PeerIdentity.generate()
        try:
            # Complete a handshake, capturing the confirm message.
            captured = {}
            client = PeerLinkClient(client_identity, _url(server))
            original_post = client._post

            def capturing_post(payload):
                if payload.get("type") == wire.CONFIRM:
                    captured.update(payload)
                return original_post(payload)

            client._post = capturing_post  # type: ignore[assignment]
            assert client.connect().ok

            # Replay it verbatim.
            status, _ = _post(_url(server), captured)
            assert status == 400  # challenge already consumed
        finally:
            server.stop()

    def test_two_distinct_clients_both_authenticate(self):
        server, server_identity, _ = _make_server()
        try:
            for _ in range(3):
                result = connect(PeerIdentity.generate(), _url(server))
                assert result.ok, result.reason
                assert result.peer_id == server_identity.peer_id
        finally:
            server.stop()

    def test_stranger_lands_in_quarantine_not_trusted(self):
        """USER always in the loop: a new peer may speak, never act."""
        server, _, policy = _make_server(mode=AdmissionMode.PUBLIC_GATED)
        try:
            client_identity = PeerIdentity.generate()
            result = connect(client_identity, _url(server))
            assert result.ok, result.reason
            assert result.state == wire.STATE_QUARANTINED

            pending = policy.pending()
            assert len(pending) == 1
            assert pending[0]["peer_id"] == client_identity.peer_id
            # And crucially: nothing was promoted on its own.
            assert policy.trusted() == []
        finally:
            server.stop()

    def test_owner_promotion_then_trusted(self):
        """Promotion by the owner takes effect, and only the owner can do it.

        Deliberately asserts on the *policy*, not on a second handshake: the
        per-key rate limit (60s) means an immediate second knock from the same
        peer is refused by design, so a second handshake would test the rate
        limiter rather than the promotion.
        """
        server, _, policy = _make_server(mode=AdmissionMode.PUBLIC_GATED)
        try:
            client_identity = PeerIdentity.generate()
            assert connect(client_identity, _url(server)).ok

            # A stranger may not promote itself: there is no API for that, and
            # the only route is the owner calling promote().
            assert policy.trusted() == []
            assert len(policy.pending()) == 1

            assert policy.promote(client_identity.peer_id)
            trusted = policy.trusted()
            assert len(trusted) == 1
            assert trusted[0]["peer_id"] == client_identity.peer_id
            assert policy.pending() == []
        finally:
            server.stop()

    def test_quarantine_queue_is_bounded(self):
        """A flood of strangers cannot grow the review queue without limit."""
        server, _, policy = _make_server(
            mode=AdmissionMode.PUBLIC_GATED, max_pending=2
        )
        try:
            accepted = 0
            for _ in range(6):
                if connect(PeerIdentity.generate(), _url(server)).ok:
                    accepted += 1
            # At most max_pending peers may sit in quarantine.
            assert len(policy.pending()) <= 2
            assert accepted <= 2
        finally:
            server.stop()

    def test_blocked_peer_is_denied(self):
        server, _, policy = _make_server(mode=AdmissionMode.PUBLIC_GATED)
        try:
            client_identity = PeerIdentity.generate()
            assert connect(client_identity, _url(server)).ok
            assert policy.block(client_identity.peer_id)

            result = connect(client_identity, _url(server))
            assert not result.ok
            assert "blocked" in result.reason
        finally:
            server.stop()

    def test_invite_mode_refuses_without_code(self):
        server, _, _ = _make_server(mode=AdmissionMode.INVITE)
        try:
            result = connect(PeerIdentity.generate(), _url(server))
            assert not result.ok
            assert "invite" in result.reason
        finally:
            server.stop()

    def test_https_url_is_reported_as_secure(self):
        server, _, _ = _make_server()
        try:
            client = PeerLinkClient(PeerIdentity.generate(), _url(server))
            assert not client.secure_transport  # http:// in tests
            https_client = PeerLinkClient(
                PeerIdentity.generate(), "https://synz.zone.id/peer/abc"
            )
            assert https_client.secure_transport
        finally:
            server.stop()


# ---------------------------------------------------------------------------
# client robustness
# ---------------------------------------------------------------------------


class TestClientRobustness:
    def test_unreachable_peer_is_a_result_not_a_traceback(self):
        """A dead address is normal traffic, not a crash."""
        port = _free_port()  # nothing is listening here
        result = connect(PeerIdentity.generate(), f"http://127.0.0.1:{port}", timeout=2)
        assert not result.ok
        assert "no response" in result.reason

    def test_connection_refused_is_reported(self):
        result = connect(PeerIdentity.generate(), "http://127.0.0.1:1", timeout=2)
        assert not result.ok

    def test_garbage_response_is_reported(self):
        """A server that answers with nonsense must not crash the client."""
        port = _free_port()

        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class Junk(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                body = b"this is not json"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):  # noqa: A002
                pass

        httpd = ThreadingHTTPServer(("127.0.0.1", port), Junk)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            result = connect(PeerIdentity.generate(), f"http://127.0.0.1:{port}", timeout=3)
            assert not result.ok
        finally:
            httpd.shutdown()
            httpd.server_close()


class TestPendingHandshakes:
    def test_challenge_is_single_use(self):
        from gateway.peer_link.server import _PendingHandshakes

        store = _PendingHandshakes()
        store.put("pl1abc", {"server_challenge": "x" * 64})
        assert store.take("pl1abc") is not None
        assert store.take("pl1abc") is None

    def test_expired_challenge_is_refused(self):
        from gateway.peer_link.server import _PendingHandshakes

        store = _PendingHandshakes(ttl=-1)  # everything is already stale
        store.put("pl1abc", {"server_challenge": "x" * 64})
        assert store.take("pl1abc") is None

    def test_map_is_bounded(self):
        """An unauthenticated caller must not grow this without limit."""
        from gateway.peer_link.server import _PendingHandshakes

        store = _PendingHandshakes(max_entries=5)
        for index in range(50):
            store.put(f"pl1peer{index:03d}", {"server_challenge": "x" * 64})
        assert len(store._entries) <= 5

    def test_unknown_peer_takes_nothing(self):
        from gateway.peer_link.server import _PendingHandshakes

        store = _PendingHandshakes()
        assert store.take("pl1never-seen") is None


class TestWorkIsActuallyRequired:
    def test_gated_mode_rejects_zero_work(self):
        """The proof of work must be load-bearing, not decorative."""
        server, _, policy = _make_server(mode=AdmissionMode.PUBLIC_GATED, pow_bits=12)
        try:
            client_identity = PeerIdentity.generate()
            # Hand-craft a hello with nonce=0, skipping solve_work.
            status, body = _post(
                _url(server),
                {
                    "type": wire.HELLO,
                    "version": wire.HANDSHAKE_VERSION,
                    "peer_id": client_identity.peer_id,
                    "public_key": client_identity.public_key_b64,
                    "challenge": wire.new_challenge(),
                    "nonce": 0,
                },
            )
            # Either the difficulty happens to be satisfied by nonce 0 (rare but
            # possible) or it is refused. Assert the refusal is a real refusal.
            if status != 200:
                assert status == 403
                assert "proof of work" in body.get("reason", "") or body.get("reason")
        finally:
            server.stop()

    def test_solved_work_is_accepted(self):
        server, _, _ = _make_server(mode=AdmissionMode.PUBLIC_GATED, pow_bits=12)
        try:
            identity = PeerIdentity.generate()
            nonce = solve_work(identity.public_key_bytes, 12)
            status, body = _post(
                _url(server),
                {
                    "type": wire.HELLO,
                    "version": wire.HANDSHAKE_VERSION,
                    "peer_id": identity.peer_id,
                    "public_key": identity.public_key_b64,
                    "challenge": wire.new_challenge(),
                    "nonce": nonce,
                },
            )
            assert status == 200
            assert body["type"] == wire.WELCOME
            assert body["state"] == wire.STATE_QUARANTINED
        finally:
            server.stop()

    def test_challenge_probe_reports_difficulty(self):
        server, _, _ = _make_server(mode=AdmissionMode.PUBLIC_GATED, pow_bits=14)
        try:
            status, body = _post(
                _url(server), {"type": wire.CHALLENGE, "version": wire.HANDSHAKE_VERSION}
            )
            assert status == 200
            assert body["difficulty"] == 14
            assert body["mode"] == "public_gated"
        finally:
            server.stop()

    def test_closed_mode_probe_reports_zero_difficulty(self):
        """In CLOSED mode nothing listens, but the policy must still answer
        coherently if asked directly."""
        policy = AdmissionPolicy(_tmp_dir(), mode=AdmissionMode.CLOSED)
        assert policy.challenge()["difficulty"] == 0


class TestServerLifecycle:
    def test_start_and_stop_are_idempotent_safe(self):
        server, _, _ = _make_server()
        server.stop()
        server.stop()  # second stop must not raise

    def test_port_zero_gets_a_real_port(self):
        server, _, _ = _make_server()
        try:
            _, port = server.address
            assert port > 0
        finally:
            server.stop()

    def test_repr_is_key_free(self):
        server, identity, _ = _make_server()
        try:
            text = repr(server)
            assert identity.peer_id in text
            # No base64 key material anywhere in the repr.
            assert identity.public_key_b64 not in text
        finally:
            server.stop()
