"""Gateway startup terminal-backend auto-repair (bug-fix round C2).

A stale/useless ``TERMINAL_ENV`` (bad backfill, lost Vercel auth, missing
SDK) strips the terminal/file/execute_code toolsets at boot, so desktop and
gateway processes stay stuck on the broken remote backend. ``start_gateway``
must invoke the same repair the CLI chat path uses, guarded so a probe
failure can never break gateway startup.
"""

from __future__ import annotations

import ast
import inspect

from gateway import run as gateway_run


def test_start_gateway_invokes_terminal_auto_repair():
    """start_gateway must run the terminal-backend repair at startup.

    The config→env bridge only exports ``TERMINAL_ENV`` verbatim; without the
    repair a stale value narrows the toolset for the whole gateway process.
    """
    tree = ast.parse(inspect.getsource(gateway_run))
    found = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "start_gateway":
            calls = {
                n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                for n in ast.walk(node)
                if isinstance(n, ast.Call)
                and isinstance(n.func, (ast.Attribute, ast.Name))
            }
            assert "_auto_repair_terminal_env" in calls, (
                "start_gateway must invoke _auto_repair_terminal_env so "
                "desktop/gateway processes are not stuck on a stale or "
                "unusable TERMINAL_ENV."
            )
            found = True
            break
    assert found, "could not locate start_gateway in gateway/run.py"


def test_auto_repair_terminal_env_swallows_probe_failures(monkeypatch):
    """The auto-repair runs the repair with persist/log_notice defaults and
    never raises even when the underlying repair explodes."""
    calls = []

    def explode(*args, **kwargs):
        calls.append((args, kwargs))
        raise RuntimeError("probe exploded")

    monkeypatch.setattr(
        "synapse_cli.env_detector.ensure_terminal_env_configured", explode
    )

    gateway_run._auto_repair_terminal_env()

    assert len(calls) == 1
    assert calls[0][1] == {"persist": True, "log_notice": False}


def test_auto_repair_terminal_env_invokes_repair(monkeypatch):
    captured = {}

    def fake_repair(*args, **kwargs):
        captured["kwargs"] = kwargs
        return {"fixed": False, "reason": "ok"}

    monkeypatch.setattr(
        "synapse_cli.env_detector.ensure_terminal_env_configured", fake_repair
    )

    gateway_run._auto_repair_terminal_env()

    assert captured["kwargs"] == {"persist": True, "log_notice": False}