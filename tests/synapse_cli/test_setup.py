"""Tests for setup.py configuration flows."""
import sys
import os
import json
import types
import subprocess as subprocess_module


from synapse_cli.config import load_config, save_config
from synapse_cli import setup as setup_mod
from synapse_cli.setup import setup_model_provider


def _maybe_keep_current_tts(question, choices):
    if question != "Select TTS provider:":
        return None
    assert choices[-1].startswith("Keep current (")
    return len(choices) - 1


def _clear_provider_env(monkeypatch):
    for key in (
        "NOUS_API_KEY",
        "OPENROUTER_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_API_KEY",
        "LLM_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)


def _clear_vercel_env(monkeypatch):
    for key in (
        "TERMINAL_VERCEL_RUNTIME",
        "VERCEL_OIDC_TOKEN",
        "VERCEL_TOKEN",
        "VERCEL_PROJECT_ID",
        "VERCEL_TEAM_ID",
    ):
        monkeypatch.delenv(key, raising=False)


def _stub_tts(monkeypatch):
    """Stub out TTS prompts so setup_model_provider doesn't block."""
    monkeypatch.setattr("synapse_cli.setup.prompt_choice", lambda q, c, d=0: (
        _maybe_keep_current_tts(q, c) if _maybe_keep_current_tts(q, c) is not None
        else d
    ))
    monkeypatch.setattr("synapse_cli.setup.prompt_yes_no", lambda *a, **kw: False)


def _write_model_config(tmp_path, provider, base_url="", model_name="test-model"):
    """Simulate what a _model_flow_* function writes to disk."""
    cfg = load_config()
    m = cfg.get("model")
    if not isinstance(m, dict):
        m = {"default": m} if m else {}
        cfg["model"] = m
    m["provider"] = provider
    if base_url:
        m["base_url"] = base_url
    if model_name:
        m["default"] = model_name
    save_config(cfg)


def test_setup_delegates_to_select_provider_and_model(tmp_path, monkeypatch):
    """setup_model_provider calls select_provider_and_model and syncs config."""
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    _clear_provider_env(monkeypatch)
    _stub_tts(monkeypatch)

    config = load_config()

    def fake_select():
        _write_model_config(tmp_path, "custom", "http://localhost:11434/v1", "qwen3.5:32b")

    monkeypatch.setattr("synapse_cli.main.select_provider_and_model", fake_select)

    setup_model_provider(config)
    save_config(config)

    reloaded = load_config()
    assert isinstance(reloaded["model"], dict)
    assert reloaded["model"]["provider"] == "custom"
    assert reloaded["model"]["base_url"] == "http://localhost:11434/v1"
    assert reloaded["model"]["default"] == "qwen3.5:32b"






def test_select_provider_and_model_warns_if_named_custom_provider_disappears(
    tmp_path, monkeypatch, capsys
):
    """If a saved custom provider is deleted mid-selection, show a warning instead of silently doing nothing."""
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    _clear_provider_env(monkeypatch)

    cfg = load_config()
    cfg["custom_providers"] = [{"name": "Local", "base_url": "http://localhost:8080/v1"}]
    save_config(cfg)

    def fake_prompt_provider_choice(choices, default=0):
        current = load_config()
        current["custom_providers"] = []
        save_config(current)
        return next(i for i, label in enumerate(choices) if label.startswith("Local (localhost:8080/v1)"))

    monkeypatch.setattr("synapse_cli.auth.resolve_provider", lambda provider: None)
    monkeypatch.setattr("synapse_cli.main._prompt_provider_choice", fake_prompt_provider_choice)
    monkeypatch.setattr(
        "synapse_cli.main._model_flow_named_custom",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("named custom flow should not run")),
    )

    from synapse_cli.main import select_provider_and_model

    select_provider_and_model()

    out = capsys.readouterr().out
    assert "selected saved custom provider is no longer available" in out








