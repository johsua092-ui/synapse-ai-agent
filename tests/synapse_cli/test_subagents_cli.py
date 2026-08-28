"""Tests for the ``synapse subagents`` CLI command (Layer 4a).

Drives the real ``synapse_cli.main`` parser (like ``test_session_cmd.py``)
with ``sys.argv`` monkeypatched, and redirects ``SYNAPSE_HOME`` to a temp dir
so definition writes land in a throwaway store.
"""

from __future__ import annotations

import sys

import pytest


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / "home"))
    return tmp_path / "home"


@pytest.fixture()
def run_cmd(monkeypatch, capsys, home):
    def _run(argv):
        monkeypatch.setattr(sys, "argv", ["synapse", "subagents", *argv])
        try:
            import synapse_cli.main as main_mod

            main_mod.main()
        except SystemExit:
            pass
        return capsys.readouterr().out

    return _run


def test_create_then_list(run_cmd):
    out = run_cmd(["create", "sec", "--skill", "security", "--task", "Audit auth"])
    assert "created" in out

    out = run_cmd(["list"])
    assert "sec" in out
    assert "security" in out


def test_create_edit(run_cmd):
    run_cmd(["create", "a", "--model", "m1", "--task", "old task"])
    out = run_cmd(["edit", "a", "--model", "m2", "--task", "new task"])
    assert "updated" in out

    out = run_cmd(["show", "a"])
    assert "m2" in out
    assert "new task" in out


def test_show_missing(run_cmd):
    out = run_cmd(["show", "nope"])
    assert "not found" in out


def test_delete(run_cmd):
    run_cmd(["create", "gone", "--task", "x"])
    out = run_cmd(["delete", "gone"])
    assert "deleted" in out
    out2 = run_cmd(["show", "gone"])
    assert "not found" in out2


def test_list_empty(run_cmd):
    out = run_cmd(["list"])
    assert "No subagents defined" in out


def test_run_reports_goal(run_cmd):
    run_cmd(["create", "solo", "--task", "Do the thing", "--model", "mm"])
    out = run_cmd(["run", "solo"])
    assert "Would run subagent 'solo'" in out
    assert "Do the thing" in out
    assert "mm" in out


def test_run_goal_override(run_cmd):
    run_cmd(["create", "solo", "--task", "Default task"])
    out = run_cmd(["run", "solo", "--goal", "Custom goal"])
    assert "Custom goal" in out
    assert "Default task" not in out


def test_run_missing(run_cmd):
    out = run_cmd(["run", "nope"])
    assert "not found" in out


def test_active_empty(run_cmd):
    out = run_cmd(["active"])
    assert "No subagents currently running" in out


def test_team_run_reports_members(run_cmd):
    run_cmd(["create", "fe", "--task", "frontend task"])
    run_cmd(["create", "be", "--task", "backend task"])

    from synapse_cli import subagents_store

    subagents_store.create_team(name="web", max_parallel=2, agents=["fe", "be"])

    out = run_cmd(["run-team", "web"])
    assert "frontend task" in out
    assert "backend task" in out


def test_team_run_missing_team(run_cmd):
    out = run_cmd(["run-team", "nosuch"])
    assert "not found" in out
