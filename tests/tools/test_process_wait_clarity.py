"""Tests for process wait timeout-result clarity (not-an-error semantics)."""

import pytest

from tools.process_registry import ProcessRegistry


@pytest.fixture
def registry(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / ".synapse"))
    return ProcessRegistry()


def _spawn_sleeper(registry, notify=False):
    session = registry.spawn_local("sleep 30", cwd="/tmp", task_id="t-waitclar")
    session.notify_on_complete = notify
    return session.id


def test_wait_uses_600_second_default_timeout(monkeypatch, registry):
    monkeypatch.delenv("TERMINAL_TIMEOUT", raising=False)
    session = registry.spawn_local("sleep 30", cwd="/tmp", task_id="t-waitclar")
    session.started_at = 0
    clock = iter((0.0, 601.0))
    monkeypatch.setattr("tools.process_registry.time.monotonic", lambda: next(clock))
    monkeypatch.setattr(registry, "_refresh_detached_session", lambda current: current)
    monkeypatch.setattr(registry, "_reconcile_local_exit", lambda current: None)
    monkeypatch.setattr("tools.interrupt.is_interrupted", lambda: False)

    result = registry.wait(session.id)

    assert result["status"] == "timeout"
    assert "Wait window of 600s elapsed" in result["timeout_note"]


class TestWaitTimeoutClarity:
    def test_wait_timeout_marks_process_running(self, registry):
        sid = _spawn_sleeper(registry)
        try:
            r = registry.wait(sid, timeout=1)
            assert r["status"] == "timeout"
            assert r["process_running"] is True
            assert "not an error" in r["timeout_note"]
            assert "Uptime" in r["timeout_note"]
        finally:
            registry.kill_process(sid)

    def test_wait_timeout_suggests_notify_when_unset(self, registry):
        sid = _spawn_sleeper(registry, notify=False)
        try:
            r = registry.wait(sid, timeout=1)
            assert "notify_on_complete=true" in r["timeout_note"]
        finally:
            registry.kill_process(sid)

    def test_wait_timeout_defers_to_notify_when_set(self, registry):
        sid = _spawn_sleeper(registry, notify=True)
        try:
            r = registry.wait(sid, timeout=1)
            assert "you will be notified on exit" in r["timeout_note"]
        finally:
            registry.kill_process(sid)

    def test_clamped_wait_keeps_clamp_note_and_running_semantics(self, registry, monkeypatch):
        monkeypatch.setenv("TERMINAL_TIMEOUT", "1")
        sid = _spawn_sleeper(registry)
        try:
            r = registry.wait(sid, timeout=600)
            assert r["status"] == "timeout"
            assert "clamped" in r["timeout_note"]
            assert "not an error" in r["timeout_note"]
            assert r["process_running"] is True
        finally:
            registry.kill_process(sid)

    def test_exited_process_unaffected(self, registry):
        session = registry.spawn_local("true", cwd="/tmp", task_id="t-waitclar")
        r = registry.wait(session.id, timeout=10)
        assert r["status"] == "exited"
        assert "process_running" not in r
