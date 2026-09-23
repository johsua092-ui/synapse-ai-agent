"""Tests for ``synapse peerlink serve`` and ``connect``.

The unit tests in ``test_peer_link_server.py`` prove the protocol works. These
prove the *commands* work — that ``serve`` actually refuses to listen in CLOSED
mode, that it binds the label (not the hostname) in path mode, and that
``connect`` reports a refusal as a clean message rather than a traceback.

The label/hostname distinction is not hypothetical: an early version passed
``own_hostname()`` to the server, which in path mode returns the shared base
domain. The server rejected it as an unsafe label and ``serve`` died before it
could bind — while the CLOSED-mode refusal stayed hidden behind the same bug.
That is why the first test here asserts on the *refusal*, not on success.
"""

from __future__ import annotations

import argparse
import json
import socket

import pytest

from synapse_cli.subcommands import peerlink


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def home(tmp_path, monkeypatch):
    """An isolated SYNAPSE_HOME. Never the real ``~/.synapse``."""
    monkeypatch.setattr(peerlink, "_data_dir", lambda: tmp_path / "peer_link")
    return tmp_path


def _ns(**kwargs) -> argparse.Namespace:
    """A Namespace with the defaults the CLI would supply."""
    base = {"json": False, "peerlink_action": None}
    base.update(kwargs)
    return argparse.Namespace(**base)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


# ---------------------------------------------------------------------------
# serve
# ---------------------------------------------------------------------------


class TestServeRefusesWhenClosed:
    def test_closed_mode_refuses_to_bind(self, home):
        """The safety default must survive all the way to the CLI.

        If this ever passes while the mode is closed, the feature has silently
        become ON by default.
        """
        with pytest.raises(Exception) as exc:
            peerlink._cmd_serve(_ns(host="127.0.0.1", port=_free_port()))
        assert "closed" in str(exc.value).lower()

    def test_error_does_not_leak_a_traceback(self, home, capsys):
        """cmd_peerlink turns it into a message + exit 1."""
        code = peerlink.cmd_peerlink(
            _ns(peerlink_action="serve", host="127.0.0.1", port=_free_port())
        )
        assert code == 1
        err = capsys.readouterr().err
        assert "closed" in err.lower()
        assert "Traceback" not in err


class TestServeUsesLabelNotHostname:
    def test_path_mode_binds_the_label(self, home, monkeypatch):
        """In path mode own_hostname() is the shared base domain.

        Binding that as a label is wrong (and was a real bug): the label is the
        only part of ``/peer/<label>`` that belongs to this instance.
        """
        peerlink._cmd_mode(_ns(mode_value="invite", json=False))

        captured = {}

        class FakeServer:
            def __init__(self, identity, policy, *, host, port, label):
                captured["label"] = label
                captured["host"] = host
                captured["port"] = port

            @property
            def address(self):
                return (captured["host"], captured["port"])

            def serve_forever(self):
                raise KeyboardInterrupt  # stop immediately, we only bind

            def stop(self):
                pass

        import gateway.peer_link.server as server_mod

        monkeypatch.setattr(server_mod, "PeerLinkServer", FakeServer)
        monkeypatch.setattr(
            peerlink, "_default_base_domain", lambda: "synz.zone.id"
        )
        monkeypatch.setattr(peerlink, "_default_address_mode", lambda: "path")

        assert peerlink._cmd_serve(
            _ns(host="127.0.0.1", port=_free_port(), base_domain=None,
                address_mode=None)
        ) == 0

        label = captured["label"]
        assert label and label != "synz.zone.id"
        from gateway.peer_link.endpoint import validate_label

        assert validate_label(label), label


