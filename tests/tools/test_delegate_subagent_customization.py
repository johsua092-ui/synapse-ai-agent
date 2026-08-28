"""Tests for per-call subagent customization: assigned skills, toolsets, and model.

Layer 1 of the subagent/agent-team feature. These tests target the pure seams in
tools/delegate_tool.py so they run without spawning real agents or depending on
installed skills:

- ``_build_child_system_prompt`` embeds the preloaded-skills block when ``skills``
  are assigned (reusing the existing skill loader).
- ``_build_child_agent`` accepts a ``skills`` list and passes it through; its
  ``toolsets`` / ``model`` params already exist and are surfaced by the caller.
- ``delegate_task`` accepts ``skills`` / ``toolsets`` / ``model`` arguments.
"""

from types import SimpleNamespace

import pytest


SKILL_TEXT = ("[preloaded-design-skill]\nuse-color-ramp-step-4: true\n")


@pytest.fixture(autouse=True)
def _fake_skill_loader(monkeypatch):
    """Stub build_preloaded_skills_prompt so tests are IO-free and deterministic."""
    import agent.skill_commands

    def fake_build(skill_identifiers, task_id=None):
        return (
            SKILL_TEXT + f"Loaded skills: {sorted(skill_identifiers)}",
            sorted(skill_identifiers),
            [],
        )

    monkeypatch.setattr(
        agent.skill_commands, "build_preloaded_skills_prompt", fake_build
    )


def _child_prompt(**overrides):
    from tools.delegate_tool import _build_child_system_prompt

    kwargs = dict(goal="Audit the auth module", role="leaf")
    kwargs.update(overrides)
    return _build_child_system_prompt(**kwargs)


class TestSkillAssignment:
    def test_no_skills_means_no_skill_block(self):
        from tools.delegate_tool import _build_child_system_prompt

        out = _build_child_system_prompt(goal="ghi", role="leaf")
        assert "preloaded" not in out.lower()
        assert "Loaded skills" not in out

    def test_skills_embed_preloaded_skill_text(self):
        out = _child_prompt(skills=["design"])
        assert SKILL_TEXT in out
        assert "design" in out

    def test_multiple_skills_all_embedded(self):
        out = _child_prompt(skills=["design", "security"])
        assert "design" in out
        assert "security" in out

    def test_skill_block_keeps_task_first(self):
        out = _child_prompt(skills=["security"])
        assert out.startswith("You are a focused subagent")
        assert "YOUR TASK" in out


class TestChildAgentParamThreading:
    def test_build_child_agent_accepts_skills(self):
        import inspect

        from tools.delegate_tool import _build_child_agent

        params = inspect.signature(_build_child_agent).parameters
        assert "skills" in params

    def test_build_child_agent_accepts_toolsets_and_model(self):
        import inspect

        from tools.delegate_tool import _build_child_agent

        params = inspect.signature(_build_child_agent).parameters
        assert "toolsets" in params
        assert "model" in params

    def test_child_system_prompt_receives_skills(self, monkeypatch):
        """_build_child_agent must hand the skills list to _build_child_system_prompt."""
        import tools.delegate_tool as dt

        captured = {}

        def fake_child_prompt(goal, context, **kw):
            captured["skills"] = kw.get("skills")
            return "child-prompt"

        monkeypatch.setattr(dt, "_build_child_system_prompt", fake_child_prompt)

        parent = SimpleNamespace(
            _delegate_depth=0,
            enabled_toolsets=["terminal"],
            model="parent-model",
            api_key="k",
            provider="p",
            base_url="http://x",
            api_mode="chat_completions",
            session_id="s",
            _safe_print=None,
            _print_fn=None,
            _client_kwargs={},
            prefill_messages=[],
            reasoning_config=None,
            request_overrides={},
        )
        parent.enabled_toolsets = ["terminal"]

        dt._build_child_agent(
            task_index=0,
            goal="g",
            context=None,
            toolsets=["terminal"],
            model="parent-model",
            max_iterations=5,
            task_count=1,
            parent_agent=parent,
            skills=["security"],
        )
        assert captured.get("skills") == ["security"]


class TestDelegateTaskSchema:
    def test_delegate_task_accepts_skills_toolsets_model(self):
        import inspect

        from tools.delegate_tool import delegate_task

        params = inspect.signature(delegate_task).parameters
        assert "skills" in params
        assert "toolsets" in params
        assert "model" in params
