import sys

import pytest


class _FakeDB:
    """Shared in-memory fake matching the surface ``cmd_session`` uses."""

    def __init__(self):
        self.sessions = {
            "abc123": {
                "id": "abc123",
                "title": "Coding project",
                "started_at": 1_700_000_000,
                "last_active": 1_700_000_100,
                "pinned": False,
            },
            "def456": {
                "id": "def456",
                "title": "Test session",
                "started_at": 1_700_000_100,
                "last_active": 1_700_000_200,
                "pinned": False,
            },
        }
        self.deleted_single = []
        self.deleted_bulk = None
        self.closed = False

    def resolve_session_id(self, sid):
        if sid == "abc123":
            return "abc123"
        if sid == "def456":
            return "def456"
        return None

    def get_session(self, sid):
        return self.sessions.get(sid)

    def delete_session(self, sid, sessions_dir=None, **kwargs):
        self.deleted_single.append(sid)
        return sid in self.sessions

    def delete_sessions(self, ids, sessions_dir=None):
        self.deleted_bulk = list(ids)
        return len(ids)

    def list_sessions_rich(self, **kwargs):
        if kwargs.get("limit", 0) == 10_000_000:
            return [dict(s, id=sid) for sid, s in self.sessions.items()]
        return list(self.sessions.values())

    def close(self):
        self.closed = True


@pytest.fixture
def run_cmd(monkeypatch, capsys):
    """Run ``synapse session <args>`` against a _FakeDB, returning (db, output)."""
    import synapse_state

    db = _FakeDB()
    monkeypatch.setattr(synapse_state, "SessionDB", lambda: db)

    def _run(argv, confirm=None):
        monkeypatch.setattr(sys, "argv", ["synapse", "session", *argv])
        if confirm is not None:
            monkeypatch.setattr("builtins.input", lambda _p="": confirm)
        try:
            import synapse_cli.main as main_mod

            main_mod.main()
        except SystemExit:
            pass
        return db, capsys.readouterr().out

    return _run


def test_session_delete_requires_confirmation(run_cmd):
    db, out = run_cmd(["delete", "abc123"], confirm="y")
    assert "Coding project" in out
    assert "ID:" in out
    assert "Created:" in out
    assert "Updated:" in out
    assert db.deleted_single == ["abc123"]
    assert "✓ Session abc123 deleted." in out
    assert db.closed


def test_session_delete_confirmation_no(run_cmd):
    db, out = run_cmd(["delete", "abc123"], confirm="n")
    assert db.deleted_single == []
    assert "Cancelled." in out


def test_session_delete_not_found(run_cmd):
    db, out = run_cmd(["delete", "nope"], confirm="y")
    assert db.deleted_single == []
    assert "not found." in out


def test_session_delete_yes_skips_confirmation(run_cmd):
    db, out = run_cmd(["delete", "abc123", "--yes"])
    assert db.deleted_single == ["abc123"]
    assert "✓ Session abc123 deleted." in out


def test_session_delete_all_strict_confirmation(run_cmd):
    db, out = run_cmd(["delete", "--all"], confirm="y")
    assert "This will permanently delete all Synapse sessions." in out
    assert db.deleted_bulk and len(db.deleted_bulk) == 2
    assert "✓ Deleted 2 session(s)." in out


def test_session_delete_all_confirmation_no(run_cmd):
    db, out = run_cmd(["delete", "--all"], confirm="n")
    assert db.deleted_bulk is None
    assert "Aborted." in out


def test_session_delete_all_yes(run_cmd):
    db, out = run_cmd(["delete", "--all", "--yes"])
    assert db.deleted_bulk and len(db.deleted_bulk) == 2
    assert "✓ Deleted 2 session(s)." in out


def test_session_delete_all_conflicts_with_id(run_cmd):
    db, out = run_cmd(["delete", "abc123", "--all"], confirm="y")
    assert db.deleted_bulk is None
    assert db.deleted_single == []
    assert "--all together with a session ID" in out


def test_session_list_output(run_cmd):
    db, out = run_cmd(["list"])
    assert "ID" in out
    assert "abc123" in out
    assert "Coding project" in out