class TestServeOutput:
    def test_prints_the_public_url_and_a_warning(self, home, monkeypatch, capsys):
        peerlink._cmd_mode(_ns(mode_value="invite", json=False))
        monkeypatch.setattr(peerlink, "_default_base_domain", lambda: "synz.zone.id")
        monkeypatch.setattr(peerlink, "_default_address_mode", lambda: "path")

        class FakeServer:
            def __init__(self, *a, **kw):
                pass

            @property
            def address(self):
                return ("127.0.0.1", 18999)

            def serve_forever(self):
                raise KeyboardInterrupt

            def stop(self):
                pass

        import gateway.peer_link.server as server_mod

        monkeypatch.setattr(server_mod, "PeerLinkServer", FakeServer)
        peerlink._cmd_serve(
            _ns(host="127.0.0.1", port=18999, base_domain=None, address_mode=None)
        )
        out = capsys.readouterr().out
        assert "https://synz.zone.id/peer/" in out
        # Plain HTTP listener behind an HTTPS name must say so.
        assert "plain HTTP" in out


# ---------------------------------------------------------------------------
# connect
# ---------------------------------------------------------------------------


class TestConnect:
    def test_unreachable_peer_exits_nonzero_without_traceback(self, home, capsys):
        code = peerlink._cmd_connect(
            _ns(url=f"http://127.0.0.1:{_free_port()}", timeout=2)
        )
        assert code == 1
        out = capsys.readouterr().out
        assert "Could not link" in out
        assert "Traceback" not in out

    @pytest.mark.parametrize("bad", ["", "   ", "ftp://x", "https://"])
    def test_unusable_url_is_a_usage_error(self, home, bad, capsys):
        assert peerlink._cmd_connect(_ns(url=bad, timeout=2)) == 2
        assert "peerlink:" in capsys.readouterr().err

    def test_json_mode_reports_ok_false(self, home, capsys):
        code = peerlink._cmd_connect(
            _ns(url=f"http://127.0.0.1:{_free_port()}", timeout=2, json=True)
        )
        assert code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is False
        assert payload["authenticated"] is False

    def test_bare_host_is_upgraded_to_https(self, home, capsys):
        """A pasted host must not be silently dialled over plain HTTP."""
        code = peerlink._cmd_connect(
            _ns(url="synz.zone.id/peer/abc123def456", timeout=2, json=True)
        )
        assert code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["url"].startswith("https://")


# ---------------------------------------------------------------------------
# the command is actually wired up
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_actions_include_serve_and_connect(self):
        assert "serve" in peerlink._ACTIONS
        assert "connect" in peerlink._ACTIONS

    def test_parser_exposes_both(self):
        import argparse

        top = argparse.ArgumentParser()
        subs = top.add_subparsers(dest="cmd")
        peerlink.build_peerlink_parser(subs)
        args = top.parse_args(["peerlink", "connect", "https://x.example/peer/y"])
        assert args.peerlink_action == "connect"
        assert args.url == "https://x.example/peer/y"

    def test_serve_parser_takes_host_and_port(self):
        import argparse

        top = argparse.ArgumentParser()
        subs = top.add_subparsers(dest="cmd")
        peerlink.build_peerlink_parser(subs)
        args = top.parse_args(
            ["peerlink", "serve", "--host", "127.0.0.1", "--port", "9000"]
        )
        assert args.peerlink_action == "serve"
        assert args.host == "127.0.0.1"
        assert args.port == 9000


# ---------------------------------------------------------------------------
# endpoint.own_label
# ---------------------------------------------------------------------------


class TestOwnLabel:
    def test_path_mode_label_differs_from_hostname(self, tmp_path):
        from gateway.peer_link.endpoint import EndpointRegistry, validate_label

        registry = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        label = registry.own_label(create=True)
        assert label and validate_label(label)
        # The whole point: hostname is shared, label is ours.
        assert registry.own_hostname(create=False) == "synz.zone.id"
        assert label != "synz.zone.id"

    def test_create_false_never_mints(self, tmp_path):
        from gateway.peer_link.endpoint import EndpointRegistry

        registry = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        assert registry.own_label(create=False) is None

    def test_own_label_is_stable_across_calls(self, tmp_path):
        from gateway.peer_link.endpoint import EndpointRegistry

        registry = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        first = registry.own_label(create=True)
        assert registry.own_label(create=True) == first

    def test_rotate_changes_the_label(self, tmp_path):
        from gateway.peer_link.endpoint import EndpointRegistry

        registry = EndpointRegistry(tmp_path, "synz.zone.id", "path")
        before = registry.own_label(create=True)
        registry.rotate()
        assert registry.own_label(create=False) != before
