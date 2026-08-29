"""Tests for the terminal.backend validation on the dashboard save path.

The flat settings form must agree with the dedicated picker whitelist
(``_TERMINAL_BACKEND_NAMES`` deliberately omits ``vercel_sandbox``) and with
the setup gate that only enables ``singularity`` on Linux.
"""

from __future__ import annotations

import sys

import pytest

from synapse_cli import web_server


def test_validate_terminal_backend_rejects_vercel_and_win_singularity():
    with pytest.raises(ValueError):
        web_server.validate_terminal_backend("vercel_sandbox", platform="win32")
    with pytest.raises(ValueError):
        web_server.validate_terminal_backend("singularity", platform="win32")
    with pytest.raises(ValueError):
        web_server.validate_terminal_backend("vercel-sandbox", platform="win32")
    with pytest.raises(ValueError):
        web_server.validate_terminal_backend("not-a-backend", platform="linux")
    assert web_server.validate_terminal_backend("local", platform="win32") == "local"
    assert web_server.validate_terminal_backend("ssh", platform="win32") == "ssh"
    assert web_server.validate_terminal_backend("singularity", platform="linux") == "singularity"


def test_flat_settings_options_match_the_picker_whitelist():
    options = web_server.CONFIG_SCHEMA["terminal.backend"]["options"]
    assert "vercel_sandbox" not in options
    assert set(options) == web_server._TERMINAL_BACKEND_NAMES - (
        {"singularity"} if sys.platform.startswith("win") else set()
    )
    assert options == sorted(options)
    for name in options:
        assert web_server.validate_terminal_backend(name, platform=sys.platform) == name


def test_put_save_validation_rejects_changing_backend_to_unknown():
    _validate = web_server._validate_terminal_section
    merged = {"terminal": {"backend": "vercel_sandbox"}}
    with pytest.raises(Exception) as excinfo:
        _validate(
            merged,
            existing={"terminal": {"backend": "local"}},
            incoming={"terminal": {"backend": "vercel_sandbox"}},
        )
    detail = str(excinfo.value)
    assert "terminal.backend" in detail
    assert "local" in detail


def test_put_save_legacy_ondisk_backend_does_not_block_unrelated_save():
    _validate = web_server._validate_terminal_section
    existing = {"terminal": {"backend": "vercel_sandbox"}, "approvals": {"mode": "suggest"}}
    incoming = {"approvals": {"mode": "suggest"}}
    merged = {"terminal": {"backend": "vercel_sandbox"}, "approvals": {"mode": "suggest"}}
    _validate(merged, existing=existing, incoming=incoming)


def test_put_save_passes_when_incoming_backend_equals_existing():
    _validate = web_server._validate_terminal_section
    existing = {"terminal": {"backend": "vercel_sandbox"}}
    incoming = {"terminal": {"backend": "vercel_sandbox"}}
    merged = {"terminal": {"backend": "vercel_sandbox"}}
    _validate(merged, existing=existing, incoming=incoming)