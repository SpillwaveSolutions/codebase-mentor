"""Unit tests for _collect_failure_artifacts() helper.

Exercises the failure artifact bundle logic with synthetic data — no external
CLIs (opencode, rulez, claude) required. Verifies that the helper produces
the expected directory structure, FAILURE_REPORT.md, config snapshots,
diagnostics file, directory tree, and compressed tarball.

Run:  pytest tests/integration/test_failure_artifacts.py -v
      (these are fast tests, NOT marked @slow)

IMPORTANT: This test proves the artifact collection code path works.
The live OpenCode e2e test (test_agent_rulez_opencode_capture_to_export)
calls this same helper on real failures but requires opencode CLI.
"""

import json
import tarfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tests.integration.test_agent_rulez_e2e import _collect_failure_artifacts


@pytest.fixture
def synthetic_project(tmp_path):
    """Create a minimal project directory matching what the e2e test would produce."""
    project = tmp_path / "project"
    project.mkdir()

    # .claude/ config files
    claude_dir = project / ".claude"
    claude_dir.mkdir()
    (claude_dir / "hooks.yaml").write_text("rules:\n  - name: block-force-push\n")
    (claude_dir / "settings.json").write_text('{"permissions": {}}')

    # .code-wizard/ with session and docs
    cw = project / ".code-wizard"
    (cw / "sessions").mkdir(parents=True)
    (cw / "docs" / "test-session-001").mkdir(parents=True)
    (cw / "scripts").mkdir(parents=True)
    (cw / "config.json").write_text('{"resolved_storage": ".code-wizard"}')
    (cw / "scripts" / "capture-session.sh").write_text("#!/bin/bash\necho capture")
    (cw / "sessions" / "test-session.json").write_text(
        json.dumps([{"turn": 1, "question": "What does this do?"}])
    )
    (cw / "docs" / "test-session-001" / "SESSION-TRANSCRIPT.md").write_text(
        "# Session Transcript\n\nPartial output before failure.\n"
    )

    # .opencode/ config
    opencode_dir = project / ".opencode"
    opencode_dir.mkdir()
    (opencode_dir / "opencode.json").write_text('{"model": "test"}')

    # Source files
    src = project / "src"
    src.mkdir()
    (src / "main.py").write_text("def calculate(a, b): return a + b\n")
    (project / "README.md").write_text("# Test Project\n")

    return project


@pytest.fixture
def synthetic_env(tmp_path, synthetic_project):
    """Create the env dict that matches integration_env / opencode_integration_env."""
    home = tmp_path / "home"
    home.mkdir()
    return {
        "home": home,
        "project": synthetic_project,
        "setup_sh": Path("/fake/setup.sh"),
        "plugin_dir": Path("/fake/plugin"),
    }


@pytest.fixture
def synthetic_subprocess_results():
    """Fake subprocess results from setup/wizard/export steps."""
    return {
        "setup": SimpleNamespace(returncode=0, stdout="Setup OK\n", stderr=""),
        "wizard": SimpleNamespace(returncode=1, stdout="Wizard started\n", stderr="Error: timeout\n"),
        "export": None,  # never reached
    }


def test_collect_failure_artifacts_produces_report(
    tmp_path, synthetic_project, synthetic_env, synthetic_subprocess_results
):
    """Verify FAILURE_REPORT.md is generated with expected sections."""
    error = AssertionError("wizard session produced no turns")

    with patch(
        "tests.integration.test_agent_rulez_e2e.REPO_ROOT", tmp_path
    ):
        _collect_failure_artifacts(
            synthetic_project,
            synthetic_env,
            "opencode",
            synthetic_subprocess_results,
            error,
        )

    # Find the artifact directory
    artifacts_dir = tmp_path / "artifacts"
    assert artifacts_dir.exists(), "artifacts/ directory was not created"

    bundle_dirs = [d for d in artifacts_dir.iterdir() if d.is_dir()]
    assert len(bundle_dirs) == 1, f"Expected 1 bundle dir, got {len(bundle_dirs)}"
    bundle = bundle_dirs[0]

    # FAILURE_REPORT.md
    report = bundle / "FAILURE_REPORT.md"
    assert report.exists(), "FAILURE_REPORT.md not created"
    report_text = report.read_text()
    assert "wizard session produced no turns" in report_text
    assert "test_agent_rulez_opencode_capture_to_export" in report_text
    assert "setup: rc=0" in report_text
    assert "wizard: rc=1" in report_text
    assert "export: rc=N/A" in report_text


