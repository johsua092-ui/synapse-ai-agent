"""Stale-dist fallback behavior in the web UI build path.

Two regressions locked down here:

- D1: with ``fatal=True`` a failed build + stale dist must return ``False``
  so the caller's ``sys.exit(1)`` fires instead of silently serving an
  outdated UI. With ``fatal=False`` the stale UI may be served as a fallback,
  but only after ``SYNAPSE_STALE_BUILD=1`` is set so ``_serve_index`` can
  surface the staleness to the SPA.
- D2: a leftover dist is a usable stale fallback only when it is a complete
  Vite build (``index.html`` + ``.vite/manifest.json``, or a non-empty
  ``assets/``). A half-written build (``emptyOutDir`` already ran but no
  assets/manifest written) must never be served.
"""

import os
from pathlib import Path
from unittest.mock import patch


def _make_web_dir(tmp_path: Path) -> tuple[Path, Path]:
    """Return (web_dir, dist_dir) matching real repo layout."""
    web_dir = tmp_path / "web"
    web_dir.mkdir(parents=True)
    (web_dir / "package.json").touch()
    dist_dir = tmp_path / "synapse_cli" / "web_dist"
    return web_dir, dist_dir


def _make_stale_dist(dist_dir: Path, *, complete: bool = True) -> None:
    dist_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("<html>stale</html>", encoding="utf-8")
    if complete:
        (dist_dir / ".vite").mkdir(parents=True)
        (dist_dir / ".vite" / "manifest.json").write_text("{}", encoding="utf-8")


def _failing_build_run() -> tuple:
    import subprocess as _subprocess

    install_ok = _subprocess.CompletedProcess([], 0, stdout="", stderr="")
    build_fail = _subprocess.CompletedProcess([], 1, stdout="vite ENOMEM", stderr="")
    return install_ok, build_fail


def _patch_failing_build(install_ok, build_fail):
    from contextlib import ExitStack

    stack = ExitStack()
    stack.enter_context(
        patch("synapse_cli.main._resolve_node_runtime_npm", return_value="/usr/bin/npm")
    )
    stack.enter_context(patch("synapse_cli.main._time.sleep"))
    stack.enter_context(
        patch("synapse_cli.main._run_npm_install_deterministic", return_value=install_ok)
    )
    stack.enter_context(
        patch("synapse_cli.main._run_with_idle_timeout", return_value=build_fail)
    )
    return stack


class TestFatalBuildFailureNotSwallowedByStaleDist:
    def test_fatal_build_failure_not_swallowed_by_complete_stale_dist(
        self, tmp_path, monkeypatch, capsys
    ):
        from synapse_cli.main import _build_web_ui

        web_dir, dist_dir = _make_web_dir(tmp_path)
        _make_stale_dist(dist_dir, complete=True)
        monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / "_home"))
        monkeypatch.delenv("TERMUX_VERSION", raising=False)
        monkeypatch.setenv("PREFIX", "/usr")
        monkeypatch.delenv("SYNAPSE_STALE_BUILD", raising=False)
        install_ok, build_fail = _failing_build_run()
        with _patch_failing_build(install_ok, build_fail):
            result = _build_web_ui(web_dir, fatal=True)

        assert result is False
        assert "Web UI build failed" in capsys.readouterr().out

    def test_fatal_build_failure_not_swallowed_by_incomplete_stale_dist(
        self, tmp_path, monkeypatch
    ):
        from synapse_cli.main import _build_web_ui

        web_dir, dist_dir = _make_web_dir(tmp_path)
        _make_stale_dist(dist_dir, complete=False)
        monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / "_home"))
        monkeypatch.delenv("TERMUX_VERSION", raising=False)
        monkeypatch.setenv("PREFIX", "/usr")
        monkeypatch.delenv("SYNAPSE_STALE_BUILD", raising=False)
        install_ok, build_fail = _failing_build_run()
        with _patch_failing_build(install_ok, build_fail):
            result = _build_web_ui(web_dir, fatal=True)

        assert result is False


class TestNonFatalStaleFallback:
    def test_nonfatal_complete_stale_dist_served_with_marker(self, tmp_path, monkeypatch, capsys):
        from synapse_cli.main import _build_web_ui

        web_dir, dist_dir = _make_web_dir(tmp_path)
        _make_stale_dist(dist_dir, complete=True)
        monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / "_home"))
        monkeypatch.delenv("TERMUX_VERSION", raising=False)
        monkeypatch.setenv("PREFIX", "/usr")
        monkeypatch.delenv("SYNAPSE_STALE_BUILD", raising=False)
        install_ok, build_fail = _failing_build_run()
        with _patch_failing_build(install_ok, build_fail):
            result = _build_web_ui(web_dir, fatal=False)

        assert result is True
        assert os.environ.get("SYNAPSE_STALE_BUILD") == "1"
        assert "serving stale dist as fallback" in capsys.readouterr().out

    def test_nonfatal_incomplete_dist_not_served(self, tmp_path, monkeypatch, capsys):
        from synapse_cli.main import _build_web_ui

        web_dir, dist_dir = _make_web_dir(tmp_path)
        _make_stale_dist(dist_dir, complete=False)
        monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / "_home"))
        monkeypatch.delenv("TERMUX_VERSION", raising=False)
        monkeypatch.setenv("PREFIX", "/usr")
        monkeypatch.delenv("SYNAPSE_STALE_BUILD", raising=False)
        install_ok, build_fail = _failing_build_run()
        with _patch_failing_build(install_ok, build_fail):
            result = _build_web_ui(web_dir, fatal=False)

        assert result is False
        assert "SYNAPSE_STALE_BUILD" not in os.environ
        assert "incomplete" in capsys.readouterr().out


