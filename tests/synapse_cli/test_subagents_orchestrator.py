"""Tests for the Agent Team orchestrator (thin glue over delegate_task).

Layer 3 of the subagent/agent-team feature. The orchestrator resolves team
member definitions into the ``tasks=[...]`` payload the existing
``delegate_task`` batch machinery consumes, so team members run concurrently
and isolated. This test targets the pure ``assemble_tasks`` seam — no live
delegation, no parent agent required.
"""

from __future__ import annotations

import pytest

import synapse_cli.subagents_orchestrator as orch


@pytest.fixture()
def home(tmp_path):
    return tmp_path / "home"


def _agent(home, name, *, task=None, skills=None, toolsets=None, model=""):
    import synapse_cli.subagents_store as store

    task = task if task is not None else ("Task for " + name)
    store.create_agent(
        home=home,
        name=name,
        task=task,
        skills=skills or [],
        toolsets=toolsets,
        model=model,
    )


class TestAssembleTasks:
    def _team(self, home, names, max_parallel=2):
        import synapse_cli.subagents_store as store

        return store.create_team(home=home, name="t", max_parallel=max_parallel, agents=list(names))

    def test_assembles_per_agent_payload(self, home):
        _agent(home, "frontend", skills=["ui"], model="m-fe")
        _agent(home, "backend", toolsets=["terminal"], task="Build API")
        team = self._team(home, ["frontend", "backend"])

        tasks = orch.assemble_tasks(team, home=home)
        by_name = {t["goal_agent"]: t for t in tasks}
        assert set(by_name) == {"frontend", "backend"}

        fe = by_name["frontend"]
        assert fe["skills"] == ["ui"]
        assert fe["model"] == "m-fe"
        assert fe["goal"].startswith("Task for frontend")

        be = by_name["backend"]
        assert be["toolsets"] == ["terminal"]
        assert be["goal"] == "Build API"

    def test_missing_member_flagged(self, home):
        team = self._team(home, ["ghost"])

        tasks = orch.assemble_tasks(team, home=home)
        assert tasks[0]["goal_agent"] == "ghost"
        assert tasks[0]["error"]
        assert "not defined" in tasks[0]["error"]

    def test_goal_override_applies_to_all(self, home):
        _agent(home, "a", task="Default A")
        _agent(home, "b", task="Default B")
        team = self._team(home, ["a", "b"])

        tasks = orch.assemble_tasks(team, home=home, goal_override="Review everything")
        assert all(t["goal"] == "Review everything" for t in tasks)

    def test_members_keep_own_skills(self, home):
        _agent(home, "a", skills=["sec"], model="m-a")
        _agent(home, "b", skills=["design"])
        team = self._team(home, ["a", "b"])

        tasks = orch.assemble_tasks(team, home=home)
        by = {t["goal_agent"]: t for t in tasks}
        assert by["a"]["skills"] == ["sec"]
        assert by["b"]["skills"] == ["design"]


class TestRunAgentPayload:
    def test_builds_single_task_payload(self, home):
        _agent(home, "solo", task="Do something", skills=["x"], model="m1")

        payload = orch.run_agent_payload(home=home, name="solo")
        assert payload["goal"] == "Do something"
        assert payload["skills"] == ["x"]
        assert payload["model"] == "m1"

    def test_builds_single_task_payload_with_override(self, home):
        _agent(home, "solo", task="Default")
        payload = orch.run_agent_payload(home=home, name="solo", goal="Override goal")
        assert payload["goal"] == "Override goal"

    def test_missing_agent_returns_none(self, home):
        assert orch.run_agent_payload(home=home, name="missing") is None
