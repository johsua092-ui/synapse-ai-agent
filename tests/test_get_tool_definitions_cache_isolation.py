"""Regression tests for issue #17335.

The ``quiet_mode=True`` fast path in :func:`model_tools.get_tool_definitions`
memoizes results to avoid re-walking the registry on every Gateway call. The
cached object must NOT be aliased into callers' return values \u2014 long-lived
Gateway processes mutate the returned list (``run_agent`` appends memory and
LCM context-engine tool schemas to ``self.tools``), and a shared list would
poison subsequent agent inits with duplicate tool names. Providers that
enforce uniqueness (DeepSeek, Xiaomi MiMo, Moonshot/Kimi) then reject the
API call with HTTP 400.

These tests pin:
- the cache-hit path returns a fresh list (existing #17098 behavior)
- the first uncached call also returns a fresh list (the fix)
- every call returns a list that is not the cached one, even after mutation
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

import model_tools


@pytest.fixture(autouse=True)
def _clear_cache():
    """Each test starts with an empty quiet_mode cache."""
    model_tools._tool_defs_cache.clear()
    getattr(model_tools, "_tool_defs_cache_times", {}).clear()
    yield
    model_tools._tool_defs_cache.clear()
    getattr(model_tools, "_tool_defs_cache_times", {}).clear()


class TestQuietModeCacheIsolation:

    def test_first_uncached_call_returns_fresh_list(self):
        """The first quiet_mode call must not alias the cached object \u2014
        otherwise a caller mutating the returned list mutates the cache."""
        first = model_tools.get_tool_definitions(quiet_mode=True)
        assert isinstance(first, list)
        # Find the cached value to compare identity.
        assert len(model_tools._tool_defs_cache) == 1
        cached = next(iter(model_tools._tool_defs_cache.values()))
        assert first is not cached, (
            "issue #17335: first quiet_mode call returned the cached list "
            "by reference \u2014 mutations will leak into subsequent calls."
        )

    def test_cache_hit_returns_fresh_list(self):
        """The cache-hit path already returned a copy pre-fix; pin it."""
        first = model_tools.get_tool_definitions(quiet_mode=True)
        second = model_tools.get_tool_definitions(quiet_mode=True)
        assert first is not second
        cached = next(iter(model_tools._tool_defs_cache.values()))
        assert second is not cached

    def test_cache_recomputes_after_check_fn_ttl(self, monkeypatch):
        """A quiet daemon must re-check tool availability after 30 seconds."""
        now = 100.0
        calls = 0

        def compute(*args, **kwargs):
            nonlocal calls
            calls += 1
            return [{"function": {"name": f"probe_{calls}"}}]

        monkeypatch.setattr(model_tools, "_compute_tool_definitions", compute)
        monkeypatch.setattr(model_tools.time, "monotonic", lambda: now)

        first = model_tools.get_tool_definitions(
            enabled_toolsets=["ttl_probe"], quiet_mode=True,
        )
        now += 29.0
        cached = model_tools.get_tool_definitions(
            enabled_toolsets=["ttl_probe"], quiet_mode=True,
        )
        now += 2.0
        refreshed = model_tools.get_tool_definitions(
            enabled_toolsets=["ttl_probe"], quiet_mode=True,
        )

        assert first == cached
        assert refreshed != cached
        assert calls == 2



    def test_defs_cache_evicted_when_check_fn_verdict_invalidated(self):
        """B1: invalidation must evict the memoized defs cache so the next
        definitions call is rebuilt under a fresh verdict, not served from the
        pre-invalidation entry (which may have stripped tools on a transient
        check_fn failure baked into a long-lived quiet daemon)."""
        from tools import registry

        model_tools.get_tool_definitions(quiet_mode=True)
        assert len(model_tools._tool_defs_cache) == 1
        before_key = next(iter(model_tools._tool_defs_cache))

        registry.invalidate_check_fn_cache()

        model_tools.get_tool_definitions(quiet_mode=True)
        assert len(model_tools._tool_defs_cache) == 1
        after_key = next(iter(model_tools._tool_defs_cache))
        assert after_key != before_key, (
            "issue B1: next definitions call was served from the "
            "pre-invalidation cache entry instead of being rebuilt"
        )

    def test_cache_bounded_by_eviction(self):
        """The cache evicts the oldest entry when it reaches the cap,
        keeping the cache bounded instead of growing unbounded over a
        long-lived Gateway's lifetime (#19251)."""
        cap = model_tools._TOOL_DEFS_CACHE_MAX
        # Fill cache to the cap with distinct keys by varying enabled_toolsets.
        for i in range(cap):
            model_tools.get_tool_definitions(
                enabled_toolsets=[f"fake_toolset_{i}"], quiet_mode=True,
            )
        assert len(model_tools._tool_defs_cache) == cap

        # Adding one more must evict the oldest, not clear everything and
        # not grow past the cap.
        model_tools.get_tool_definitions(
            enabled_toolsets=["fake_toolset_overflow"], quiet_mode=True,
        )
        assert len(model_tools._tool_defs_cache) == cap, (
            "Eviction should keep the cache at the cap, not clear it or grow"
        )

    def test_non_quiet_mode_does_not_use_cache(self):
        """Sanity: quiet_mode=False (TUI path) skips the cache entirely \u2014
        explains why the bug only hit Gateway."""
        model_tools.get_tool_definitions(quiet_mode=False)
        assert len(model_tools._tool_defs_cache) == 0

    def test_concurrent_capacity_misses_evict_atomically(self, monkeypatch):
        """Two profile/toolset misses at capacity cannot race on eviction."""
        barrier = Barrier(2)

        def compute(*args, **kwargs):
            barrier.wait(timeout=2)
            return []

        monkeypatch.setattr(model_tools, "_compute_tool_definitions", compute)
        for index in range(model_tools._TOOL_DEFS_CACHE_MAX):
            model_tools._tool_defs_cache[("old", index)] = []

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(
                    model_tools.get_tool_definitions,
                    enabled_toolsets=[f"concurrent_{index}"],
                    quiet_mode=True,
                )
                for index in range(2)
            ]
            assert [future.result(timeout=2) for future in futures] == [[], []]

        assert len(model_tools._tool_defs_cache) == model_tools._TOOL_DEFS_CACHE_MAX