class TestStaleDistUsable:
    def test_accepts_complete_manifest_build(self, tmp_path):
        from synapse_cli.main import _build_stale_dist_usable

        dist = tmp_path / "dist"
        (dist / ".vite").mkdir(parents=True)
        (dist / ".vite" / "manifest.json").write_text("{}", encoding="utf-8")
        (dist / "index.html").write_text("<html>ok</html>", encoding="utf-8")
        assert _build_stale_dist_usable(str(dist)) is True

    def test_accepts_nonempty_assets_fallback(self, tmp_path):
        from synapse_cli.main import _build_stale_dist_usable

        dist = tmp_path / "dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "assets" / "app.js").write_text("x", encoding="utf-8")
        (dist / "index.html").write_text("<html>ok</html>", encoding="utf-8")
        assert _build_stale_dist_usable(str(dist)) is True

    def test_rejects_incomplete_dist_without_manifest_or_assets(self, tmp_path):
        from synapse_cli.main import _build_stale_dist_usable

        dist = tmp_path / "dist"
        dist.mkdir(parents=True)
        (dist / "index.html").write_text("<html>half</html>", encoding="utf-8")
        assert _build_stale_dist_usable(str(dist)) is False

    def test_rejects_empty_assets_dir(self, tmp_path):
        from synapse_cli.main import _build_stale_dist_usable

        dist = tmp_path / "dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text("<html>half</html>", encoding="utf-8")
        assert _build_stale_dist_usable(str(dist)) is False

    def test_rejects_missing_index_html(self, tmp_path):
        from synapse_cli.main import _build_stale_dist_usable

        dist = tmp_path / "dist"
        (dist / ".vite").mkdir(parents=True)
        (dist / ".vite" / "manifest.json").write_text("{}", encoding="utf-8")
        assert _build_stale_dist_usable(str(dist)) is False


class TestServeIndexStaleMarker:
    def _client(self, tmp_path, monkeypatch):
        from fastapi import FastAPI
        from starlette.testclient import TestClient
        import synapse_cli.web_server as ws

        dist = tmp_path / "web_dist"
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text(
            "<html><head><title>t</title></head><body>SPA</body></html>",
            encoding="utf-8",
        )
        monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
        monkeypatch.setenv("SYNAPSE_SERVE_HEADLESS", "")
        monkeypatch.delenv("SYNAPSE_SERVE_HEADLESS", raising=False)
        monkeypatch.setattr(ws, "WEB_DIST", dist)
        spa_app = FastAPI()
        ws.mount_spa(spa_app)
        return TestClient(spa_app)

    def test_injects_stale_marker_when_flag_set(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SYNAPSE_STALE_BUILD", "1")
        resp = self._client(tmp_path, monkeypatch).get("/chat")
        assert resp.status_code == 200
        assert "window.__SYNAPSE_STALE_BUILD__=true;" in resp.text
        head = resp.text.split("</head>")[0]
        assert "window.__SYNAPSE_STALE_BUILD__=true;" in head

    def test_no_marker_when_flag_unset(self, tmp_path, monkeypatch):
        import synapse_cli.web_server as ws

        monkeypatch.delenv("SYNAPSE_STALE_BUILD", raising=False)
        resp = self._client(tmp_path, monkeypatch).get("/chat")
        assert resp.status_code == 200
        assert "window.__SYNAPSE_STALE_BUILD__" not in resp.text


class TestSuccessClearsStaleMarker:
    """M6: a successful rebuild in the same process must stop injecting the
    stale marker, so a UI repaired after a stale fallback is no longer
    marketed as stale."""

    def test_successful_rebuild_clears_stale_marker(self, tmp_path, monkeypatch):
        import subprocess

        from synapse_cli.main import _build_web_ui

        web_dir, dist_dir = _make_web_dir(tmp_path)
        monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path / "_home"))
        monkeypatch.setenv("SYNAPSE_STALE_BUILD", "1")
        monkeypatch.delenv("TERMUX_VERSION", raising=False)
        monkeypatch.setenv("PREFIX", "/usr")

        install_ok = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        build_ok = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with patch("synapse_cli.main.shutil.which", return_value="/usr/bin/npm"), \
             patch("synapse_cli.main._time.sleep"), \
             patch("synapse_cli.main.subprocess.run", return_value=install_ok), \
             patch("synapse_cli.main._run_with_idle_timeout", return_value=build_ok):
            result = _build_web_ui(web_dir)

        assert result is True
        assert "SYNAPSE_STALE_BUILD" not in os.environ
