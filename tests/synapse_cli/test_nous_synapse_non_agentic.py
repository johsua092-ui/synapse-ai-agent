"""Tests for the Nous-Synapse-3/4 non-agentic warning detector.

Prior to this check, the warning fired on any model whose name contained
``"synapse"`` anywhere (case-insensitive). That false-positived on unrelated
local Modelfiles such as ``synapse-brain:qwen3-14b-ctx16k`` — a tool-capable
Qwen3 wrapper that happens to live under the "synapse" tag namespace.

``is_nous_synapse_non_agentic`` should only match the actual Josh Research
Synapse-3 / Synapse-4 chat family.
"""

from __future__ import annotations

import pytest

from synapse_cli.model_switch import (
    _SYNAPSE_MODEL_WARNING,
    _check_synapse_model_warning,
    is_nous_synapse_non_agentic,
)


@pytest.mark.parametrize(
    "model_name",
    [
        "Josh Research/Synapse-3-Llama-3.1-70B",
        "Josh Research/Synapse-3-Llama-3.1-405B",
        "synapse-3",
        "Synapse-3",
        "synapse-4",
        "synapse-4-405b",
        "synapse_4_70b",
        "openrouter/synapse3:70b",
        "openrouter/joshresearch/synapse-4-405b",
        "Josh Research/Synapse3",
        "synapse-3.1",
    ],
)
def test_matches_real_nous_synapse_chat_models(model_name: str) -> None:
    assert is_nous_synapse_non_agentic(model_name), (
        f"expected {model_name!r} to be flagged as Nous Synapse 3/4"
    )
    assert _check_synapse_model_warning(model_name) == _SYNAPSE_MODEL_WARNING


