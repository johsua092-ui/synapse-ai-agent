"""``synapse session`` command — session management CLI.

A focused, user-facing session-management surface built on top of the same
synapse_state ``SessionDB`` that drives ``synapse sessions`` (plural). It
keeps the CLI UX described in the task brief:

* ``synapse session list``            — readable listing (ID, TITLE, UPDATED)
* ``synapse session delete <id>``     — confirm then delete one session
* ``synapse session delete --all``    — strict confirmation, then delete all
* ``synapse session delete <id> --yes`` / ``--all --yes`` — skip confirmation

Only session data is touched — never configuration, credentials, API keys,
skills, or installation files. Deletion delegates to ``SessionDB.delete_session``
/ ``SessionDB.delete_sessions`` (the single backend shared by the CLI, the
desktop, and the web dashboard API), so there is exactly one delete
implementation in the codebase.
"""

import os
import sys
from pathlib import Path


def _m():
    """Lazy ``synapse_cli.main`` reference (call-time, keeps patches working)."""
    from synapse_cli import main

    return main


def _confirm_prompt(prompt: str) -> bool:
    """Prompt for y/N confirmation, safe against non-TTY environments."""
    try:
        return input(prompt).strip().lower() in {"y", "yes"}
    except (EOFError, KeyboardInterrupt):
        return False


def _relative_time(ts):
    return _m()._relative_time(ts)


def _render_info(session: dict) -> str:
    """Build the human-readable session info block shown before deletion."""
    import time as _time

    def _fmt(v):
        if not v:
            return "—"
        try:
            return _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime(float(v)))
        except (TypeError, ValueError, OSError):
            return str(v)

    lines = ["Session:"]
    title = session.get("title") or session.get("preview") or ""
    if title:
        lines.append(f"  Title:   {title}")
    lines.append(f"  ID:      {session.get('id', '?')}")
    lines.append(f"  Created: {_fmt(session.get('started_at') or session.get('created_at'))}")
    lines.append(f"  Updated: {_fmt(session.get('last_active'))}")
    return "\n".join(lines)


def _open_db():
    """Open the shared session store, returning a ``(db, error)`` pair."""
    try:
        from synapse_state import SessionDB

        return SessionDB(), None
    except Exception as e:  # pragma: no cover - mirrors existing error path
        return None, f"Error: Could not open session database: {e}"


def _sessions_dir() -> Path:
    return get_synapse_home() / "sessions"


def get_synapse_home() -> Path:
    return _m().get_synapse_home()


def _list_sessions(args):
    """``synapse session list`` — readable ID/TITLE/UPDATED listing."""
    db, err = _open_db()
    if err:
        print(err)
        return 1
    try:
        source = getattr(args, "source", None)
        exclude = None if source else ["tool"]
        try:
            sessions = db.list_sessions_rich(
                source=source,
                exclude_sources=exclude,
                limit=getattr(args, "limit", 100),
            )
        except TypeError:
            sessions = db.list_sessions_rich(
                source=source, limit=getattr(args, "limit", 100)
            )
    finally:
        db.close()

    if not sessions:
        print("No sessions found.")
        return 0

    print(f"{'ID':<22} {'TITLE':<40} {'UPDATED'}")
    print("─" * 78)
    for s in sessions:
        sid = s.get("id", "?")
        title = (s.get("title") or s.get("preview") or "—")[:38]
        print(f"{sid:<22} {title:<40} {_relative_time(s.get('last_active'))}")
    return 0


def _delete_one(db, args) -> int:
    """``synapse session delete <session_id>`` (with optional --yes)."""
    from synapse_state import workspace_key as _ws_key  # noqa: F401  (kept for parity)

    sid = args.session_id
    resolved = db.resolve_session_id(sid)
    if not resolved:
        print(f"Error: session '{sid}' not found.")
        return 1

    _get_session = getattr(db, "get_session", None)
    _meta = (_get_session(resolved) or {}) if callable(_get_session) else {}
    print(_render_info(_meta or {"id": resolved}))

    pinned_note = " (PINNED)" if _meta.get("pinned") else ""
    if not args.yes:
        if not _confirm_prompt(f"Delete this session{pinned_note}? [y/N] "):
            print("Cancelled.")
            return 1

    sessions_dir = _sessions_dir()
    if db.delete_session(resolved, sessions_dir=sessions_dir):
        print(f"✓ Session {resolved} deleted.")
        return 0
    print(f"Error: session '{sid}' not found.")
    return 1


def _delete_all(db, args) -> int:
    """``synapse session delete --all`` — strict confirmation, delete all."""
    if not args.yes:
        print("⚠ This will permanently delete all Synapse sessions.")
        if not _confirm_prompt("Continue? [y/N] "):
            print("Aborted.")
            return 1

    # Enumerate every session id (no source filtering — this is a full wipe).
    try:
        all_sessions = db.list_sessions_rich(
            source=None,
            exclude_sources=None,
            limit=10_000_000,
            include_children=True,
            include_hidden=True,
            include_archived=True,
            include_pinned=True,
        )
    except TypeError:  # pragma: no cover - degrade gracefully on older SessionDB
        all_sessions = db.list_sessions_rich(
            source=None, limit=10_000_000, include_children=True,
            include_archived=True, include_pinned=True,
        )

    ids = [s.get("id") for s in all_sessions if s.get("id")]
    if not ids:
        print("No sessions to delete.")
        return 0

    deleted = db.delete_sessions(ids, sessions_dir=_sessions_dir())
    print(f"✓ Deleted {deleted} session(s).")
    return 0


def cmd_session(args):
    """Dispatch for the ``synapse session`` command."""
    action = getattr(args, "session_action", None)

    if action == "list":
        return _list_sessions(args)

    if action == "delete":
        if getattr(args, "all", False) and getattr(args, "session_id", None):
            print("Error: cannot use --all together with a session ID.")
            return 2
        db, err = _open_db()
        if err:
            print(err)
            return 1
        try:
            if getattr(args, "all", False):
                return _delete_all(db, args)
            return _delete_one(db, args)
        finally:
            db.close()

    # Fallthrough: bare ``synapse session`` with no subcommand.
    if args is not None:
        try:
            print("Usage: synapse session {list,delete} [options]\n")
            print("Manage Synapse sessions.")
            print("\nAvailable subcommands:")
            print("  list              List recent sessions")
            print("                    synapse session list")
            print("  delete <id>       Delete a single session (confirm, or --yes)")
            print("                    synapse session delete <session-id>")
            print("  delete --all      Delete all sessions (strict confirm, or --yes)")
            print("                    synapse session delete --all")
            return 0
        except Exception:  # pragma: no cover
            pass
    return 0
