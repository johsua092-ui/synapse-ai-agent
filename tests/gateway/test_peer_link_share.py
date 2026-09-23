"""Tests for Peer Link share links and QR rendering.

Two behaviours are covered, both of which were *missing* before this change:

1. ``connect`` never sent the invite code, so ``mode invite`` — the recommended
   mode — was impossible to complete from the CLI. A share link carries the
   code, and ``connect`` must both extract it and put it in the handshake.
2. Nothing could render a QR, so a code had to be typed by hand.

The share-link tests are deliberately network-free: they assert the *encoding*
contract. The end-to-end path (link in, ``authenticated: True`` out) is proven
separately against a real listener.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

from gateway.peer_link.client import (  # noqa: E402
    build_share_link,
    split_share_link,
)
from gateway.peer_link.qr import qr_available, render_qr  # noqa: E402


class TestShareLink:
    """``<url>#c=<code>`` — one string a human can paste or scan."""

    def test_round_trip(self):
        link = build_share_link("https://synz.zone.id/peer/abc", "ABCD2345")
        assert link == "https://synz.zone.id/peer/abc#c=ABCD2345"
        url, code = split_share_link(link)
        assert url == "https://synz.zone.id/peer/abc"
        assert code == "ABCD2345"

    def test_code_rides_in_the_fragment_not_the_query(self):
        """The fragment is never sent to the server; a query string would be
        logged. This is a privacy property, not a style preference."""
        link = build_share_link("https://peer.example/p", "SECRET12")
        assert "#c=" in link
        assert "?" not in link

    def test_url_alone_yields_no_code(self):
        url, code = split_share_link("https://synz.zone.id/peer/abc")
        assert url == "https://synz.zone.id/peer/abc"
        assert code == ""

    def test_bare_code_is_recognised(self):
        url, code = split_share_link("ABCD2345")
        assert url == ""
        assert code == "ABCD2345"

    def test_empty_input_is_empty_output(self):
        assert split_share_link("") == ("", "")

    def test_build_without_code_is_just_the_url(self):
        assert build_share_link("https://x/p", "") == "https://x/p"

    def test_trailing_slash_is_normalised(self):
        assert build_share_link("https://x/p/", "AB") == "https://x/p#c=AB"

    def test_split_tolerates_the_long_form_key(self):
        url, code = split_share_link("https://x/p#code=ZZ99")
        assert code == "ZZ99"
        assert url == "https://x/p"


class TestQrRendering:
    """QR is optional: missing ``qrcode`` must degrade, never break."""

    def test_render_is_non_empty_when_available(self):
        if not qr_available():
            pytest.skip("qrcode not installed in this environment")
        art = render_qr("https://synz.zone.id/peer/abc#c=ABCD2345")
        assert art
        assert art.count("\n") > 10  # a real symbol, not a stub

    def test_empty_text_renders_empty(self):
        assert render_qr("") == ""

    def test_missing_qrcode_returns_empty_not_raises(self, monkeypatch):
        """A missing optional dep must not turn a working command into a crash."""
        import gateway.peer_link.qr as qr_mod

        monkeypatch.setattr(qr_mod, "_ensure_qrcode", lambda: False)
        assert qr_mod.render_qr("https://x/p") == ""


class TestCliWiring:
    """The flags exist and are documented, so `--help` matches the behaviour."""

    def _help(self, *args: str) -> str:
        proc = subprocess.run(
            [sys.executable, "-m", "synapse_cli.main", "peerlink", *args],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        return proc.stdout + proc.stderr

    def test_invite_exposes_qr_flag(self):
        assert "--qr" in self._help("invite", "--help")

    def test_connect_exposes_code_flag(self):
        assert "--code" in self._help("connect", "--help")
