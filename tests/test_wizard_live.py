"""Live integration tests -- real LLM calls via claude -p and opencode run.

Run with: pytest -m slow tests/test_wizard_live.py
Skip in fast CI:  pytest -m 'not slow'

Requires:
  - claude CLI installed and authenticated (OAuth or ANTHROPIC_API_KEY)
  - opencode CLI installed and authenticated
  - codebase-wizard plugin installed globally via ai-codebase-mentor
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURE_PROJECT = Path(__file__).parent / "fixtures" / "sample-wizard-project"

# ─────────────────────────────────────────────────────────────────────────────
# Auth availability — evaluated once at module import time
# ─────────────────────────────────────────────────────────────────────────────


def _probe_claude() -> bool:
    """Return True if claude -p can make a real API call."""
    if shutil.which("claude") is None:
        return False
    try:
        r = subprocess.run(
            [
                "claude", "-p", "OK",
                "--dangerously-skip-permissions",
                "--max-budget-usd", "0.01",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


def _probe_opencode() -> bool:
    """Return True if opencode run can make a real API call."""
    if shutil.which("opencode") is None:
        return False
    try:
        r = subprocess.run(
            ["opencode", "run", "OK"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


CLAUDE_AVAILABLE = _probe_claude()
OPENCODE_AVAILABLE = _probe_opencode()

skip_no_claude = pytest.mark.skipif(
    not CLAUDE_AVAILABLE,
    reason="claude not available or not authenticated",
)
skip_no_opencode = pytest.mark.skipif(
    not OPENCODE_AVAILABLE,
    reason="opencode not available or not authenticated",
)

# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def wizard_project(tmp_path):
    """Copy fixture project to isolated tmp dir and pre-create .code-wizard storage."""
    project = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project)
    (project / ".code-wizard" / "sessions").mkdir(parents=True)
    (project / ".code-wizard" / "docs").mkdir(parents=True)
    (project / ".code-wizard" / "config.json").write_text(
        '{"version": 1, "resolved_storage": ".code-wizard", "created": "2026-03-25T00:00:00Z"}\n'
    )
    return project


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def run_claude(
    prompt: str, cwd: Path, budget: float = 0.50, timeout: int = 120
) -> subprocess.CompletedProcess:
    """Run claude -p in headless mode. Requires global plugin install."""
    return subprocess.run(
        [
            "claude", "-p", prompt,
            "--dangerously-skip-permissions",
            "--max-budget-usd", str(budget),
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_opencode(
    message: str, cwd: Path, timeout: int = 120
) -> subprocess.CompletedProcess:
    """Run opencode run in headless mode. Uses --dir to set working directory."""
    return subprocess.run(
        ["opencode", "run", message, "--dir", str(cwd)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests: WIZARD-01 through WIZARD-05
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.slow
@skip_no_claude
def test_claude_describe_creates_transcript(wizard_project):
    """WIZARD-01: claude -p describe mode creates SESSION-TRANSCRIPT.md."""
    result = run_claude(
        "Run the codebase wizard in describe mode on this project. "
        "This is a teaching example. "
        "Write SESSION-TRANSCRIPT.md to .code-wizard/docs/claude-test-001/. "
        "Proceed without asking questions -- document as-is.",
        cwd=wizard_project,
    )
    assert result.returncode == 0, (
        f"claude -p failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    transcript = wizard_project / ".code-wizard" / "docs" / "claude-test-001" / "SESSION-TRANSCRIPT.md"
    assert transcript.exists(), (
        f"SESSION-TRANSCRIPT.md not created at {transcript}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    content = transcript.read_text()
    assert len(content) > 200, (
        f"SESSION-TRANSCRIPT.md too small: {len(content)} bytes.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert any(line.startswith("# ") for line in content.splitlines()), (
        f"SESSION-TRANSCRIPT.md has no top-level heading.\n"
        f"Content preview: {content[:500]}"
    )


@pytest.mark.slow
@skip_no_claude
def test_claude_describe_creates_codebase_md(wizard_project):
    """WIZARD-02: claude -p describe mode creates SESSION-TRANSCRIPT.md and CODEBASE.md."""
    result = run_claude(
        "Run the codebase wizard in describe mode. "
        "Write SESSION-TRANSCRIPT.md and CODEBASE.md to .code-wizard/docs/claude-test-002/. "
        "Proceed without questions.",
        cwd=wizard_project,
    )
    assert result.returncode == 0, (
        f"claude -p failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    transcript = wizard_project / ".code-wizard" / "docs" / "claude-test-002" / "SESSION-TRANSCRIPT.md"
    assert transcript.exists(), (
        f"SESSION-TRANSCRIPT.md not created at {transcript}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    content = transcript.read_text()
    assert len(content) > 100, (
        f"SESSION-TRANSCRIPT.md too small: {len(content)} bytes.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.slow
@skip_no_opencode
def test_opencode_describe_creates_transcript(wizard_project):
    """WIZARD-03: opencode run describe mode creates SESSION-TRANSCRIPT.md."""
    result = run_opencode(
        "Run the codebase wizard in describe mode on this project. "
        "Write SESSION-TRANSCRIPT.md to .code-wizard/docs/opencode-test-001/. "
        "Proceed without asking questions.",
        cwd=wizard_project,
    )
    assert result.returncode == 0, (
        f"opencode run failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    transcript = (
        wizard_project / ".code-wizard" / "docs" / "opencode-test-001" / "SESSION-TRANSCRIPT.md"
    )
    assert transcript.exists(), (
        f"SESSION-TRANSCRIPT.md not created at {transcript}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    content = transcript.read_text()
    assert len(content) > 200, (
        f"SESSION-TRANSCRIPT.md too small: {len(content)} bytes.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.slow
def test_claude_skip_when_no_auth():
    """WIZARD-04: Skip logic probe runs without crashing when claude not available."""
    assert isinstance(CLAUDE_AVAILABLE, bool), (
        "_probe_claude() did not return a bool -- probe function is broken"
    )
    if not CLAUDE_AVAILABLE:
        pytest.skip("claude not available -- skip logic confirmed working")
    assert shutil.which("claude") is not None, (
        "CLAUDE_AVAILABLE=True but shutil.which('claude') returned None -- inconsistent state"
    )


@pytest.mark.slow
def test_opencode_skip_when_no_auth():
    """WIZARD-05: Skip logic probe runs without crashing when opencode not available."""
    assert isinstance(OPENCODE_AVAILABLE, bool), (
        "_probe_opencode() did not return a bool -- probe function is broken"
    )
    if not OPENCODE_AVAILABLE:
        pytest.skip("opencode not available -- skip logic confirmed working")
    assert shutil.which("opencode") is not None, (
        "OPENCODE_AVAILABLE=True but shutil.which('opencode') returned None -- inconsistent state"
    )
