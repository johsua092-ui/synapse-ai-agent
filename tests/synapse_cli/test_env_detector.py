"""Tests for synapse_cli.env_detector terminal-environment auto-detection."""

from __future__ import annotations

import os

import pytest

from synapse_cli import env_detector


@pytest.fixture(autouse=True)
def _isolate_home(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    monkeypatch.delenv("TERMINAL_ENV", raising=False)
    monkeypatch.setattr(env_detector, "is_termux", lambda: False)
    monkeypatch.setattr(env_detector, "is_container", lambda: False)
    monkeypatch.setattr(env_detector, "_docker_runtime_usable", lambda: True)
    return tmp_path


def write_config(synapse_home, terminal_backend=None):
    config = {"terminal": {"backend": terminal_backend}} if terminal_backend else {}
    config_path = synapse_home / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    import yaml

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f)
    return config_path


class TestDetectTerminalBackend:
    def test_plain_local_machine_is_local(self):
        assert env_detector.detect_terminal_backend() == "local"

    def test_termux_is_local(self, monkeypatch):
        monkeypatch.setattr(env_detector, "is_termux", lambda: True)
        monkeypatch.setattr(env_detector, "is_container", lambda: True)
        assert env_detector.detect_terminal_backend() == "local"

    def test_container_with_docker_is_docker(self, monkeypatch):
        monkeypatch.setattr(env_detector, "is_container", lambda: True)
        monkeypatch.setattr(env_detector, "_docker_runtime_usable", lambda: True)
        assert env_detector.detect_terminal_backend() == "docker"

    def test_container_without_docker_is_local(self, monkeypatch):
        monkeypatch.setattr(env_detector, "is_container", lambda: True)
        monkeypatch.setattr(env_detector, "_docker_runtime_usable", lambda: False)
        assert env_detector.detect_terminal_backend() == "local"


class TestCurrentEffectiveBackend:
    def test_config_wins_over_env(self, _isolate_home, monkeypatch):
        write_config(_isolate_home, "docker")
        monkeypatch.setenv("TERMINAL_ENV", "local")
        assert env_detector.current_effective_backend() == "docker"

    def test_env_fallback_when_no_config(self, monkeypatch):
        monkeypatch.setenv("TERMINAL_ENV", "docker")
        assert env_detector.current_effective_backend() == "docker"

    def test_none_when_neither(self):
        assert env_detector.current_effective_backend() is None


class TestEnsureTerminalEnvConfigured:
    def test_missing_backend_gets_detected_local(self, _isolate_home):
        monkeypatch = pytest.MonkeyPatch()
        result = env_detector.ensure_terminal_env_configured()
        assert result["reason"] == "missing"
        assert result["detected"] == "local"
        assert result["fixed"] is True
        assert env_detector.current_effective_backend() == "local"

    def test_invalid_backend_is_repaired(self, _isolate_home):
        write_config(_isolate_home, "nonexistent_backend")
        result = env_detector.ensure_terminal_env_configured()
        assert result["reason"] == "invalid"
        assert result["fixed"] is True
        assert env_detector.current_effective_backend() == "local"

    def test_valid_different_explicit_backend_is_respected(self, _isolate_home):
        write_config(_isolate_home, "ssh")
        result = env_detector.ensure_terminal_env_configured()
        assert result["fixed"] is False
        assert result["reason"] == "ok"
        assert env_detector.current_effective_backend() == "ssh"

    def test_container_mismatch_fixes_to_docker(self, _isolate_home, monkeypatch):
        monkeypatch.setattr(env_detector, "is_container", lambda: True)
        monkeypatch.setattr(env_detector, "_docker_runtime_usable", lambda: True)
        write_config(_isolate_home, "local")
        result = env_detector.ensure_terminal_env_configured()
        assert result["reason"] == "mismatch"
        assert result["fixed"] is True
        assert env_detector.current_effective_backend() == "docker"

    def test_persist_false_only_sets_env(self, _isolate_home):
        result = env_detector.ensure_terminal_env_configured(persist=False)
        assert result["fixed"] is False
        assert os.environ.get("TERMINAL_ENV") == "local"
        assert env_detector.current_effective_backend() == "local"

    def test_writes_land_in_config_and_env(self, _isolate_home):
        env_detector.ensure_terminal_env_configured()
        import yaml

        with open(_isolate_home / "config.yaml", encoding="utf-8") as f:
            written = yaml.safe_load(f)
        assert written["terminal"]["backend"] == "local"
        env_data = (_isolate_home / ".env").read_text(encoding="utf-8")
        assert "TERMINAL_ENV=local" in env_data

    def test_already_correct_is_noop(self, _isolate_home):
        write_config(_isolate_home, "local")
        before = (_isolate_home / "config.yaml").read_text(encoding="utf-8")
        result = env_detector.ensure_terminal_env_configured()
        assert result["reason"] == "ok"
        assert result["fixed"] is False
        after = (_isolate_home / "config.yaml").read_text(encoding="utf-8")
        assert before == after