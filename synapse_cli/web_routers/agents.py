"""Agents dashboard routes — native subagent / Agent Team definitions + teams.

Layer 4b of the native Subagent / Agent Team feature. Mirrors the
``web_routers/skills.py`` single-router pattern: ``router = APIRouter()`` mounted
by ``synapse_cli.web_server``. The store it drives (``subagents_store``) is a
standalone module over ``~/.synapse/agents`` YAML files, so no web_server-owned
helper is needed via the late-binding seam — only ``load_config``/profile scope
for profile-aware home resolution.

Endpoints:
* ``GET    /api/agents``                 — list saved subagent definitions
* ``POST   /api/agents``                 — create a definition
* ``PUT    /api/agents/{name}``          — update a definition
* ``DELETE /api/agents/{name}``          — delete a definition
* ``GET    /api/agents/active``          — currently running subagents
* ``GET    /api/agents/teams``           — list Agent Teams
* ``POST   /api/agents/teams``           — create an Agent Team
* ``PUT    /api/agents/teams/{name}``    — update an Agent Team
* ``DELETE /api/agents/teams/{name}``    — delete an Agent Team
* ``POST   /api/agents/teams/{name}/run`` — assemble + run an Agent Team
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from synapse_cli.web_deps import late
from synapse_cli.web_models import (
    AgentCreate,
    AgentTeamCreate,
    AgentTeamRun,
    AgentTeamUpdate,
    AgentUpdate,
)

# Same logger the extraction uses (identical logger object).
_log = logging.getLogger("synapse_cli.web_server")

router = APIRouter()

# Late-bound web_server helper (cycle-safe, monkeypatch-transparent).
_profile_scope = late("_profile_scope")


def _store():
    from synapse_cli import subagents_store

    return subagents_store


def _orchestrator():
    from synapse_cli import subagents_orchestrator

    return subagents_orchestrator


def _agent_payload(agent: dict) -> dict:
    return {
        "name": agent.get("name"),
        "model": agent.get("model") or "",
        "skills": agent.get("skills") or [],
        "toolsets": agent.get("toolsets") or [],
        "task": agent.get("task") or "",
    }


def _team_payload(team: dict) -> dict:
    return {
        "name": team.get("name"),
        "max_parallel": team.get("max_parallel"),
        "agents": team.get("agents") or [],
    }


# ─── Subagent definitions ────────────────────────────────────────────────────


@router.get("/api/agents")
async def list_agents(profile: Optional[str] = None):
    def _run():
        with _profile_scope(profile):
            return [_agent_payload(a) for a in _store().list_agents()]

    try:
        agents = await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("GET /api/agents failed")
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"agents": agents}


@router.get("/api/agents/active")
async def list_active_agents():
    def _run():
        from tools.delegate_tool import list_active_subagents

        return list_active_subagents()

    try:
        active = await asyncio.to_thread(_run)
    except Exception:
        _log.exception("GET /api/agents/active failed")
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"active": active}


@router.post("/api/agents")
async def create_agent(body: AgentCreate):
    def _run():
        with _profile_scope(body.profile):
            data = _store().create_agent(
                body.name,
                model=body.model or "",
                skills=body.skills or [],
                toolsets=body.toolsets or None,
                task=body.task or "",
                timeout=body.timeout,
            )
            return _agent_payload(data)

    try:
        return await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("POST /api/agents failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/api/agents/{name}")
async def update_agent(name: str, body: AgentUpdate):
    def _run():
        with _profile_scope(body.profile):
            store = _store()
            kwargs = {}
            if body.model is not None:
                kwargs["model"] = body.model
            if body.skills is not None:
                kwargs["skills"] = body.skills
            if body.toolsets is not None:
                kwargs["toolsets"] = body.toolsets
            if body.task is not None:
                kwargs["task"] = body.task
            if body.timeout is not None:
                kwargs["timeout"] = body.timeout
            data = store.update_agent(name, **kwargs)
            if data is None:
                raise HTTPException(status_code=404, detail=f"subagent '{name}' not found")
            return _agent_payload(data)

    try:
        return await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("PUT /api/agents/%s failed", name)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/api/agents/{name}")
async def delete_agent(name: str, profile: Optional[str] = None):
    def _run():
        with _profile_scope(profile):
            if not _store().delete_agent(name):
                raise HTTPException(status_code=404, detail=f"subagent '{name}' not found")
            return {"ok": True}

    try:
        return await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("DELETE /api/agents/%s failed", name)
        raise HTTPException(status_code=500, detail="Internal server error")


# ─── Agent Teams ─────────────────────────────────────────────────────────────


@router.get("/api/agents/teams")
async def list_teams(profile: Optional[str] = None):
    def _run():
        with _profile_scope(profile):
            return [_team_payload(t) for t in _store().list_teams()]

    try:
        teams = await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("GET /api/agents/teams failed")
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"teams": teams}


@router.post("/api/agents/teams")
async def create_team(body: AgentTeamCreate):
    def _run():
        with _profile_scope(body.profile):
            data = _store().create_team(
                body.name,
                max_parallel=body.max_parallel,
                agents=body.agents or [],
            )
            return _team_payload(data)

    try:
        return await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("POST /api/agents/teams failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/api/agents/teams/{name}")
async def update_team(name: str, body: AgentTeamUpdate):
    def _run():
        with _profile_scope(body.profile):
            store = _store()
            kwargs = {}
            if body.max_parallel is not None:
                kwargs["max_parallel"] = body.max_parallel
            if body.agents is not None:
                kwargs["agents"] = body.agents
            data = store.update_team(name, **kwargs)
            if data is None:
                raise HTTPException(status_code=404, detail=f"agent team '{name}' not found")
            return _team_payload(data)

    try:
        return await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("PUT /api/agents/teams/%s failed", name)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/api/agents/teams/{name}")
async def delete_team(name: str, profile: Optional[str] = None):
    def _run():
        with _profile_scope(profile):
            if not _store().delete_team(name):
                raise HTTPException(status_code=404, detail=f"agent team '{name}' not found")
            return {"ok": True}

    try:
        return await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("DELETE /api/agents/teams/%s failed", name)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/api/agents/teams/{name}/run")
async def run_team(name: str, body: AgentTeamRun = AgentTeamRun()):
    """Assemble an Agent Team and show what would be run.

    A live delegation needs a running agent / tool context; the dashboard
    endpoint resolves the team into its delegate payload (per-member goal,
    skills, toolsets, model) and reports any unresolved members so the UI can
    show exactly what a run would delegate.
    """

    def _run():
        with _profile_scope(body.profile):
            orch = _orchestrator()
            store = _store()
            team = store.get_team(name)
            if team is None:
                raise HTTPException(status_code=404, detail=f"agent team '{name}' not found")
            tasks = orch.assemble_tasks(team, goal_override=body.goal)
            return [
                {
                    "agent": t.get("goal_agent"),
                    "goal": t.get("goal") or "",
                    "skills": t.get("skills") or [],
                    "toolsets": t.get("toolsets") or [],
                    "model": t.get("model") or "",
                    "error": t.get("error"),
                }
                for t in tasks
            ]

    try:
        tasks = await asyncio.to_thread(_run)
    except HTTPException:
        raise
    except Exception:
        _log.exception("POST /api/agents/teams/%s/run failed", name)
        raise HTTPException(status_code=500, detail="Internal server error")
    return {"team": name, "tasks": tasks}