def test_modal_setup_persists_direct_mode_when_user_chooses_their_own_account(tmp_path, monkeypatch):
    monkeypatch.setattr("synapse_cli.setup.managed_nous_tools_enabled", lambda: True)
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)
    monkeypatch.delenv("MODAL_TOKEN_SECRET", raising=False)
    config = load_config()

    def fake_prompt_choice(question, choices, default=0):
        if question == "Select terminal backend:":
            return 2
        if question == "Select how Modal execution should be billed:":
            return 1
        raise AssertionError(f"Unexpected prompt_choice call: {question}")

    prompt_values = iter(["token-id", "token-secret", ""])

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", fake_prompt_choice)
    monkeypatch.setattr("synapse_cli.setup.prompt", lambda *args, **kwargs: next(prompt_values))
    monkeypatch.setattr("synapse_cli.setup._prompt_container_resources", lambda config: None)
    monkeypatch.setattr(
        "synapse_cli.setup.get_nous_subscription_features",
        lambda config: type("Features", (), {"nous_auth_present": True})(),
    )
    monkeypatch.setitem(
        sys.modules,
        "tools.managed_tool_gateway",
        types.SimpleNamespace(
            is_managed_tool_gateway_ready=lambda vendor: vendor == "modal",
            resolve_managed_tool_gateway=lambda vendor: None,
        ),
    )
    monkeypatch.setitem(sys.modules, "swe_rex", object())

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    assert config["terminal"]["backend"] == "modal"
    assert config["terminal"]["modal_mode"] == "direct"


# test_setup_slack_* moved to tests/gateway/test_slack_plugin_setup.py — the
# _setup_slack wizard migrated to the slack plugin's interactive_setup (#41112).


def test_vercel_setup_configures_access_token_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    _clear_vercel_env(monkeypatch)
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "old-oidc")
    monkeypatch.setitem(sys.modules, "vercel", types.ModuleType("vercel"))
    config = load_config()

    def fake_prompt_choice(question, choices, default=0):
        if question == "Select terminal backend:":
            return 5
        raise AssertionError(f"Unexpected prompt_choice call: {question}")

    prompt_values = iter(["python3.13", "yes", "2", "4096", "token", "project", "team"])

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", fake_prompt_choice)
    monkeypatch.setattr("synapse_cli.setup.prompt", lambda *args, **kwargs: next(prompt_values))

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    assert config["terminal"]["backend"] == "vercel_sandbox"
    assert config["terminal"]["vercel_runtime"] == "python3.13"
    assert config["terminal"]["container_disk"] == 51200
    assert os.environ["TERMINAL_VERCEL_RUNTIME"] == "python3.13"
    assert "VERCEL_OIDC_TOKEN" not in os.environ
    assert os.environ["VERCEL_TOKEN"] == "token"
    assert os.environ["VERCEL_PROJECT_ID"] == "project"
    assert os.environ["VERCEL_TEAM_ID"] == "team"


def test_vercel_setup_prefills_project_and_team_from_link_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    _clear_vercel_env(monkeypatch)
    project_root = tmp_path / "project"
    nested = project_root / "app" / "src"
    nested.mkdir(parents=True)
    vercel_dir = project_root / ".vercel"
    vercel_dir.mkdir()
    (vercel_dir / "project.json").write_text(
        json.dumps({"projectId": "linked-project", "orgId": "linked-team"}),
        encoding="utf-8",
    )
    monkeypatch.chdir(nested)
    monkeypatch.setitem(sys.modules, "vercel", types.ModuleType("vercel"))
    config = load_config()
    config["terminal"]["container_disk"] = 999

    def fake_prompt_choice(question, choices, default=0):
        if question == "Select terminal backend:":
            return 5
        raise AssertionError(f"Unexpected prompt_choice call: {question}")

    prompt_values = iter(["node24", "no", "1", "5120", "token", "", ""])
    defaults = {}

    def fake_prompt(message, default="", **kwargs):
        defaults[message] = default
        value = next(prompt_values)
        return value or default

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", fake_prompt_choice)
    monkeypatch.setattr("synapse_cli.setup.prompt", fake_prompt)

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    assert config["terminal"]["backend"] == "vercel_sandbox"
    assert config["terminal"]["container_persistent"] is False
    assert config["terminal"]["container_disk"] == 51200
    assert "VERCEL_OIDC_TOKEN" not in os.environ
    assert os.environ["VERCEL_TOKEN"] == "token"
    assert os.environ["VERCEL_PROJECT_ID"] == "linked-project"
    assert os.environ["VERCEL_TEAM_ID"] == "linked-team"
    assert defaults["    Vercel project ID"] == "linked-project"
    assert defaults["    Vercel team ID"] == "linked-team"


