"""Tests for the terminal.backend validation on the dashboard save path.

The flat settings form must agree with the dedicated picker whitelist
(``_TERMINAL_BACKEND_NAMES`` deliberately omits ``vercel_sandbox``) and with
the setup gate that only enables ``singularity`` on Linux.
"""

from __future__ import annotations

import sys

import pytest

from synapse_cli import web_server


def _reject(value, platform):
    with pytest.raises(ValueError):
        web_server.validate_terminal_backend(value, platform=platform)


def test_validate_terminal_backend_rejects_vercel_and_nonlinux_singularity():
    _reject("vercel_sandbox", platform="win32")
    _reject("singularity", platform="win32")
    _reject("singularity", platform="darwin")
    _reject("vercel-sandbox", platform="win32")
    _reject("not-a-backend", platform="linux")
    assert web_server.validate_terminal_backend("local", platform="win32") == "local"
    assert web_server.validate_terminal_backend("ssh", platform="win32") == "ssh"
    assert web_server.validate_terminal_backend("ssh", platform="darwin") == "ssh"
    assert web_server.validate_terminal_backend("singularity", platform="linux") == "singularity"


def test_flat_settings_options_match_the_picker_whitelist():
    options = web_server.CONFIG_SCHEMA["terminal.backend"]["options"]
    assert "vercel_sandbox" not in options
    assert set(options) == web_server._TERMINAL_BACKEND_NAMES - (
        {"singularity"} if not sys.platform.startswith("linux") else set()
    )
    assert options == sorted(options)
    for name in options:
        assert web_server.validate_terminal_backend(name, platform=sys.platform) == name


def test_flat_options_retain_configured_legacy_backend():
    """I1: a legacy on-disk backend (vercel_sandbox) must survive the flat form
    round-trip — appended to the options so the select keeps it, never coerced
    to a sorted option by the browser on the next save."""
    options = web_server._terminal_backend_options(
        {"terminal": {"backend": "vercel_sandbox"}}
    )
    assert "vercel_sandbox" in options


def test_flat_options_without_config_omit_legacy_backend():
    options = web_server._terminal_backend_options(None)
    assert "vercel_sandbox" not in options


def test_flat_options_linux_omit_singularity_when_not_linux():
    saved = sys.platform
    try:
        sys.platform = "darwin"
        options = web_server._terminal_backend_options(None)
    finally:
        sys.platform = saved
    assert "singularity" not in options


def test_put_save_validation_rejects_changing_backend_to_unknown():
    from fastapi import HTTPException

    _validate = web_server._validate_terminal_section
    merged = {"terminal": {"backend": "vercel_sandbox"}}
    with pytest.raises(HTTPException) as excinfo:
        _validate(
            merged,
            existing={"terminal": {"backend": "local"}},
            incoming={"terminal": {"backend": "vercel_sandbox"}},
        )
    detail = str(excinfo.value.detail)
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


def test_put_save_roundtrips_legacy_backend_without_rewrite():
    """I1: saving with a legacy on-disk backend carried in the payload must
    pass (the change-guard sees normalized values as equal) and must NOT be
    diverted or rewritten — the flat form round-trips it unchanged."""
    _validate = web_server._validate_terminal_section
    existing = {"terminal": {"backend": "vercel_sandbox"}, "approvals": {"mode": "suggest"}}
    incoming = {"terminal": {"backend": "vercel_sandbox"}, "approvals": {"mode": "suggest"}}
    merged = {"terminal": {"backend": "vercel_sandbox"}, "approvals": {"mode": "suggest"}}
    _validate(merged, existing=existing, incoming=incoming)
    assert merged["terminal"]["backend"] == "vercel_sandbox"


def test_put_save_normalizes_change_back_onto_merged_document():
    """M3: a changed backend is normalized (stripped/lower-cased) and that
    canonical form is written back onto the merged document, so the canonical
    form persists instead of the raw payload."""
    _validate = web_server._validate_terminal_section
    existing = {"terminal": {"backend": "local"}}
    incoming = {"terminal": {"backend": " SSH "}}
    merged = {"terminal": {"backend": " SSH "}}
    _validate(merged, existing=existing, incoming=incoming)
    assert merged["terminal"]["backend"] == "ssh"
