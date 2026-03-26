"""Live integration tests — real LLM calls via claude -p and opencode run.

Run slow suite:  pytest -m slow tests/test_wizard_live.py
Fast tests only: pytest tests/  (slow deselected by default via pyproject.toml addopts)

Design contract:
- Plugin installed from current checkout into an isolated HOME (not ambient global state).
  Auth credentials are copied from the real HOME so CLIs can authenticate.
- Prompts use trigger phrases from the explaining-codebase SKILL.md, not explicit paths.
  Output path is derived from config.json resolved_storage (the skill's own contract).
- Assertions check fixture-specific content (calculate, src/main.py) to prove the wizard
  actually read the project, not just produced a generic response.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pytest

FIXTURE_PROJECT = Path(__file__).parent / "fixtures" / "sample-wizard-project"

# ─────────────────────────────────────────────────────────────────────────────
# Auth probes — lazy, never called at import time
# ─────────────────────────────────────────────────────────────────────────────


def _probe_claude() -> bool:
    """Return True if claude -p can make a real API call."""
    if shutil.which("claude") is None:
        return False
    try:
        r = subprocess.run(
            ["claude", "-p", "OK", "--dangerously-skip-permissions", "--max-budget-usd", "0.01"],
            capture_output=True, text=True, timeout=30,
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
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Session-scoped auth fixtures — probes run once per session, only under -m slow
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def claude_available() -> bool:
    return _probe_claude()


@pytest.fixture(scope="session")
def opencode_available() -> bool:
    return _probe_opencode()


# ─────────────────────────────────────────────────────────────────────────────
# Isolated HOME — install current checkout, copy auth credentials
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def isolated_home(tmp_path_factory) -> Path:
    """Install codebase-wizard from current checkout into an isolated HOME.

    Auth credentials are copied from the real HOME so `claude -p` can authenticate.
    Plugin files come exclusively from the current checkout install, not ambient state.
    """
    home = tmp_path_factory.mktemp("home")
    isolated_claude = home / ".claude"
    isolated_claude.mkdir(parents=True)

    # Copy only auth credentials — not global plugins or settings
    real_claude = Path.home() / ".claude"
    for auth_file in ("auth.json", ".credentials.json"):
        src = real_claude / auth_file
        if src.exists():
            shutil.copy2(src, isolated_claude / auth_file)

    # Install from current checkout (writes plugins/ + installed_plugins.json + settings.json)
    result = subprocess.run(
        ["ai-codebase-mentor", "install", "--for", "claude"],
        env={**os.environ, "HOME": str(home)},
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        pytest.skip(
            f"ai-codebase-mentor install --for claude failed (rc={result.returncode}).\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return home


@pytest.fixture(scope="session")
def isolated_plugin_dir(isolated_home: Path) -> Path:
    """Return the versioned plugin directory installed in isolated_home.

    ai-codebase-mentor installs to:
        ~/.claude/plugins/cache/codebase-mentor/codebase-wizard/{version}/

    Returns the latest versioned directory so tests can pass it to
    claude --plugin-dir without overriding HOME (which breaks keychain auth).
    """
    cache_plugin_dir = (
        isolated_home / ".claude" / "plugins" / "cache"
        / "codebase-mentor" / "codebase-wizard"
    )
    if not cache_plugin_dir.exists():
        pytest.skip(
            f"Plugin cache not found: {cache_plugin_dir}\n"
            "ai-codebase-mentor install may have failed silently."
        )
    version_dirs = sorted([d for d in cache_plugin_dir.iterdir() if d.is_dir()])
    if not version_dirs:
        pytest.skip(f"No versioned plugin dirs found under {cache_plugin_dir}")
    return version_dirs[-1]


# ─────────────────────────────────────────────────────────────────────────────
# Per-test project fixture
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def wizard_project(tmp_path) -> Path:
    """Copy fixture project to isolated tmp dir and pre-create .code-wizard storage."""
    project = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project)
    (project / ".code-wizard" / "sessions").mkdir(parents=True)
    (project / ".code-wizard" / "docs").mkdir(parents=True)
    (project / ".code-wizard" / "config.json").write_text(
        json.dumps({
            "version": 1,
            "resolved_storage": ".code-wizard",
            "created": "2026-03-26T00:00:00Z",
        }) + "\n"
    )
    return project


# ─────────────────────────────────────────────────────────────────────────────
# CLI helpers
# ─────────────────────────────────────────────────────────────────────────────


def run_claude(
    prompt: str, cwd: Path, plugin_dir: Path, budget: float = 0.75, timeout: int = 180
) -> subprocess.CompletedProcess:
    """Run claude -p with plugin loaded from isolated install dir.

    Uses --plugin-dir instead of HOME override so macOS keychain auth works.
    """
    return subprocess.run(
        [
            "claude", "-p", prompt,
            "--plugin-dir", str(plugin_dir),
            "--dangerously-skip-permissions",
            "--max-budget-usd", str(budget),
        ],
        cwd=str(cwd),
        capture_output=True, text=True, timeout=timeout,
    )


def run_opencode(
    message: str, cwd: Path, timeout: int = 180
) -> subprocess.CompletedProcess:
    """Run opencode run in headless mode. Uses --dir to set working directory."""
    return subprocess.run(
        ["opencode", "run", message, "--dir", str(cwd)],
        capture_output=True, text=True, timeout=timeout,
    )


def _find_output(project: Path, filename: str) -> Optional[Path]:
    """Find a wizard output file under .code-wizard/docs/*/<filename>.

    The session_id subdirectory is generated dynamically by the skill, so
    we glob rather than hardcode the path.
    """
    matches = list((project / ".code-wizard" / "docs").glob(f"*/{filename}"))
    return matches[0] if matches else None


