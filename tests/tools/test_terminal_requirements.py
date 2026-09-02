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


def test_docker_probe_timeout_is_not_usable(monkeypatch):
    import tools.environments.docker as docker_mod
    import subprocess as sp
    import synapse_cli._subprocess_compat as compat

    def fake_find_docker():
        return "/usr/bin/docker"

    def raising_probe(argv, **kw):
        raise sp.TimeoutExpired(argv[0], kw.get("timeout", 5))

    monkeypatch.setattr(docker_mod, "find_docker", fake_find_docker)
    monkeypatch.setattr(compat, "bounded_probe_run", raising_probe)
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "docker")
    assert terminal_tool_module.check_terminal_requirements() is False


def test_windows_local_without_bash_is_not_ready(monkeypatch):
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "local")

    def raising_find_bash():
        raise RuntimeError("Git Bash not found")

    import os as _real_os

    class FakeOs:
        name = "nt"

        def __getattr__(self, name):
            return getattr(_real_os, name)

    monkeypatch.setattr(terminal_tool_module, "os", FakeOs())

    import tools.environments.local as local_env

    monkeypatch.setattr(local_env, "_find_bash", raising_find_bash)
    assert terminal_tool_module.check_terminal_requirements() is False


def test_docker_probe_uses_bounded_probe_run(monkeypatch):
    import tools.environments.docker as docker_mod
    import synapse_cli._subprocess_compat as compat

    calls = {}

    def fake_find_docker():
        return "/usr/bin/docker"

    def fake_probe(argv, **kw):
        calls["probe"] = True
        calls["timeout"] = kw.get("timeout")
        return None

    monkeypatch.setattr(docker_mod, "find_docker", fake_find_docker)
    monkeypatch.setattr(compat, "bounded_probe_run", fake_probe)
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "docker")
    assert terminal_tool_module.check_terminal_requirements() is False
    assert calls.get("probe") is True
    assert calls.get("timeout") == 5


def test_local_terminal_requirements(monkeypatch, caplog):
    """Local backend uses Synapse' own LocalEnvironment wrapper."""
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "local")

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is True
    assert "Terminal requirements check failed" not in caplog.text


def test_terminal_config_default_timeout_is_600(monkeypatch):
    _clear_terminal_env(monkeypatch)
    config = terminal_tool_module._get_env_config()
    assert config["timeout"] == 600


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


def test_terminal_requirements_survive_env_config_exception(monkeypatch, caplog):
    """An unexpected exception in _get_env_config must NOT strip the tools.

    This is the "Tool does not exists" report from a Windows user after
    /update: check_terminal_requirements wraps everything in try/except and
    returned False on ANY exception from _get_env_config — silently removing
    the terminal AND file toolsets. Since the same exception re-fired on every
    requirements probe, retries never recovered ("10+ retry"). A transient or
    platform-specific config fault must expose the tools instead (real errors
    then surface at call time where the model can read and adapt).
    """
    _clear_terminal_env(monkeypatch)

    def _boom():
        raise RuntimeError("simulated env-config fault")

    monkeypatch.setattr(terminal_tool_module, "_get_env_config", _boom)

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is True
    assert any(
        "Terminal requirements check failed" in record.getMessage()
        for record in caplog.records
    )


def test_sandbox_requirements_survive_env_config_exception(monkeypatch):
    """execute_code must stay exposed when _get_env_config raises.

    check_sandbox_requirements forwards to terminal_tool._get_env_config and
    returned False when it raised — which stripped execute_code alongside the
    terminal/file tools (the Windows user's report had terminal, patch AND
    execute_code all unavailable). A config-resolution fault is not a sandbox
    capability fault: expose the tool and let the real error surface at call
    time.
    """
    _clear_terminal_env(monkeypatch)

    def _boom():
        raise RuntimeError("simulated env-config fault")

    monkeypatch.setattr(terminal_tool_module, "_get_env_config", _boom)

    from tools.code_execution_tool import check_sandbox_requirements

    assert check_sandbox_requirements() is True


def test_config_exception_keeps_core_tools_exposed(monkeypatch):
    """terminal/read_file/patch/execute_code stay under a raising env-config."""
    _clear_terminal_env(monkeypatch)

    def _boom():
        raise RuntimeError("simulated env-config fault")

    monkeypatch.setattr(terminal_tool_module, "_get_env_config", _boom)

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

    for tool in ("terminal", "read_file", "patch", "execute_code"):
        assert tool in names, f"{tool} was stripped after env-config exception"


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


def test_vercel_backend_malformed_disk_exposes_tool_and_logs_reason(monkeypatch, caplog):
    """A malformed env value must not hide the terminal/file tools.

    Historically a bad TERMINAL_CONTAINER_DISK made _get_env_config raise a
    ValueError; the outer except returned False and silently stripped the whole
    terminal+file toolset ("Tool does not exist"). On a Windows machine after
    /update a single malformed bridged env value produced exactly that, plus a
    stripped execute_code (check_sandbox_requirements forwards to
    _get_env_config). Config-resolution faults log the real reason and keep
    the tools exposed, so the actual error surfaces at call time.
    """
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "vercel_sandbox")
    monkeypatch.setenv("TERMINAL_CONTAINER_DISK", "large")
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "oidc-token")
    monkeypatch.setattr(terminal_tool_module.importlib.util, "find_spec", lambda _name: object())

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is True
    assert any(
        "Invalid value for TERMINAL_CONTAINER_DISK" in record.getMessage()
        for record in caplog.records
    )