def test_reconcile_env_only_terminal_env_removes_stale_backend(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("TERMINAL_ENV=vercel_sandbox\n", encoding="utf-8")

    assert setup_mod.reconcile_env_only_terminal_env() is True
    assert "TERMINAL_ENV=vercel_sandbox" not in env_path.read_text(encoding="utf-8")


def test_reconcile_env_only_terminal_env_keeps_config_driven_backend(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("TERMINAL_ENV=ssh\n", encoding="utf-8")
    cfg = load_config()
    cfg.setdefault("terminal", {})["backend"] = "ssh"
    save_config(cfg)

    assert setup_mod.reconcile_env_only_terminal_env() is False
    assert "TERMINAL_ENV=ssh" in env_path.read_text(encoding="utf-8")


def test_reconcile_env_only_terminal_env_preserves_local(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("TERMINAL_ENV=local\n", encoding="utf-8")

    assert setup_mod.reconcile_env_only_terminal_env() is False
    assert "TERMINAL_ENV=local" in env_path.read_text(encoding="utf-8")


def test_keep_current_reconciles_stale_env_only_backend(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    env_path = tmp_path / ".env"
    env_path.write_text("TERMINAL_ENV=vercel_sandbox\n", encoding="utf-8")
    config = load_config()

    def keep_current(question, choices, default=0):
        return next(i for i, c in enumerate(choices) if str(c).startswith("Keep current"))

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", keep_current)

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    assert "TERMINAL_ENV=vercel_sandbox" not in env_path.read_text(encoding="utf-8")


def test_sanitize_backend_for_write_allows_real_backends():
    from synapse_cli.setup import _sanitize_backend_for_write

    assert _sanitize_backend_for_write("docker") == "docker"
    assert _sanitize_backend_for_write("vercel_sandbox") == "vercel_sandbox"
    assert _sanitize_backend_for_write("local") == "local"
    assert _sanitize_backend_for_write("singularity") == "singularity"


def test_sanitize_backend_for_write_rejects_unknown_and_none():
    from synapse_cli.setup import _sanitize_backend_for_write

    assert _sanitize_backend_for_write(None) is None
    assert _sanitize_backend_for_write("vercel-sandbox") is None
    assert _sanitize_backend_for_write("garbage") is None


def test_unknown_selection_writes_neither_config_nor_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    config = load_config()

    monkeypatch.setattr(
        "synapse_cli.setup.prompt_choice",
        lambda q, choices, default=0: 99999,
    )

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    assert config["terminal"]["backend"] == "local"
    env_path = tmp_path / ".env"
    if env_path.exists():
        assert "TERMINAL_ENV=" not in env_path.read_text(encoding="utf-8")


def test_write_ssh_key_if_present_skips_missing_path(tmp_path):
    from synapse_cli.setup import _write_ssh_key_if_present

    sink = {}
    _write_ssh_key_if_present(str(tmp_path / "does-not-exist.pem"), sink)
    assert sink == {}


def test_write_ssh_key_if_present_writes_existing_path(tmp_path):
    from synapse_cli.setup import _write_ssh_key_if_present

    key_file = tmp_path / "key.pem"
    key_file.write_text("PRIVATE-KEY", encoding="utf-8")
    sink = {}
    _write_ssh_key_if_present(str(key_file), sink)
    assert sink == {"TERMINAL_SSH_KEY": str(key_file)}


def test_write_ssh_key_if_present_expands_tilde(tmp_path, monkeypatch):
    from synapse_cli.setup import _write_ssh_key_if_present

    key_file = tmp_path / "id_ed25519"
    key_file.write_text("PRIVATE-KEY", encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))
    sink = {}
    _write_ssh_key_if_present("~/id_ed25519", sink)
    assert sink == {"TERMINAL_SSH_KEY": str(key_file)}


def test_ssh_setup_skips_dead_key_path(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_SSH_KEY", raising=False)
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    config = load_config()

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", lambda q, choices, default=0: 3)

    dead_key = str(tmp_path / "missing.pem")
    prompt_values = iter(["", "", "", dead_key])
    monkeypatch.setattr("synapse_cli.setup.prompt", lambda *a, **kw: next(prompt_values))

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    assert config["terminal"]["backend"] == "ssh"
    assert "TERMINAL_SSH_KEY" not in os.environ
    env_path = tmp_path / ".env"
    assert "TERMINAL_SSH_KEY=" not in env_path.read_text(encoding="utf-8")


def test_ssh_connection_test_skips_dead_key_in_ssh_command(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_SSH_KEY", raising=False)
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    config = load_config()

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", lambda q, choices, default=0: 3)

    dead_key = str(tmp_path / "missing.pem")
    prompt_values = iter(["myhost", "alice", "", dead_key, "y"])
    monkeypatch.setattr("synapse_cli.setup.prompt", lambda *a, **kw: next(prompt_values))
    monkeypatch.setattr("synapse_cli.setup.prompt_yes_no", lambda *a, **kw: True)

    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = list(cmd)
        return types.SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess_module, "run", fake_run)

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    assert dead_key not in captured["cmd"]


def test_env_mirror_uses_sanitized_backend_value(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    config = load_config()

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", lambda q, choices, default=0: 1)
    monkeypatch.setattr("synapse_cli.setup.prompt_yes_no", lambda *a, **kw: False)
    monkeypatch.setattr(
        "synapse_cli.setup._sanitize_backend_for_write",
        lambda selected: (selected or "").strip().upper() or None,
    )

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    env_path = tmp_path / ".env"
    assert "TERMINAL_ENV=DOCKER" in env_path.read_text(encoding="utf-8")


def test_ssh_setup_persists_existing_key_path(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_SSH_KEY", raising=False)
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    config = load_config()
    key_file = tmp_path / "key.pem"
    key_file.write_text("PRIVATE-KEY", encoding="utf-8")

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", lambda q, choices, default=0: 3)

    key_path = str(key_file)
    prompt_values = iter(["", "", "", key_path])
    monkeypatch.setattr("synapse_cli.setup.prompt", lambda *a, **kw: next(prompt_values))

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    env_path = tmp_path / ".env"
    assert f"TERMINAL_SSH_KEY={key_path}" in env_path.read_text(encoding="utf-8")


def test_vercel_default_accept_does_not_mirror_runtime(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    _clear_vercel_env(monkeypatch)
    monkeypatch.setitem(sys.modules, "vercel", types.ModuleType("vercel"))
    config = load_config()

    def fake_prompt_choice(question, choices, default=0):
        if question == "Select terminal backend:":
            return 5
        raise AssertionError(f"Unexpected prompt_choice call: {question}")

    prompt_values = iter(["", "no", "1", "5120", "token", "", ""])

    monkeypatch.setattr("synapse_cli.setup.prompt_choice", fake_prompt_choice)
    monkeypatch.setattr("synapse_cli.setup.prompt", lambda *a, **kw: next(prompt_values))

    from synapse_cli.setup import setup_terminal_backend

    setup_terminal_backend(config)

    assert config["terminal"]["backend"] == "vercel_sandbox"
    assert config["terminal"]["vercel_runtime"] == "node24"
    assert "TERMINAL_VERCEL_RUNTIME" not in os.environ
    env_path = tmp_path / ".env"
    assert "TERMINAL_VERCEL_RUNTIME=" not in env_path.read_text(encoding="utf-8")
