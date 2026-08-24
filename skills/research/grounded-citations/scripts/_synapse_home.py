"""Resolve SYNAPSE_HOME for standalone skill scripts.

Skill scripts may run outside the Synapse process (system Python, nix env,
CI) where ``synapse_constants`` is not importable.  This module provides the
same ``get_synapse_home()`` contract without requiring it on ``sys.path``.

When ``synapse_constants`` IS available it is used directly so profile
resolution and any future enhancements are picked up automatically.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from synapse_constants import get_synapse_home as get_synapse_home
except (ModuleNotFoundError, ImportError):

    def get_synapse_home() -> Path:
        """Return the Synapse home directory (default: ``~/.synapse``)."""
        val = os.environ.get("SYNAPSE_HOME", "").strip()
        return Path(val) if val else Path.home() / ".synapse"
