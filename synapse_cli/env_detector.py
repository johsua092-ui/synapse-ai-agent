"""Terminal environment auto-detection.

Detects whether the current machine is best served by the ``local`` or
``docker`` terminal backend, and repairs a missing / invalid configured
``TERMINAL_ENV`` / ``terminal.backend`` so the terminal + file toolsets are
never silently stripped at runtime (see "Tool terminal does not exist").

Design

* Detection is conservative: only ``docker`` (running inside a container where
  a usable Docker runtime is present) is ever chosen over ``local``.  A plain
  laptop/desktop, a VPS shell, WSL and Termux all map to ``local`` — their own
  shell *is* the terminal.  The remote backends (``ssh``, ``modal``,
  ``daytona``, ``vercel_sandbox``, ``singularity``) are always explicit user
  choices and are never overridden here.
* Repair is conservative too: an explicitly configured *usable* backend is
  left alone; only a missing, unrecognized, or unusable-on-this-machine value
  is replaced with the detected one.  A backend that is merely *known* but
  cannot run here (e.g. ``vercel_sandbox`` left behind by a stale backfill)
  used to strip the whole terminal/file toolset at boot, so it is repaired
  rather than respected.
* Runs in library context (startup / post-update), so it must not print to
  stdout or call ``sys.exit``.  It writes config.yaml via the raw read +
  ``atomic_yaml_write`` round-trip (preserving user structure) and mirrors
  ``TERMINAL_ENV`` to ``~/.synapse/.env`` + ``os.environ``.
"""

from __future__ import annotations

import logging
import os
import shutil
from typing import Any, Dict, Optional

from synapse_constants import is_container, is_termux

logger = logging.getLogger(__name__)

# Mirrors tools.terminal_tool._KNOWN_TERMINAL_ENVS. Kept separate here
# (non-import) so startup code can load this module without dragging in the
# heavy terminal_tool dependency tree.
KNOWN_BACKENDS = frozenset(
    {"local", "docker", "singularity", "modal", "daytona", "vercel_sandbox", "ssh"}
)


def _docker_runtime_usable() -> bool:
    """Return True when a Docker runtime looks reachable from this process.

    Checks (in order): an explicit ``DOCKER_HOST`` env var, a Unix socket at
    the standard path, and a ``docker`` binary on ``PATH``.  Any one is enough
    — but only when we are actually inside a container; callers gate on
    :func:`is_container` first.
    """
    if os.environ.get("DOCKER_HOST"):
        return True
    if os.path.exists("/var/run/docker.sock"):
        return True
    return shutil.which("docker") is not None


def detect_terminal_backend() -> str:
    """Return the best automatic ``terminal.backend`` for this machine.

    ``docker`` when running inside a container with a usable Docker runtime,
    otherwise ``local``.  Never returns a remote backend — those are explicit
    user choices.
    """
    if is_termux():
        return "local"
    if is_container():
        return "docker" if _docker_runtime_usable() else "local"
    return "local"


def _read_config_backend() -> Optional[str]:
    """Return the ``terminal.backend`` explicitly written in config.yaml."""
    from synapse_cli.config import read_user_config_raw

    try:
        raw = read_user_config_raw()
    except Exception:
        logger.debug("env_detector: config read failed", exc_info=True)
        return None
    terminal = raw.get("terminal")
    if not isinstance(terminal, dict):
        return None
    backend = terminal.get("backend")
    if isinstance(backend, str) and backend:
        return backend.strip().lower()
    return None


def current_effective_backend() -> Optional[str]:
    """Resolve today's effective backend: explicit config wins, else env.

    Mirrors the bridge in ``_ensure_terminal_env_bridged`` (config.yaml
    ``terminal.backend`` is authoritative when explicitly present), but reads
    the ``TERMINAL_ENV`` env var for the fallback instead of the merged
    defaults — this module must not guess a value the user never set.
    """
    from_config = _read_config_backend()
    if from_config is not None:
        return from_config
    env_value = os.environ.get("TERMINAL_ENV")
    if env_value:
        return env_value.strip().lower()
    return None


def _persist_backend(backend: str) -> bool:
    """Persist ``terminal.backend`` to config.yaml + ``TERMINAL_ENV`` to .env.

    Config write uses the raw-round-trip (key-only, structure-preserving)
    pattern; the .env mirror keeps terminal_tool's env-driven readers in sync.
    Returns True when the config.yaml write succeeded.
    """
    from synapse_cli.config import get_config_path, read_user_config_raw, save_env_value

    try:
        raw = read_user_config_raw()
        if not isinstance(raw.get("terminal"), dict):
            raw["terminal"] = {}
        raw["terminal"]["backend"] = backend
        from utils import atomic_yaml_write

        atomic_yaml_write(get_config_path(), raw)
    except Exception:
        logger.warning("env_detector: could not write terminal.backend to config.yaml", exc_info=True)
        return False

    try:
        save_env_value("TERMINAL_ENV", backend)
    except Exception:
        logger.warning("env_detector: could not mirror TERMINAL_ENV to .env", exc_info=True)
    if os.environ.get("TERMINAL_ENV") != backend:
        os.environ["TERMINAL_ENV"] = backend
    return True


