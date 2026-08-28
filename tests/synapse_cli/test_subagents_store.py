"""Tests for the persistent subagent definition + Agent Team YAML store.

Layer 2 of the subagent/agent-team feature. Definitions live at
``<home>/agents/<name>.yaml``; Agent Teams at ``<home>/agents/teams/<team>.yaml``.
The store honors an explicit ``home`` for testability and ``SYNAPSE_HOME`` by
default (via ``get_synapse_home``).
"""

from __future__ import annotations

import pytest

import synapse_cli.subagents_store as store


@pytest.fixture()
def home(tmp_path):
    return tmp_path / "home"


def _create_one(home, **kw):
    defaults = dict(
        name="security-reviewer",
        model="",
        skills=["security"],
        toolsets=None,
        task="Audit authentication",
        timeout=None,
    )
    defaults.update(kw)
    return store.create_agent(home=home, **defaults)


class TestSubagentCRUD:
    def test_create_then_get(self, home):
        _create_one(home)
        got = store.get_agent(home=home, name="security-reviewer")
        assert got["name"] == "security-reviewer"
        assert got["skills"] == ["security"]
        assert got["toolsets"] is None

    def test_list(self, home):
        _create_one(home)
        _create_one(home, name="backend", skills=["terminal"], task="Serve API")
        names = {a["name"] for a in store.list_agents(home=home)}
        assert names == {"security-reviewer", "backend"}

    def test_get_missing_returns_none(self, home):
        assert store.get_agent(home=home, name="nope") is None

    def test_create_ignores_unknown_fields(self, home):
        _create_one(home, name="clean", skill=["plural"], bogus="x")
        got = store.get_agent(home=home, name="clean")
        assert "bogus" not in got
        assert "skill" not in got

    def test_update_preserves_and_overrides(self, home):
        _create_one(home, name="a", skills=["security"])
        store.update_agent(
            home=home, name="a", skills=["security", "design"], model="m-1"
        )
        got = store.get_agent(home=home, name="a")
        assert got["skills"] == ["security", "design"]
        assert got["model"] == "m-1"

    def test_delete(self, home):
        _create_one(home, name="a")
        assert store.delete_agent(home=home, name="a") is True
        assert store.get_agent(home=home, name="a") is None

    def test_delete_missing_returns_false(self, home):
        assert store.delete_agent(home=home, name="missing") is False

    def test_file_roundtrip_persists(self, home):
        _create_one(home, name="persisted", task="Do a thing")
        store2_agents = store.list_agents(home=home)
        assert any(a["name"] == "persisted" for a in store2_agents)


class TestTeamCRUD:
    def _team(self, home, **kw):
        defaults = dict(name="my-team", max_parallel=4, agents=["frontend", "backend"])
        defaults.update(kw)
        return store.create_team(home=home, **defaults)

    def test_create_then_get(self, home):
        self._team(home)
        got = store.get_team(home=home, name="my-team")
        assert got["name"] == "my-team"
        assert got["agents"] == ["frontend", "backend"]
        assert got["max_parallel"] == 4

    def test_list_teams(self, home):
        self._team(home, name="t1")
        self._team(home, name="t2")
        assert {t["name"] for t in store.list_teams(home=home)} == {"t1", "t2"}

    def test_update_team(self, home):
        self._team(home, name="t1", agents=["frontend"])
        store.update_team(home=home, name="t1", agents=["frontend", "backend", "ops"])
        got = store.get_team(home=home, name="t1")
        assert got["agents"] == ["frontend", "backend", "ops"]

    def test_delete_team(self, home):
        self._team(home, name="t1")
        assert store.delete_team(home=home, name="t1") is True
        assert store.get_team(home=home, name="t1") is None

    def test_teams_in_subdirectory(self, home):
        self._team(home, name="t1")
        agents_dir = home / "agents"
        assert (agents_dir / "teams" / "t1.yaml").exists()
        assert not (agents_dir / "t1.yaml").exists()


class TestEnvHome:
    def test_defaults_to_synapse_home(self, home, monkeypatch):
        monkeypatch.setenv("SYNAPSE_HOME", str(home))
        _create_one(home)
        from synapse_cli.subagents_store import get_agents_home

        assert get_agents_home() == (home / "agents")
        assert store.list_agents()  # resolves via SYNAPSE_HOME
