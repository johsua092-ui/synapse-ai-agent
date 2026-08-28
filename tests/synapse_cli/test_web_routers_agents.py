"""Tests for the Agents dashboard web router (Layer 4b backend).

Mounts only ``web_routers/agents`` on a fresh FastAPI app with the late-bound
``_profile_scope`` swapped for a no-op, and redirects ``SYNAPSE_HOME`` to a
temp store so the CRUD endpoints exercise the real YAML store.
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from synapse_cli import subagents_store
from synapse_cli.web_routers import agents as agents_routes


@pytest.fixture()
def client(home, monkeypatch):
    @contextmanager
    def _noop_scope(*_args, **_kwargs):
        yield None

    monkeypatch.setattr(agents_routes, "_profile_scope", _noop_scope)

    app = FastAPI()
    app.include_router(agents_routes.router)
    return TestClient(app)


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / "home"))
    return tmp_path / "home"


class TestAgentsCRUD:
    def test_list_empty(self, client):
        r = client.get("/api/agents")
        assert r.status_code == 200
        assert r.json() == {"agents": []}

    def test_create_then_list(self, client):
        r = client.post(
            "/api/agents",
            json={
                "name": "fe",
                "model": "m1",
                "skills": ["ui"],
                "toolsets": ["terminal"],
                "task": "Build UI",
            },
        )
        assert r.status_code == 200
        assert r.json()["name"] == "fe"

        r = client.get("/api/agents")
        assert r.status_code == 200
        agents = r.json()["agents"]
        assert len(agents) == 1
        assert agents[0]["name"] == "fe"
        assert agents[0]["skills"] == ["ui"]

    def test_update(self, client):
        client.post("/api/agents", json={"name": "a", "task": "old"})
        r = client.put("/api/agents/a", json={"task": "new", "model": "m9"})
        assert r.status_code == 200
        assert r.json()["task"] == "new"
        assert r.json()["model"] == "m9"

    def test_update_missing_404(self, client):
        r = client.put("/api/agents/nope", json={"task": "x"})
        assert r.status_code == 404

    def test_delete(self, client):
        client.post("/api/agents", json={"name": "gone"})
        r = client.delete("/api/agents/gone")
        assert r.status_code == 200
        r = client.delete("/api/agents/gone")
        assert r.status_code == 404

    def test_active_empty(self, client):
        r = client.get("/api/agents/active")
        assert r.status_code == 200
        assert "active" in r.json()


class TestTeamsCRUD:
    def test_create_team_then_list(self, client, home):
        client.post("/api/agents", json={"name": "fe"})
        client.post("/api/agents", json={"name": "be"})
        r = client.post(
            "/api/agents/teams", json={"name": "web", "max_parallel": 2, "agents": ["fe", "be"]}
        )
        assert r.status_code == 200
        assert r.json()["agents"] == ["fe", "be"]

        r = client.get("/api/agents/teams")
        assert r.status_code == 200
        teams = r.json()["teams"]
        assert len(teams) == 1
        assert teams[0]["name"] == "web"
        # Teams live under agents/teams/, not agents/.
        assert subagents_store.get_agent("web") is None

    def test_update_team(self, client):
        client.post("/api/agents/teams", json={"name": "t1", "agents": ["fe"]})
        r = client.put("/api/agents/teams/t1", json={"agents": ["fe", "be"]})
        assert r.status_code == 200
        assert r.json()["agents"] == ["fe", "be"]

    def test_delete_team(self, client):
        client.post("/api/agents/teams", json={"name": "t1"})
        r = client.delete("/api/agents/teams/t1")
        assert r.status_code == 200
        r = client.delete("/api/agents/teams/t1")
        assert r.status_code == 404

    def test_run_team_reports_members(self, client):
        client.post("/api/agents", json={"name": "fe", "task": "frontend", "skills": ["ui"]})
        client.post("/api/agents", json={"name": "be", "task": "backend"})
        client.post("/api/agents/teams", json={"name": "web", "agents": ["fe", "be"]})

        r = client.post("/api/agents/teams/web/run")
        assert r.status_code == 200
        body = r.json()
        by_agent = {t["agent"]: t for t in body["tasks"]}
        assert set(by_agent) == {"fe", "be"}
        assert by_agent["fe"]["goal"] == "frontend"
        assert by_agent["fe"]["skills"] == ["ui"]

    def test_run_team_missing_team_404(self, client):
        r = client.post("/api/agents/teams/nosuch/run")
        assert r.status_code == 404
