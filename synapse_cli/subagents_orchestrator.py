"""Subagent / Agent Team orchestrator — thin glue over ``delegate_task``.

Layer 3 of the native Subagent / Agent Team system.

The heavy lifting (parallel spawn, isolation, lifecycle, timeout, failure
handling, cancellation, synthesis) is already implemented by Synapse's
``delegate_task`` batch machinery. This module is intentionally thin: it
resolves Agent Team members (and single subagent definitions) from the YAML
store into the ``tasks=[...]`` payload ``delegate_task`` already consumes, so
team members run concurrently with their assigned skills / toolsets / model.

Two kinds of result objects are produced:

* ``assemble_tasks`` / ``run_agent_payload`` — the pure, testable seam. They
  return per-task payloads (each with an internal ``goal_agent`` marker and an
  ``error`` string when a member is undefined; both are stripped before those
  payloads reach ``delegate_task``).
* ``run_team`` / ``run_agent`` — the live glue that hands the payload to the
  real ``delegate_task`` (requires a live parent agent / tool context, exactly
  like any delegation).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from synapse_cli.subagents_store import get_agent, get_team

__all__ = [
    "assemble_tasks",
    "run_agent_payload",
    "run_team",
    "run_agent",
]

# Keys carried inside task dicts that must NOT reach delegate_task.
_INTERNAL_TASK_FIELDS = ("goal_agent", "error")


def _task_from_agent(name: str, agent: Dict[str, Any], goal_override: Optional[str]) -> Dict[str, Any]:
    goal = goal_override or agent.get("task") or ""
    return {
        "goal": goal,
        "context": agent.get("context") or "",
        "skills": agent.get("skills") or [],
        "toolsets": agent.get("toolsets") or None,
        "model": agent.get("model") or "",
        "goal_agent": name,
    }


def assemble_tasks(
    team: Dict[str, Any],
    *,
    home: Optional[Any] = None,
    goal_override: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Resolve each team member definition into a ``delegate_task`` task dict.

    Members whose definition is missing are still returned, flagged with a
    truthy ``error`` (and no goal) so a caller can report the exact miss
    before attempting a run. Internal keys (``goal_agent`` / ``error``) are
    stripped by :func:`_clean_tasks` right before delegation.
    """
    tasks: List[Dict[str, Any]] = []
    for name in team.get("agents") or []:
        agent = get_agent(name, home=home)
        if agent is None:
            tasks.append({"error": f"subagent '{name}' is not defined", "goal_agent": name})
            continue
        tasks.append(_task_from_agent(name, agent, goal_override))
    return tasks


def run_agent_payload(
    *,
    name: str,
    home: Optional[Any] = None,
    goal: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Build the single-task payload for running one subagent definition."""
    agent = get_agent(name, home=home)
    if agent is None:
        return None
    tasks = assemble_tasks(
        {"agents": [name]}, home=home, goal_override=goal
    )
    return tasks[0] if tasks else None


def _clean_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Strip orchestrator-internal keys before handing payloads to delegate_task."""
    return [
        {k: v for k, v in t.items() if k not in _INTERNAL_TASK_FIELDS}
        for t in tasks
    ]


def run_team(
    team_name: str,
    *,
    home: Optional[Any] = None,
    goal: Optional[str] = None,
    parent_agent=None,
    credentials_cfg: Optional[Dict[str, Any]] = None,
):
    """Assemble a team and run it through the real ``delegate_task`` batch path.

    Returns whatever ``delegate_task`` returns (a consolidated result string).
    Requires a live parent agent / tool context, like any delegation.
    """
    from tools import delegate_tool

    team = get_team(team_name, home=home)
    if team is None:
        raise ValueError(f"agent team '{team_name}' is not defined")
    tasks = assemble_tasks(team, home=home, goal_override=goal)
    # Never delegate an unresolved member.
    tasks = [t for t in tasks if not t.get("error")]
    if not tasks:
        raise ValueError("agent team has no runnable members")
    return delegate_tool.delegate_task(
        tasks=_clean_tasks(tasks),
        parent_agent=parent_agent,
        credentials_cfg=credentials_cfg,
    )


def run_agent(
    name: str,
    *,
    home: Optional[Any] = None,
    goal: Optional[str] = None,
    parent_agent=None,
    credentials_cfg: Optional[Dict[str, Any]] = None,
):
    """Run a single subagent definition through the real ``delegate_task`` path."""
    from tools import delegate_tool

    payload = run_agent_payload(name=name, home=home, goal=goal)
    if payload is None:
        raise ValueError(f"subagent '{name}' is not defined")
    return delegate_tool.delegate_task(
        goal=payload.get("goal"),
        context=payload.get("context"),
        skills=payload.get("skills") or None,
        toolsets=payload.get("toolsets") or None,
        model=payload.get("model") or None,
        parent_agent=parent_agent,
        credentials_cfg=credentials_cfg,
    )