def test_collect_failure_artifacts_copies_configs(
    tmp_path, synthetic_project, synthetic_env, synthetic_subprocess_results
):
    """Verify config files are copied into the bundle."""
    error = AssertionError("test error")

    with patch(
        "tests.integration.test_agent_rulez_e2e.REPO_ROOT", tmp_path
    ):
        _collect_failure_artifacts(
            synthetic_project,
            synthetic_env,
            "opencode",
            synthetic_subprocess_results,
            error,
        )

    bundle = next(d for d in (tmp_path / "artifacts").iterdir() if d.is_dir())
    config_dir = bundle / "config-files"
    assert config_dir.exists()
    assert (config_dir / "hooks.yaml").exists()
    assert (config_dir / "settings.json").exists()
    assert (config_dir / "config.json").exists()
    assert (config_dir / "capture-session.sh").exists()
    assert (config_dir / ".opencode").exists()


def test_collect_failure_artifacts_copies_sessions(
    tmp_path, synthetic_project, synthetic_env, synthetic_subprocess_results
):
    """Verify session and docs directories are copied."""
    error = AssertionError("test error")

    with patch(
        "tests.integration.test_agent_rulez_e2e.REPO_ROOT", tmp_path
    ):
        _collect_failure_artifacts(
            synthetic_project,
            synthetic_env,
            "opencode",
            synthetic_subprocess_results,
            error,
        )

    bundle = next(d for d in (tmp_path / "artifacts").iterdir() if d.is_dir())
    assert (bundle / "sessions" / "test-session.json").exists()
    assert (bundle / "docs" / "test-session-001" / "SESSION-TRANSCRIPT.md").exists()


def test_collect_failure_artifacts_creates_tarball(
    tmp_path, synthetic_project, synthetic_env, synthetic_subprocess_results
):
    """Verify .tar.gz archive is created and contains FAILURE_REPORT.md."""
    error = AssertionError("test error")

    with patch(
        "tests.integration.test_agent_rulez_e2e.REPO_ROOT", tmp_path
    ):
        _collect_failure_artifacts(
            synthetic_project,
            synthetic_env,
            "opencode",
            synthetic_subprocess_results,
            error,
        )

    tarballs = list((tmp_path / "artifacts").glob("*.tar.gz"))
    assert len(tarballs) == 1, f"Expected 1 tarball, got {len(tarballs)}"

    with tarfile.open(str(tarballs[0]), "r:gz") as tar:
        names = tar.getnames()
        assert any("FAILURE_REPORT.md" in n for n in names), (
            f"FAILURE_REPORT.md not in tarball. Contents: {names}"
        )


def test_collect_failure_artifacts_creates_dir_tree(
    tmp_path, synthetic_project, synthetic_env, synthetic_subprocess_results
):
    """Verify directory tree file is generated."""
    error = AssertionError("test error")

    with patch(
        "tests.integration.test_agent_rulez_e2e.REPO_ROOT", tmp_path
    ):
        _collect_failure_artifacts(
            synthetic_project,
            synthetic_env,
            "opencode",
            synthetic_subprocess_results,
            error,
        )

    bundle = next(d for d in (tmp_path / "artifacts").iterdir() if d.is_dir())
    tree_file = bundle / "dir-tree.txt"
    assert tree_file.exists()
    tree_text = tree_file.read_text()
    assert "main.py" in tree_text
    assert "hooks.yaml" in tree_text


def test_collect_failure_artifacts_subprocess_results_file(
    tmp_path, synthetic_project, synthetic_env, synthetic_subprocess_results
):
    """Verify subprocess results are written."""
    error = AssertionError("test error")

    with patch(
        "tests.integration.test_agent_rulez_e2e.REPO_ROOT", tmp_path
    ):
        _collect_failure_artifacts(
            synthetic_project,
            synthetic_env,
            "opencode",
            synthetic_subprocess_results,
            error,
        )

    bundle = next(d for d in (tmp_path / "artifacts").iterdir() if d.is_dir())
    results_file = bundle / "subprocess-results.txt"
    assert results_file.exists()
    text = results_file.read_text()
    assert "Setup OK" in text
    assert "Error: timeout" in text
    assert "(not run)" in text  # export was None


def test_collect_failure_artifacts_project_snapshot(
    tmp_path, synthetic_project, synthetic_env, synthetic_subprocess_results
):
    """Verify full project snapshot is copied."""
    error = AssertionError("test error")

    with patch(
        "tests.integration.test_agent_rulez_e2e.REPO_ROOT", tmp_path
    ):
        _collect_failure_artifacts(
            synthetic_project,
            synthetic_env,
            "opencode",
            synthetic_subprocess_results,
            error,
        )

    bundle = next(d for d in (tmp_path / "artifacts").iterdir() if d.is_dir())
    snapshot = bundle / "project-snapshot"
    assert snapshot.exists()
    assert (snapshot / "src" / "main.py").exists()
    assert (snapshot / ".claude" / "hooks.yaml").exists()
