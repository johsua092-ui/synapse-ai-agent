"""Persistent subagent definitions + Agent Team YAML store.

Layer 2 of the native Subagent / Agent Team system.

Storage layout (mirrors Synapse config conventions, resolved via
``get_synapse_home`` unless an explicit ``home`` is given for testability):

* ``<home>/agents/<name>.yaml``            — one subagent definition
* ``<home>/agents/teams/<team>.yaml``      — one Agent Team

A subagent definition:

.. code-block:: yaml

    name: security-reviewer
    model: ""                 # empty = use default / delegation config
    skills: [security, superpowers/systematic-debugging]
    toolsets: [terminal]      # optional; empty = inherit parent's toolsets
    task: "Audit the authentication implementation"
    timeout: 600              # optional seconds

An Agent Team:

.. code-block:: yaml

    name: my-team
    max_parallel: 4
    agents: [frontend, backend, security]

Only non-secret, declarative fields are written — never credentials or keys.
Writes go through ``atomic_yaml_write``; reads through the comment-safe
``fast_safe_load`` helper, so the exact utility the rest of the codebase uses
is reused (no second YAML implementation).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils import atomic_yaml_write, fast_safe_load

__all__ = [
    "get_agents_home",
    "get_teams_home",
    "agent_file",
    "team_file",
    "list_agents",
    "get_agent",
    "create_agent",
    "update_agent",
    "delete_agent",
    "list_teams",
    "get_team",
    "create_team",
    "update_team",
    "delete_team",
]

# Fields a subagent definition may carry (canonical keys). Anything else a user
# provides (typos, plural aliases) is dropped on write — see the ignore test.
_AGENT_FIELDS = ("name", "model", "skills", "toolsets", "task", "timeout")
_TEAM_FIELDS = ("name", "max_parallel", "agents")
_AGENTS_SUBDIR = "agents"
_TEAMS_SUBDIR = "teams"


def get_agents_home(home: Optional[Path] = None) -> Path:
    """Return the directory holding subagent definitions."""
    return (_resolve_home(home) / _AGENTS_SUBDIR)


def get_teams_home(home: Optional[Path] = None) -> Path:
    """Return the directory holding Agent Team definitions."""
    return (_resolve_home(home) / _AGENTS_SUBDIR / _TEAMS_SUBDIR)


def _resolve_home(home: Optional[Path] = None) -> Path:
    if home is not None:
        return Path(home)
    from synapse_constants import get_synapse_home

    return get_synapse_home()


def agent_file(name: str, home: Optional[Path] = None) -> Path:
    return get_agents_home(home) / f"{name}.yaml"


def team_file(name: str, home: Optional[Path] = None) -> Path:
    return get_teams_home(home) / f"{name}.yaml"


def _sanitize_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    for key in _AGENT_FIELDS:
        if key in data:
            clean[key] = data[key]
    return clean


def _sanitize_team(data: Dict[str, Any]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    for key in _TEAM_FIELDS:
        if key in data:
            clean[key] = data[key]
    return clean


def _read_yaml(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = fast_safe_load(fh)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _mkdirs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write(path: Path, data: Dict[str, Any]) -> None:
    _mkdirs(path)
    atomic_yaml_write(path, data, sort_keys=False)


# ─── Subagent definitions ────────────────────────────────────────────────────


def list_agents(home: Optional[Path] = None) -> List[Dict[str, Any]]:
    d = get_agents_home(home)
    if not d.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    for path in sorted(d.glob("*.yaml")):
        data = _read_yaml(path)
        if data:
            out.append(data)
    return out


def get_agent(name: str, home: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    return _read_yaml(agent_file(name, home))


def create_agent(
    name: str,
    *,
    model: Optional[str] = "",
    skills: Optional[List[str]] = None,
    toolsets: Optional[List[str]] = None,
    task: Optional[str] = "",
    timeout: Optional[int] = None,
    home: Optional[Path] = None,
    **_extra,
) -> Dict[str, Any]:
    data = _sanitize_agent(
        {
            "name": name,
            "model": model or "",
            "skills": list(skills or []),
            "toolsets": list(toolsets) if toolsets else None,
            "task": task or "",
            "timeout": timeout,
        }
    )
    _write(agent_file(name, home), data)
    return data


def update_agent(
    name: str,
    *,
    model: Optional[str] = None,
    skills: Optional[List[str]] = None,
    toolsets: Optional[List[str]] = None,
    task: Optional[str] = None,
    timeout: Optional[int] = None,
    home: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    path = agent_file(name, home)
    current = _read_yaml(path)
    if current is None:
        return None
    if model is not None:
        current["model"] = model
    if skills is not None:
        current["skills"] = list(skills)
    if toolsets is not None:
        current["toolsets"] = list(toolsets)
    if task is not None:
        current["task"] = task
    if timeout is not None:
        current["timeout"] = timeout
    clean = _sanitize_agent(current)
    _write(path, clean)
    return clean


def delete_agent(name: str, home: Optional[Path] = None) -> bool:
    path = agent_file(name, home)
    if not path.exists():
        return False
    try:
        path.unlink()
    except OSError:
        return False
    return True


# ─── Agent Teams ─────────────────────────────────────────────────────────────


def list_teams(home: Optional[Path] = None) -> List[Dict[str, Any]]:
    d = get_teams_home(home)
    if not d.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    for path in sorted(d.glob("*.yaml")):
        data = _read_yaml(path)
        if data:
            out.append(data)
    return out


def get_team(name: str, home: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    return _read_yaml(team_file(name, home))


def parse_max_parallel(value) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return 0
    return n if n > 0 else 0


def create_team(
    name: str,
    *,
    max_parallel: Optional[int] = None,
    agents: Optional[List[str]] = None,
    home: Optional[Path] = None,
    **_extra,
) -> Dict[str, Any]:
    data = _sanitize_team(
        {
            "name": name,
            "max_parallel": parse_max_parallel(max_parallel),
            "agents": list(agents or []),
        }
    )
    _write(team_file(name, home), data)
    return data


def update_team(
    name: str,
    *,
    max_parallel: Optional[int] = None,
    agents: Optional[List[str]] = None,
    home: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    path = team_file(name, home)
    current = _read_yaml(path)
    if current is None:
        return None
    if max_parallel is not None:
        current["max_parallel"] = parse_max_parallel(max_parallel)
    if agents is not None:
        current["agents"] = list(agents)
    clean = _sanitize_team(current)
    _write(path, clean)
    return clean


def delete_team(name: str, home: Optional[Path] = None) -> bool:
    path = team_file(name, home)
    if not path.exists():
        return False
    try:
        path.unlink()
    except OSError:
        return False
    return True