def _explicit_backend_usable(backend: str) -> bool:
    """Return True when an explicitly configured *backend* can actually run.

    Uses the SAME check the runtime uses (``tools.terminal_tool.
    check_terminal_requirements``) so a backend that is merely *known* but not
    usable on this machine (e.g. ``vercel_sandbox`` left behind by a stale
    backfill with no Vercel auth, or ``ssh``/``docker`` without working
    credentials) is repaired at startup instead of silently stripping the
    terminal + file + execute_code toolsets ("Tool terminal does not exist").
    ``local`` is always usable.  The import is deferred so this module stays
    importable from startup paths that must stay light.
    """
    if backend == "local":
        return True
    try:
        # Probe against the CURRENT config.yaml on disk.  terminal_tool bridges
        # config -> env only ONCE per process (`_terminal_config_bridge_attempted`),
        # so in a long-lived daemon the check could otherwise see a stale env
        # (e.g. "local") from an earlier run and mis-report this backend as
        # usable.  Temporarily clear the flag, probe, then restore it.
        import tools.terminal_tool as _terminal_tool

        _prev_bridged = _terminal_tool._terminal_config_bridge_attempted
        _terminal_tool._terminal_config_bridge_attempted = False
        try:
            return bool(_terminal_tool.check_terminal_requirements())
        finally:
            _terminal_tool._terminal_config_bridge_attempted = _prev_bridged
    except Exception:
        logger.warning(
            "env_detector: could not verify backend %r; treating as unusable",
            backend,
            exc_info=True,
        )
        return False


def ensure_terminal_env_configured(*, persist: bool = True, log_notice: bool = True) -> Dict[str, Any]:
    """Repair a missing / invalid terminal backend for this machine.

    Returns a result dict describing what happened::

        {"detected": "docker"|"local",
         "current":  <effective backend or None>,
         "fixed":    bool,          # True when a value was written
         "reason":   "missing" | "invalid" | "unusable" | "mismatch" | "ok"}

    * ``current`` invalid (not in KNOWN_BACKENDS) or missing → detected value
      is written (missing is written so the configured truth is explicit).
    * ``current`` valid but unusable on this machine (the runtime requirements
      check fails — e.g. ``vercel_sandbox`` with no auth, ``ssh`` without
      host/user) → repaired to the detected value; a broken backend would
      otherwise strip the terminal + file + execute_code toolsets at boot.
    * ``current`` usable but differs from detected → left alone unless it is
      the docker-in-container case (a fresh container deployment has no reason
      to run the local backend); everything else stays untouched.
    * ``current`` == detected → no-op.

    Never prints to stdout and never raises; failures are logged and reported
    via the result dict.
    """
    detected = detect_terminal_backend()
    current = current_effective_backend()

    if current is None:
        reason = "missing"
    elif current not in KNOWN_BACKENDS:
        reason = "invalid"
    elif current == detected:
        reason = "ok"
        return {
            "detected": detected,
            "current": current,
            "fixed": False,
            "reason": "ok",
        }
    elif detected == "docker":
        # A fresh docker deployment: the container runtime is available and
        # there's no reason for an explicit-but-different backend we should
        # preserve.  (Remote/ssh backends aren't produced by detection, so the
        # only mismatch that can round-trip is local↔docker by design.)
        reason = "mismatch"
    else:
        # Valid explicit backend that differs from our auto-detect: respect the
        # user's configured choice ONLY when it actually works on this machine
        # (e.g. a real ssh/modal/vercel setup).  A known-but-broken backend —
        # stale backfill, lost credentials — would otherwise strip the whole
        # terminal + file + execute_code toolset at boot, so repair it to the
        # detected backend instead.
        if _explicit_backend_usable(current):
            return {
                "detected": detected,
                "current": current,
                "fixed": False,
                "reason": "ok",
            }
        reason = "unusable"

    if persist:
        fixed = _persist_backend(detected)
    else:
        fixed = False
        if os.environ.get("TERMINAL_ENV") != detected:
            os.environ["TERMINAL_ENV"] = detected

    if fixed and log_notice:
        logger.info(
            "env_detector: terminal backend %r (%r) → %r",
            reason,
            current,
            detected,
        )
    return {
        "detected": detected,
        "current": current,
        "fixed": fixed,
        "reason": reason,
    }