"""``synapse subagents`` command — subagent / Agent Team management CLI.

Layer 4a of the native Subagent / Agent Team system, mirroring the
``session_cmd.py`` pattern: a ``cmd_*`` dispatcher on a sub-action, plain
``print()``, home resolution via ``get_synapse_home``, and lazy imports so the
module stays import-light until the subcommand actually runs.

Surfaces:

* ``synapse subagents list``                    — list saved definitions + teams
* ``synapse subagents create <name> [--skill S]... [--tool T]... [--model M] [--task TASK]``
* ``synapse subagents edit <name> [same flags]``
* ``synapse subagents delete <name>``
* ``synapse subagents run <name> [--goal G]``            — resolve one definition
* ``synapse subagents run-team <team> [--goal G]``       — assemble + run a team
* ``synapse subagents active``                          — trn running subagents

Only declarative definition data is touched — never credentials or keys.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def _m():
    """Lazy ``synapse_cli.main`` reference (call-time, keeps patches working)."""
    from synapse_cli import main

    return main


def get_synapse_home() -> Path:
    return _m().get_synapse_home()


def _store():
    from synapse_cli import subagents_store

    return subagents_store


def _orchestrator():
    from synapse_cli import subagents_orchestrator

    return subagents_orchestrator


def _relative_time(ts):
    return _m()._relative_time(ts)


def _fmt_ts(ts):
    if not ts:
        return "—"
    try:
        return _m()._relative_time(ts)
    except Exception:
        return str(ts)


def _field_list(value):
    if isinstance(value, (list, tuple)):
        return ", ".join(str(v) for v in value)
    if value:
        return str(value)
    return "—"


def _render_agent(agent: dict) -> str:
    return (
        f"  name:     {agent.get('name', '?')}\n"
        f"  model:    {agent.get('model') or '—'}\n"
        f"  skills:   {_field_list(agent.get('skills'))}\n"
        f"  toolsets: {_field_list(agent.get('toolsets'))}\n"
        f"  task:     {agent.get('task') or '—'}"
    )


def _render_team(team: dict) -> str:
    return (
        f"  name:        {team.get('name', '?')}\n"
        f"  max_parallel:{team.get('max_parallel', '—')}\n"
        f"  agents:      {_field_list(team.get('agents'))}"
    )


def _list_cmd(args):
    store = _store()
    home = get_synapse_home()
    agents = store.list_agents(home=home)
    teams = store.list_teams(home=home)

    if not agents and not teams:
        print("No subagents defined.")
        return 0

    if agents:
        print("Subagents:")
        for a in agents:
            print(f"  - {a.get('name', '?')}   [{_field_list(a.get('skills'))}]")
        print()

    if teams:
        print("Agent Teams:")
        for t in teams:
            print(f"  - {t.get('name', '?')}   ({_field_list(t.get('agents'))})")

    return 0


def _show_cmd(args):
    store = _store()
    agent = store.get_agent(args.name, home=get_synapse_home())
    if agent is None:
        print(f"Error: subagent '{args.name}' not found.")
        return 1
    print(_render_agent(agent))
    return 0


def _create_cmd(args):
    store = _store()
    data = store.create_agent(
        args.name,
        model=args.model,
        skills=args.skill,
        toolsets=args.tool,
        task=args.task,
        home=get_synapse_home(),
    )
    print(f"✓ Subagent '{data['name']}' created.")
    return 0


def _edit_cmd(args):
    store = _store()
    kwargs = {}
    if args.model is not None:
        kwargs["model"] = args.model
    if args.skill is not None:
        kwargs["skills"] = args.skill
    if args.tool is not None:
        kwargs["toolsets"] = args.tool
    if args.task is not None:
        kwargs["task"] = args.task
    result = store.update_agent(args.name, home=get_synapse_home(), **kwargs)
    if result is None:
        print(f"Error: subagent '{args.name}' not found.")
        return 1
    print(f"✓ Subagent '{args.name}' updated.")
    return 0


def _delete_cmd(args):
    store = _store()
    if store.delete_agent(args.name, home=get_synapse_home()):
        print(f"✓ Subagent '{args.name}' deleted.")
        return 0
    print(f"Error: subagent '{args.name}' not found.")
    return 1


def _active_cmd(args):
    try:
        from tools.delegate_tool import list_active_subagents

        agents = list_active_subagents()
    except Exception as e:  # pragma: no cover
        print(f"Error: could not query active subagents: {e}")
        return 1

    if not agents:
        print("No subagents currently running.")
        return 0

    print(f"{'ID':<14} {'STATUS':<14} {'MODEL':<18} GOAL")
    print("─" * 78)
    for a in agents:
        print(
            f"{a.get('subagent_id', '?')[:13]:<14} "
            f"{str(a.get('status', '?'))[:13]:<14} "
            f"{str(a.get('model', '?'))[:17]:<18} "
            f"{(a.get('goal') or '')[:40]}"
        )
    return 0


def _resolve_and_report(kind: str, name: str, goal: Optional[str]) -> int:
    """Resolve a definition/team into its delegation payload and show it.

    Running a live delegation from the raw CLI is the same situation as
    calling ``delegate_task`` directly: it needs a running agent / tool
    context. Here we resolve and print exactly what would be delegated so a
    user can inspect (and, from inside an agent, call the same payload via
    ``delegate_task``). ``--goal`` overrides the task text.
    """
    orch = _orchestrator()
    store = _store()
    home = get_synapse_home()

    if kind == "agent":
        payload = orch.run_agent_payload(name=name, home=home, goal=goal)
        if payload is None:
            print(f"Error: subagent '{name}' not found.")
            return 1
        print(f"Would run subagent '{name}':")
        print(f"  goal:     {payload.get('goal') or '—'}")
        print(f"  skills:   {_field_list(payload.get('skills'))}")
        print(f"  toolsets: {_field_list(payload.get('toolsets'))}")
        print(f"  model:    {payload.get('model') or '—'}")
        return 0

    team = store.get_team(name, home=home)
    if team is None:
        print(f"Error: agent team '{name}' not found.")
        return 1
    tasks = orch.assemble_tasks(team, home=home, goal_override=goal)
    print(f"Would run agent team '{name}' ({len(tasks)} member(s)):")
    for t in tasks:
        if t.get("error"):
            print(f"  - {t.get('goal_agent', '?')}: {t['error']}")
        else:
            print(f"  - {t.get('goal_agent')}: {t.get('goal') or '—'}  "
                  f"[skills={_field_list(t.get('skills'))} toolsets={_field_list(t.get('toolsets'))}]")
    return 0


def cmd_subagents(args):
    """Dispatch for the ``synapse subagents`` command."""
    action = getattr(args, "subagents_action", None)

    if action == "list":
        return _list_cmd(args)
    if action == "show":
        return _show_cmd(args)
    if action == "create":
        return _create_cmd(args)
    if action == "edit":
        return _edit_cmd(args)
    if action == "delete":
        return _delete_cmd(args)
    if action == "active":
        return _active_cmd(args)
    if action == "run":
        return _resolve_and_report("agent", args.name, getattr(args, "goal", None))
    if action == "run-team":
        return _resolve_and_report("team", args.name, getattr(args, "goal", None))

    # Fallthrough: bare ``synapse subagents`` with no subcommand.
    if args is not None:
        try:
            print("Usage: synapse subagents {list,show,create,edit,delete,run,run-team,active}\n")
            print("Manage subagent definitions and Agent Teams.")
            print("\nAvailable subcommands:")
            print("  list                         List saved subagents and teams")
            print("  show <name>                  Show one subagent definition")
            print("  create <name> [options]      Create a subagent definition")
            print("  edit <name> [options]        Update a subagent definition")
            print("  delete <name>                Delete a subagent definition")
            print("  run <name> [--goal G]        Resolve one definition to run")
            print("  run-team <team> [--goal G]   Resolve + assemble an Agent Team")
            print("  active                       List currently running subagents")
            return 0
        except Exception:  # pragma: no cover
            pass
    return 0
