"""Migration v39: legacy terminal timeouts (60/180) lift to the 600s default."""

import os

import pytest


@pytest.fixture
def migration_env(tmp_path, monkeypatch):
    """Hermetic SYNAPSE_HOME with a config.yaml + .env pair."""
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / ".synapse"))
    home = tmp_path / ".synapse"
    home.mkdir(parents=True)
    (home / "config.yaml").write_text(
        "_config_version: 38\nterminal:\n  backend: local\n  timeout: 180\n"
    )
    (home / ".env").write_text("TERMINAL_TIMEOUT=180\n")
    return home


def _run_v39():
    from synapse_cli.config_migrations import _migrate_to_39

    results = {"config_added": [], "env_removed": [], "warnings": []}
    _migrate_to_39(results, quiet=True)
    return results


def _read_config(home):
    import yaml

    return yaml.safe_load((home / "config.yaml").read_text())


def _read_env(home):
    return (home / ".env").read_text()


def test_config_timeout_180_lifted_to_600(migration_env):
    results = _run_v39()
    assert _read_config(migration_env)["terminal"]["timeout"] == 600
    assert any("terminal.timeout=600" in line for line in results["config_added"])


def test_env_legacy_timeout_removed(migration_env, monkeypatch):
    monkeypatch.setenv("TERMINAL_TIMEOUT", "180")
    results = _run_v39()
    assert "TERMINAL_TIMEOUT" not in _read_env(migration_env)
    assert os.environ.get("TERMINAL_TIMEOUT") is None
    assert any("TERMINAL_TIMEOUT" in line for line in results["env_removed"])


def test_env_value_60_removed_too(migration_env, monkeypatch):
    monkeypatch.setenv("TERMINAL_TIMEOUT", "60")
    _run_v39()
    assert "TERMINAL_TIMEOUT" not in _read_env(migration_env)


def test_deliberate_timeout_preserved(migration_env):
    cfg = _read_config(migration_env)
    cfg["terminal"]["timeout"] = 120
    import yaml

    (migration_env / "config.yaml").write_text(yaml.safe_dump(cfg))
    results = _run_v39()
    assert _read_config(migration_env)["terminal"]["timeout"] == 120
    assert results["config_added"] == []


def test_env_file_wins_over_stale_process_env(migration_env, monkeypatch):
    # os.environ says 900 (e.g. worker-scoped override) but the FILE carries
    # the legacy 180 — the file is the source of truth and must be cleaned.
    monkeypatch.setenv("TERMINAL_TIMEOUT", "900")
    results = _run_v39()
    assert "TERMINAL_TIMEOUT" not in _read_env(migration_env)
    assert any("TERMINAL_TIMEOUT" in line for line in results["env_removed"])


def test_non_legacy_env_file_value_preserved(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / ".synapse"))
    home = tmp_path / ".synapse"
    home.mkdir(parents=True)
    (home / "config.yaml").write_text(
        "_config_version: 38\nterminal:\n  backend: local\n  timeout: 600\n"
    )
    (home / ".env").write_text("TERMINAL_TIMEOUT=900\n")
    results = _run_v39()
    assert "TERMINAL_TIMEOUT=900" in _read_env(home)
    assert results["env_removed"] == []


def test_noop_when_already_current(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / ".synapse"))
    home = tmp_path / ".synapse"
    home.mkdir(parents=True)
    (home / "config.yaml").write_text(
        "_config_version: 39\nterminal:\n  backend: local\n  timeout: 600\n"
    )
    (home / ".env").write_text("")
    results = _run_v39()
    assert results["config_added"] == []
    assert results["env_removed"] == []
    assert _read_config(home)["terminal"]["timeout"] == 600
