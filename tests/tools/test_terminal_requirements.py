import importlib
import logging

import pytest


terminal_tool_module = importlib.import_module("tools.terminal_tool")


def _clear_terminal_env(monkeypatch):
    """Remove terminal env vars that could affect requirements checks."""
    keys = [
        "TERMINAL_ENV",
        "TERMINAL_CONTAINER_CPU",
        "TERMINAL_CONTAINER_DISK",
        "TERMINAL_CONTAINER_MEMORY",
        "TERMINAL_DOCKER_FORWARD_ENV",
        "TERMINAL_DOCKER_VOLUMES",
        "TERMINAL_LIFETIME_SECONDS",
        "TERMINAL_MODAL_MODE",
        "TERMINAL_SSH_HOST",
        "TERMINAL_SSH_PORT",
        "TERMINAL_SSH_USER",
        "TERMINAL_TIMEOUT",
        "TERMINAL_VERCEL_RUNTIME",
        "MODAL_TOKEN_ID",
        "MODAL_TOKEN_SECRET",
        "VERCEL_OIDC_TOKEN",
        "VERCEL_TOKEN",
        "VERCEL_PROJECT_ID",
        "VERCEL_TEAM_ID",
        "HOME",
        "USERPROFILE",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    # Default: no Nous subscription — patch both the terminal_tool local
    # binding and tool_backend_helpers (used by resolve_modal_backend_state).
    monkeypatch.setattr(terminal_tool_module, "managed_nous_tools_enabled", lambda: False)
    import tools.tool_backend_helpers as _tbh
    monkeypatch.setattr(_tbh, "managed_nous_tools_enabled", lambda: False)


def test_local_terminal_requirements(monkeypatch, caplog):
    """Local backend uses Synapse' own LocalEnvironment wrapper."""
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "local")

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is True
    assert "Terminal requirements check failed" not in caplog.text


def test_unknown_terminal_env_falls_back_to_local(monkeypatch, caplog):
    """An unrecognized TERMINAL_ENV must NOT strip the terminal/file tools.

    Historically an unknown value fell through to the ``else`` branch and made
    ``check_terminal_requirements()`` return False — which silently removed the
    entire ``terminal`` AND ``file`` toolsets (read_file/write_file/patch/
    search_files delegate to ``check_file_requirements`` → this function), so
    the agent reported "Tool terminal does not exist". A typo'd or stale value
    (e.g. bridged from config.yaml ``terminal.backend``) must degrade to the
    safe local backend with a clear warning instead of breaking core tools.
    """
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "unknown-backend")

    with caplog.at_level(logging.WARNING):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is True
    assert any(
        "unknown-backend" in record.getMessage() and "falling back" in record.getMessage()
        for record in caplog.records
    )


def test_unknown_terminal_env_keeps_core_tools_exposed(monkeypatch):
    """terminal/read_file/patch stay in get_tool_definitions under a bad env.

    This is the end-to-end symptom guard for the "Tool terminal does not
    exist" bug: an unrecognized TERMINAL_ENV must not empty the terminal+file
    toolsets (they route through check_terminal_requirements).
    """
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "unknown-backend")
    import logging as _logging

    _logging.disable(_logging.CRITICAL)
    try:
        from model_tools import get_tool_definitions

        defs = get_tool_definitions(
            enabled_toolsets=None, disabled_toolsets=None, quiet_mode=True
        )
    finally:
        _logging.disable(_logging.NOTSET)
    names = {d["function"]["name"] for d in defs}

    for tool in ("terminal", "read_file", "write_file", "patch", "search_files"):
        assert tool in names, f"{tool} was stripped under unknown TERMINAL_ENV"


def test_modal_backend_managed_mode_without_feature_flag_logs_clear_error(monkeypatch, caplog, tmp_path):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "modal")
    monkeypatch.setenv("TERMINAL_MODAL_MODE", "managed")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(terminal_tool_module, "is_managed_tool_gateway_ready", lambda _vendor: False)

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is False
    assert any(
        "Nous Tool Gateway access is not currently available" in record.getMessage()
        for record in caplog.records
    )


def test_vercel_backend_without_sdk_logs_specific_error(monkeypatch, caplog):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: None)

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is False
    assert any(
        "vercel is required for the Vercel Sandbox terminal backend" in record.getMessage()
        for record in caplog.records
    )


def test_vercel_backend_without_auth_logs_specific_error(monkeypatch, caplog):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is False
    assert any(
        "no supported auth configuration was found" in record.getMessage()
        for record in caplog.records
    )


def test_vercel_backend_accepts_oidc_auth(monkeypatch):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc-token")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    assert terminal_tool_module.check_terminal_requirements() is True


def test_vercel_backend_accepts_token_tuple_auth(monkeypatch):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setenv("VERCEL_TOKEN", "token")
    monkeypatch.setenv("VERCEL_PROJECT_ID", "project")
    monkeypatch.setenv("VERCEL_TEAM_ID", "team")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    assert terminal_tool_module.check_terminal_requirements() is True


@pytest.mark.parametrize("runtime", ["node24", "node22", "python3.13"])
def test_vercel_backend_accepts_supported_runtimes(monkeypatch, runtime):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setenv("TERMINAL_VERCEL_RUNTIME", runtime)
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc-token")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    assert terminal_tool_module.check_terminal_requirements() is True


def test_vercel_backend_accepts_blank_runtime(monkeypatch):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setenv("TERMINAL_VERCEL_RUNTIME", "   ")
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc-token")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    assert terminal_tool_module.check_terminal_requirements() is True


def test_vercel_backend_rejects_unsupported_runtime(monkeypatch, caplog):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setenv("TERMINAL_VERCEL_RUNTIME", "node20")
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc-token")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is False
    assert any(
        "Vercel Sandbox runtime 'node20' is not supported" in record.getMessage()
        and "node24, node22, python3.13" in record.getMessage()
        for record in caplog.records
    )


def test_vercel_backend_rejects_nondefault_disk(monkeypatch, caplog):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setenv("TERMINAL_CONTAINER_DISK", "8192")
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc-token")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is False
    assert any(
        "does not support custom TERMINAL_CONTAINER_DISK=8192" in record.getMessage()
        for record in caplog.records
    )


def test_vercel_backend_rejects_malformed_disk_without_raising(monkeypatch, caplog):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setenv("TERMINAL_CONTAINER_DISK", "large")
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc-token")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is False
    assert any(
        "Invalid value for TERMINAL_CONTAINER_DISK" in record.getMessage()
        for record in caplog.records
    )
