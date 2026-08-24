"""Resolve SYNAPSE_HOME for standalone skill scripts.

Skill scripts may run outside the Synapse process (e.g. system Python,
nix env, CI) where ``synapse_constants`` is not importable.  This module
provides the same ``get_synapse_home()`` and ``display_synapse_home()``
contracts as ``synapse_constants`` without requiring it on ``sys.path``.

When ``synapse_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``synapse_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``SYNAPSE_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from synapse_constants import display_synapse_home as display_synapse_home
    from synapse_constants import get_synapse_home as get_synapse_home
except (ModuleNotFoundError, ImportError):

    def get_synapse_home() -> Path:
        """Return the Synapse home directory (default: ~/.synapse).

        Mirrors ``synapse_constants.get_synapse_home()``."""
        val = os.environ.get("SYNAPSE_HOME", "").strip()
        return Path(val) if val else Path.home() / ".synapse"

    def display_synapse_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``synapse_constants.display_synapse_home()``."""
        home = get_synapse_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