# ─────────────────────────────────────────────────────────────────────────────
# Tests: WIZARD-01 through WIZARD-05
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_claude_describe_creates_transcript(wizard_project, claude_available, isolated_plugin_dir):
    """WIZARD-01: claude -p describe mode writes SESSION-TRANSCRIPT.md via skill output contract.

    The prompt uses SKILL.md trigger phrases. The output path comes from config.json
    resolved_storage, not from the prompt. Assertions verify fixture-specific content
    to prove the wizard actually scanned the project files.
    """
    if not claude_available:
        pytest.skip("claude not available or not authenticated")
    result = run_claude(
        "describe this codebase and save a SESSION-TRANSCRIPT.md when done. "
        "Proceed without asking questions.",
        cwd=wizard_project,
        plugin_dir=isolated_plugin_dir,
    )
    assert result.returncode == 0, (
        f"claude -p failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    transcript = _find_output(wizard_project, "SESSION-TRANSCRIPT.md")
    docs_dir = wizard_project / ".code-wizard" / "docs"
    assert transcript is not None, (
        f"SESSION-TRANSCRIPT.md not found under .code-wizard/docs/*/.\n"
        f"docs contents: {list(docs_dir.iterdir()) if docs_dir.exists() else 'empty'}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    content = transcript.read_text()
    assert len(content) > 200, (
        f"SESSION-TRANSCRIPT.md too small ({len(content)} bytes).\nPreview: {content[:200]}"
    )
    assert any(line.startswith("# ") for line in content.splitlines()), (
        f"SESSION-TRANSCRIPT.md has no top-level heading.\nPreview: {content[:500]}"
    )
    # Fixture-specific: wizard must have read src/main.py and found calculate()
    assert "calculate" in content or "src/main.py" in content, (
        f"SESSION-TRANSCRIPT.md does not mention fixture-specific content "
        f"(calculate or src/main.py).\nPreview: {content[:500]}"
    )


@pytest.mark.slow
def test_claude_describe_creates_codebase_md(wizard_project, claude_available, isolated_plugin_dir):
    """WIZARD-02: claude -p describe mode creates CODEBASE.md with expected section headings.

    Asserts CODEBASE.md exists (not just SESSION-TRANSCRIPT.md) and contains at least
    one of the documented sections from the explain-codebase SKILL.md output contract.
    Also verifies fixture-specific content to confirm the project was actually scanned.
    """
    if not claude_available:
        pytest.skip("claude not available or not authenticated")
    result = run_claude(
        "describe this codebase and generate CODEBASE.md. "
        "Proceed without asking questions.",
        cwd=wizard_project,
        plugin_dir=isolated_plugin_dir,
    )
    assert result.returncode == 0, (
        f"claude -p failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    docs_dir = wizard_project / ".code-wizard" / "docs"
    codebase_md = _find_output(wizard_project, "CODEBASE.md")
    assert codebase_md is not None, (
        f"CODEBASE.md not found under .code-wizard/docs/*/.\n"
        f"docs contents: {list(docs_dir.iterdir()) if docs_dir.exists() else 'empty'}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    content = codebase_md.read_text()
    assert len(content) > 100, (
        f"CODEBASE.md too small ({len(content)} bytes).\nPreview: {content[:200]}"
    )
    # At least one documented CODEBASE.md section must appear
    has_section = any(
        heading in content
        for heading in ("## Overview", "# Overview", "## Entry Points", "## Entry", "## Constraints")
    )
    assert has_section, (
        f"CODEBASE.md missing expected headings (Overview / Entry Points / Constraints).\n"
        f"Preview: {content[:500]}"
    )
    # Fixture-specific: describe mode must have read the actual source file
    assert "calculate" in content or "Sample Wizard" in content or "src/main.py" in content, (
        f"CODEBASE.md does not mention fixture-specific content.\nPreview: {content[:500]}"
    )


@pytest.mark.slow
def test_opencode_describe_creates_transcript(wizard_project, opencode_available):
    """WIZARD-03: opencode run describe mode creates SESSION-TRANSCRIPT.md.

    Uses SKILL.md trigger phrases. Output path derived from config.json.
    Assertions check fixture-specific content.
    """
    if not opencode_available:
        pytest.skip("opencode not available or not authenticated")
    result = run_opencode(
        "describe this codebase and save a SESSION-TRANSCRIPT.md when done. "
        "Proceed without asking questions.",
        cwd=wizard_project,
    )
    assert result.returncode == 0, (
        f"opencode run failed.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    docs_dir = wizard_project / ".code-wizard" / "docs"
    transcript = _find_output(wizard_project, "SESSION-TRANSCRIPT.md")
    assert transcript is not None, (
        f"SESSION-TRANSCRIPT.md not found under .code-wizard/docs/*/.\n"
        f"docs contents: {list(docs_dir.iterdir()) if docs_dir.exists() else 'empty'}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    content = transcript.read_text()
    assert len(content) > 200, (
        f"SESSION-TRANSCRIPT.md too small ({len(content)} bytes).\nPreview: {content[:200]}"
    )
    assert "calculate" in content or "src/main.py" in content, (
        f"SESSION-TRANSCRIPT.md does not mention fixture content.\nPreview: {content[:500]}"
    )


@pytest.mark.slow
def test_claude_skip_when_no_auth(claude_available):
    """WIZARD-04: Skip logic probe runs without crashing when claude not available."""
    assert isinstance(claude_available, bool), (
        "_probe_claude() did not return a bool -- probe function is broken"
    )
    if not claude_available:
        pytest.skip("claude not available -- skip logic confirmed working")
    assert shutil.which("claude") is not None, (
        "claude_available=True but shutil.which('claude') returned None -- inconsistent state"
    )


@pytest.mark.slow
def test_opencode_skip_when_no_auth(opencode_available):
    """WIZARD-05: Skip logic probe runs without crashing when opencode not available."""
    assert isinstance(opencode_available, bool), (
        "_probe_opencode() did not return a bool -- probe function is broken"
    )
    if not opencode_available:
        pytest.skip("opencode not available -- skip logic confirmed working")
    assert shutil.which("opencode") is not None, (
        "opencode_available=True but shutil.which('opencode') returned None -- inconsistent state"
    )
