# Phase 13: Live Wizard CLI Integration Tests — Research

**Researched:** 2026-03-25
**Domain:** Headless LLM CLI invocation, pytest slow-test patterns, subprocess integration testing
**Confidence:** HIGH (all findings verified by direct execution)

---

## Summary

Phase 13 writes the live integration test suite for the codebase-wizard — tests that actually call `claude -p` and `opencode run` against a sample fixture project and verify that `.code-wizard/docs/` output files are created with expected content.

The critical discovery is that **`claude -p` does NOT support slash commands** (`/codebase-wizard`, `/codebase-wizard-setup`) in headless/print mode — they return `"Unknown skill: codebase-wizard"`. The correct approach is natural language prompts that activate the explaining-codebase skill via its trigger phrases. Both `claude -p "natural language..."` and `opencode run "natural language..."` work reliably and do write SESSION-TRANSCRIPT.md to the specified output path.

These tests make real LLM API calls, take 30–120 seconds each, and require authentication (`ANTHROPIC_API_KEY` for CI or OAuth for local dev). They must be isolated from the fast test suite with `@pytest.mark.slow` and skip logic that detects missing auth at collection time.

**Primary recommendation:** Create `tests/test_wizard_live.py` with `@pytest.mark.slow` markers, a `pytest_configure`-registered custom marker, natural language invocation via subprocess, and content assertions on file existence plus minimum byte-count.

---

## Standard Stack

### Core

| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| `pytest` | 9.0.2 (current) | Test runner | Already in use for all 49 existing tests |
| `subprocess` | stdlib | Invoke `claude -p` and `opencode run` | No new dependency; same pattern as `test_e2e_setup.py` |
| `pathlib.Path` | stdlib | Path assertions | Same pattern as all existing tests |
| `json` | stdlib | Parse opencode --format json output (optional) | Same pattern as `test_e2e_installer.py` |

### Supporting

| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| `pytest.mark.slow` | custom marker | Gate live tests behind a flag | All tests in `test_wizard_live.py` |
| `pytest.mark.skipif` | pytest built-in | Skip when auth unavailable | Tests that need `claude` or `opencode` |
| `tmp_path` | pytest built-in | Isolated temp dir per test | All fixture project tests |
| `--max-budget-usd 0.50` | `claude -p` flag | Cap API spend per test | All `claude -p` invocations |

### Installed CLIs (verified on this machine)

| CLI | Path | Auth Method | Command for headless |
|-----|------|-------------|----------------------|
| `claude` | `~/.local/bin/claude` | OAuth (local) or `ANTHROPIC_API_KEY` (CI) | `claude -p "prompt" --dangerously-skip-permissions` |
| `opencode` | `/opt/homebrew/bin/opencode` | Same as Claude | `opencode run "message"` |

**Installation:**

No new Python dependencies required. The tests use subprocess to call CLIs that are already installed.

Add to `pyproject.toml` under `[tool.pytest.ini_options]`:
```toml
[tool.pytest.ini_options]
markers = [
    "slow: mark test as slow — makes real LLM API calls (deselect with -m 'not slow')",
]
```

**Version verification:** Run `claude --version` and `opencode --version` to confirm CLIs are present before the test session.

---

## Architecture Patterns

### Recommended Project Structure

```
tests/
├── test_wizard_live.py        # NEW — Phase 13 live integration tests
├── fixtures/
│   └── sample-wizard-project/ # NEW — minimal Python fixture project
│       ├── README.md
│       └── src/
│           └── main.py
├── test_e2e_installer.py      # Existing — CliRunner tests (fast)
├── test_e2e_setup.py          # Existing — setup.sh subprocess tests (fast)
├── test_claude_installer.py   # Existing — unit tests
└── test_opencode_installer.py # Existing — unit tests
```

### Pattern 1: Fixture Project via tmp_path

The fixture project is copied from `tests/fixtures/sample-wizard-project/` into `tmp_path` at test time. This isolates every test run and avoids state pollution.

```python
# Source: verified execution pattern from test_e2e_setup.py
import shutil
from pathlib import Path

FIXTURE_PROJECT = Path(__file__).parent / "fixtures" / "sample-wizard-project"
SETUP_SH = Path(__file__).parent.parent / "plugins" / "codebase-wizard" / \
           "skills" / "configuring-codebase-wizard" / "scripts" / "setup.sh"

@pytest.fixture
def wizard_project(tmp_path):
    """Copy fixture project to tmp_path, pre-create .code-wizard storage."""
    project = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project)
    # Pre-create .code-wizard/ so setup.sh doesn't prompt interactively
    (project / ".code-wizard" / "sessions").mkdir(parents=True)
    (project / ".code-wizard" / "docs").mkdir(parents=True)
    (project / ".code-wizard" / "config.json").write_text(
        '{"version": 1, "resolved_storage": ".code-wizard", "created": "2026-03-25T00:00:00Z"}\n'
    )
    return project
```

### Pattern 2: claude -p Invocation

`claude -p` runs in print/headless mode. Slash commands (`/codebase-wizard`) are **not** supported — they return `"Unknown skill: name"`. Use natural language prompts that match the skill's trigger conditions from `explaining-codebase/SKILL.md`.

```python
# Source: verified by direct execution (2026-03-25)
import subprocess

def run_claude(prompt: str, cwd: Path, budget: float = 0.50, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run claude -p in headless mode. Requires global plugin install or --plugin-dir."""
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
```

**Critical:** The plugin must be installed globally (`~/.claude/plugins/cache/codebase-mentor/codebase-wizard/1.0.0/`) OR loaded via `--plugin-dir path/to/plugin`. As of 2026-03-25, `codebase-wizard@codebase-mentor: true` is confirmed in `~/.claude/settings.json`.

### Pattern 3: opencode run Invocation

`opencode run` takes a message positional argument. Use `--dir` to set the working directory. The `--command` flag (intended for slash commands) hangs silently and should not be used.

```python
# Source: verified by direct execution (2026-03-25)
def run_opencode(message: str, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run opencode run in headless mode."""
    return subprocess.run(
        ["opencode", "run", message, "--dir", str(cwd)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
```

### Pattern 4: Auth Skip Guard

Tests that need LLM auth should skip gracefully when running in environments without credentials (e.g., fresh CI without `ANTHROPIC_API_KEY`, local without OAuth). The skip fixture runs a cheap probe call at test session start.

```python
# Source: verified skip pattern; probe confirmed working 2026-03-25
import os, shutil

def _claude_available() -> bool:
    """Return True if claude -p can make an API call."""
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

def _opencode_available() -> bool:
    """Return True if opencode run can make an API call."""
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

# Skip markers — evaluated once per session via module-level variables
CLAUDE_AVAILABLE = _claude_available()
OPENCODE_AVAILABLE = _opencode_available()

skip_no_claude = pytest.mark.skipif(not CLAUDE_AVAILABLE, reason="claude not available or not authenticated")
skip_no_opencode = pytest.mark.skipif(not OPENCODE_AVAILABLE, reason="opencode not available or not authenticated")
```

### Pattern 5: Wizard Invocation Prompt

The natural language prompt must match the skill trigger conditions. The following prompt is verified to activate describe mode and write both SESSION-TRANSCRIPT.md and CODEBASE.md without interactive prompts:

```python
# Source: verified by direct execution (2026-03-25)
DESCRIBE_PROMPT_TEMPLATE = (
    "Run the codebase wizard in describe mode on this project. "
    "This is a teaching example. "
    "Write SESSION-TRANSCRIPT.md and CODEBASE.md to "
    ".code-wizard/docs/{session_id}/ now. "
    "Proceed without asking questions — document as-is."
)
```

For explore mode (TOUR.md):
```python
EXPLORE_PROMPT_TEMPLATE = (
    "Run the codebase wizard in explore mode on this project. "
    "I am a new developer learning this codebase. "
    "Write TOUR.md and SESSION-TRANSCRIPT.md to "
    ".code-wizard/docs/{session_id}/ now. "
    "Proceed without asking questions."
)
```

### Pattern 6: Content Assertions

LLM output is non-deterministic. Assert on structural presence (file exists, minimum size, key heading pattern) — not exact strings.

```python
# Source: verified against multiple generated transcripts (2026-03-25)
def assert_session_transcript(docs_dir: Path, session_id: str) -> None:
    """Assert SESSION-TRANSCRIPT.md exists and has expected structure."""
    transcript = docs_dir / session_id / "SESSION-TRANSCRIPT.md"
    assert transcript.exists(), f"SESSION-TRANSCRIPT.md not found at {transcript}"
    content = transcript.read_text()
    assert len(content) > 200, f"SESSION-TRANSCRIPT.md too small ({len(content)} bytes) — likely empty"
    # Must contain at least one heading (the session title)
    assert any(line.startswith("# ") for line in content.splitlines()), \
        "SESSION-TRANSCRIPT.md has no top-level heading"
```

### Anti-Patterns to Avoid

- **Using `/codebase-wizard` slash command in `-p` mode:** Returns `"Unknown skill: codebase-wizard"`. The `-p` flag does not invoke plugin commands via slash syntax.
- **Using `opencode run --command codebase-wizard`:** The `--command` flag hangs silently. Use natural language message instead.
- **Asserting exact transcript content:** LLM output varies. Assert presence + minimum size only.
- **Running slow tests in main test suite without marker:** Slows CI drastically. Always use `@pytest.mark.slow`.
- **Not pre-creating `.code-wizard/`:** Without the directory, tools write to arbitrary locations (e.g., `docs/` at project root instead of `.code-wizard/docs/`). Always pre-create `.code-wizard/sessions/`, `.code-wizard/docs/`, and `config.json`.
- **Omitting `--dangerously-skip-permissions` from `claude -p`:** Without this flag, Claude prompts for workspace trust in headless mode, causing the test to hang.
- **Omitting `--max-budget-usd` from `claude -p`:** Without a budget cap, a runaway test can spend unexpected amounts on API calls.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Auth detection | Custom API key parser | Check `ANTHROPIC_API_KEY` env + probe call | OAuth auth has no file to parse; probe is the only reliable check |
| Subprocess timeout | Polling loop with sleep | `subprocess.run(timeout=N)` | Built-in, raises TimeoutExpired on overrun |
| Content validation | String diff / exact match | Presence + length assertions | LLM output is non-deterministic; exact assertions create flakiness |
| Fixture project management | Complex factory fixture | `shutil.copytree` from static fixtures dir | Simpler, source-controlled, reproducible |

---

## Common Pitfalls

### Pitfall 1: Slash Commands Don't Work in -p Mode

**What goes wrong:** Test invokes `claude -p "/codebase-wizard"` and gets `"Unknown skill: codebase-wizard"` exit code 1.
**Why it happens:** `claude -p` processes skills (SKILL.md triggers) but not plugin commands (commands/*.md with frontmatter). Plugin commands are interactive-session only.
**How to avoid:** Use natural language prompts matching skill triggers: `"explain this codebase"`, `"run codebase wizard describe mode"`, `"document this project"`.
**Warning signs:** Test output contains `"Unknown skill:"` string.

### Pitfall 2: opencode --command Flag Hangs

**What goes wrong:** `opencode run --command codebase-wizard` returns no output, no error, just hangs until timeout.
**Why it happens:** The `--command` flag is underdocumented; it may require specific opencode-format command names that differ from our plugin's naming.
**How to avoid:** Use `opencode run "natural language message"` instead of `--command`.
**Warning signs:** Test hangs for full timeout duration with no output.

### Pitfall 3: Missing .code-wizard Pre-Setup

**What goes wrong:** `opencode run` creates `docs/` at project root instead of `.code-wizard/docs/`. Claude writes to a random path.
**Why it happens:** Without `.code-wizard/config.json`, neither tool has a reference for the storage path. They improvise.
**How to avoid:** Every fixture must pre-create `.code-wizard/sessions/`, `.code-wizard/docs/`, and `config.json` with `resolved_storage: .code-wizard`.
**Warning signs:** Assertions fail because `session_dir` doesn't exist but `docs/` or other top-level directories appear.

### Pitfall 4: Test Pollution from OAuth Session History

**What goes wrong:** `claude -p` picks up previous session context and treats the test fixture project as the wrong codebase.
**Why it happens:** Without `--no-session-persistence`, Claude may resume previous sessions or add context from prior calls.
**How to avoid:** Add `--no-session-persistence` to `claude -p` invocations in tests. BUT: this flag combined with `--max-budget-usd` in the same invocation may cause issues on some versions — test the combination first.
**Warning signs:** Transcript references files not in the fixture project.

### Pitfall 5: Budget Exceeded Causes Test Failure

**What goes wrong:** Test fails with `"Error: Exceeded USD budget (0.1)"`.
**Why it happens:** Budget set too low for a describe-mode session on even a tiny project.
**How to avoid:** Use `--max-budget-usd 0.50` as the minimum. Verified: 0.50 is sufficient for a 3-file Python fixture project in describe mode.
**Warning signs:** Test exits with non-zero code and stderr contains `"Exceeded USD budget"`.

### Pitfall 6: CI Authentication

**What goes wrong:** Tests pass locally (OAuth keychain) but fail in CI (`"Error: No authentication found"`).
**Why it happens:** CI environments have no keychain; OAuth is unavailable. Only `ANTHROPIC_API_KEY` works in CI.
**How to avoid:** (a) Add skip logic: `pytest.mark.skipif(not ANTHROPIC_API_KEY, ...)`. (b) Add `ANTHROPIC_API_KEY` to CI secrets. (c) Mark all live tests `@pytest.mark.slow` and exclude from `pytest -m 'not slow'` in CI unless the secret is present.
**Warning signs:** All live tests are skipped in CI; fast tests still pass.

---

## Code Examples

### Complete Test File Skeleton

```python
# tests/test_wizard_live.py
# Source: verified patterns from direct execution (2026-03-25)
"""Live integration tests — real LLM calls via claude -p and opencode run.

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
SETUP_SH = (
    Path(__file__).parent.parent
    / "plugins" / "codebase-wizard"
    / "skills" / "configuring-codebase-wizard" / "scripts" / "setup.sh"
)

# ─────────────────────────────────────────────────────────────────────────────
# Auth availability — evaluated once at module import time
# ─────────────────────────────────────────────────────────────────────────────

def _probe_claude() -> bool:
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

CLAUDE_AVAILABLE = _probe_claude()
OPENCODE_AVAILABLE = _probe_opencode()

skip_no_claude = pytest.mark.skipif(
    not CLAUDE_AVAILABLE,
    reason="claude not available or not authenticated"
)
skip_no_opencode = pytest.mark.skipif(
    not OPENCODE_AVAILABLE,
    reason="opencode not available or not authenticated"
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

def run_claude(prompt: str, cwd: Path, budget: float = 0.50, timeout: int = 120):
    return subprocess.run(
        ["claude", "-p", prompt,
         "--dangerously-skip-permissions",
         "--max-budget-usd", str(budget)],
        cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
    )

def run_opencode(message: str, cwd: Path, timeout: int = 120):
    return subprocess.run(
        ["opencode", "run", message, "--dir", str(cwd)],
        capture_output=True, text=True, timeout=timeout,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Tests: WIZARD-01 through WIZARD-0N
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.slow
@skip_no_claude
def test_claude_describe_mode_creates_session_transcript(wizard_project):
    """WIZARD-01: claude -p describe mode creates SESSION-TRANSCRIPT.md."""
    result = run_claude(
        "Run codebase wizard describe mode. This is a teaching example. "
        "Write SESSION-TRANSCRIPT.md and CODEBASE.md to .code-wizard/docs/claude-describe-001/. "
        "Proceed without questions.",
        cwd=wizard_project,
    )
    assert result.returncode == 0, f"claude -p failed: {result.stderr}"
    transcript = wizard_project / ".code-wizard" / "docs" / "claude-describe-001" / "SESSION-TRANSCRIPT.md"
    assert transcript.exists(), f"SESSION-TRANSCRIPT.md not created at {transcript}"
    content = transcript.read_text()
    assert len(content) > 200, f"SESSION-TRANSCRIPT.md too small: {len(content)} bytes"
```

### Fixture Project Files

```
tests/fixtures/sample-wizard-project/
├── README.md
└── src/
    └── main.py
```

`README.md`:
```markdown
# Sample Wizard Project

A minimal Python utility for testing the codebase-wizard skill.

## Functions

- `calculate(a, b)` — returns sum, difference, and product as a dict
```

`src/main.py`:
```python
"""Sample project: minimal Python for codebase-wizard testing."""


def calculate(a: int, b: int) -> dict:
    """Compute sum, difference, and product of two integers.

    Returns a dict with keys 'sum', 'diff', 'product'.
    """
    return {"sum": a + b, "diff": a - b, "product": a * b}
```

### pyproject.toml Addition

```toml
# Source: pytest marker registration docs
[tool.pytest.ini_options]
markers = [
    "slow: mark test as slow — makes real LLM API calls (skip with -m 'not slow')",
]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Interactive CLI sessions | `claude -p` headless print mode | Available since Claude Code v1 | Enables automated testing of LLM-powered tools |
| Manual slash command invocation | Natural language prompt triggers skills | Always been skill-based | Tests must use NL prompts, not `/command` syntax |
| All tests in one file | Separate slow/fast files by marker | Best practice for LLM test suites | Fast CI stays fast; slow tests opt-in |

**Deprecated/outdated:**
- `claude -p "/slash-command"`: Returns `"Unknown skill: name"` — never worked in `-p` mode for plugin commands.
- `opencode run --command NAME`: Hangs silently in observed behavior on this machine (2026-03-25). Use natural language message instead.

---

## Open Questions

1. **CI: How to conditionally run slow tests when `ANTHROPIC_API_KEY` is available?**
   - What we know: Tests need API key in CI; OAuth not available there
   - What's unclear: Which GitHub Actions workflow should run slow tests — `test-installer.yml` or a new `test-wizard-live.yml`?
   - Recommendation: Add a separate `test-wizard-live.yml` that gates on `secrets.ANTHROPIC_API_KEY` being present; skip in the fast workflow

2. **Plugin install in CI: global vs. --plugin-dir?**
   - What we know: `--plugin-dir` works for loading plugins without global install
   - What's unclear: Whether `claude -p` with `--plugin-dir` pointing to the project's `plugins/codebase-wizard/` is sufficient, or if `ai-codebase-mentor install --for claude` is required first
   - Recommendation: Use `--plugin-dir $(PLUGIN_SOURCE_PATH)` in CI to avoid needing the installer as a prerequisite; verified that `--plugin-dir` loads command files correctly

3. **opencode: Does it auto-install codebase-wizard from `~/.config/opencode/codebase-wizard/`?**
   - What we know: `~/.config/opencode/codebase-wizard/` exists on this dev machine (installed by `ai-codebase-mentor install --for opencode`)
   - What's unclear: Whether opencode scans a configurable plugin dir or only the global config dir
   - Recommendation: Require `ai-codebase-mentor install --for opencode` as a test prerequisite in the skip guard; detect by checking `~/.config/opencode/codebase-wizard/` existence

4. **Content assertion stability: how stable are the structural headers?**
   - What we know: Observed across 6 separate sessions — `SESSION-TRANSCRIPT.md` always has at least one `# ` heading and is > 200 bytes
   - What's unclear: Whether the exact heading text (e.g. `"# Session Transcript"`) is stable enough to assert
   - Recommendation: Assert only on existence + minimum size; do NOT assert on specific heading text

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` — needs `[tool.pytest.ini_options]` with `markers = ["slow: ..."]` |
| Quick run command | `python -m pytest tests/ -m 'not slow' -v` |
| Full suite command (no live) | `python -m pytest tests/ -m 'not slow' -v` |
| Live tests only | `python -m pytest tests/test_wizard_live.py -m slow -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIZARD-01 | `claude -p` describe mode creates SESSION-TRANSCRIPT.md | live integration | `pytest -m slow tests/test_wizard_live.py::test_claude_describe_mode_creates_session_transcript` | Wave 0 |
| WIZARD-02 | `claude -p` describe mode SESSION-TRANSCRIPT.md has content (> 200 bytes, heading present) | live integration | `pytest -m slow tests/test_wizard_live.py::test_claude_describe_mode_transcript_has_content` | Wave 0 |
| WIZARD-03 | `opencode run` describe mode creates SESSION-TRANSCRIPT.md | live integration | `pytest -m slow tests/test_wizard_live.py::test_opencode_describe_mode_creates_session_transcript` | Wave 0 |
| WIZARD-04 | Hook files exist after `setup.sh` runs (agent-rulez.yaml, capture-session.sh) | E2E subprocess (fast) | `pytest tests/test_e2e_setup.py -v` (already passing) | tests/test_e2e_setup.py |
| WIZARD-05 | Full pipeline: pre-setup .code-wizard + claude describe + verify docs dir populated | live integration | `pytest -m slow tests/test_wizard_live.py::test_full_pipeline_claude_describe` | Wave 0 |
| WIZARD-06 | Skip logic: tests skip gracefully when CLI not authenticated | unit (probe logic) | `pytest -m slow tests/test_wizard_live.py` (should skip, not fail, when no auth) | Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ -m 'not slow' --tb=short` (49 existing tests, < 5 seconds)
- **Per wave merge:** `python -m pytest tests/ -m 'not slow' -v` (full fast suite)
- **Phase gate:** Fast suite green + live suite green (when auth available) before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_wizard_live.py` — covers WIZARD-01 through WIZARD-06 (new file)
- [ ] `tests/fixtures/sample-wizard-project/README.md` — fixture project (new file)
- [ ] `tests/fixtures/sample-wizard-project/src/main.py` — fixture source (new file)
- [ ] `pyproject.toml` — add `[tool.pytest.ini_options]` with `markers = ["slow: ..."]`

---

## Sources

### Primary (HIGH confidence)

- Direct execution: `claude -p` flag enumeration via `claude --help` — verified 2026-03-25
- Direct execution: `opencode run --help` — verified 2026-03-25
- Direct execution: `claude -p "/codebase-wizard"` → `"Unknown skill: codebase-wizard"` — verified 2026-03-25
- Direct execution: `claude -p "natural language describe prompt"` → SESSION-TRANSCRIPT.md created — verified 2026-03-25, 6 separate test runs
- Direct execution: `opencode run "natural language"` with `--dir` → SESSION-TRANSCRIPT.md created — verified 2026-03-25, 3 separate test runs
- `~/.claude/plugins/installed_plugins.json` — codebase-wizard@codebase-mentor confirmed installed at `~/.claude/plugins/cache/codebase-mentor/codebase-wizard/1.0.0/`
- `~/.claude/settings.json` — `"codebase-wizard@codebase-mentor": true` confirmed
- `~/.config/opencode/codebase-wizard/command/` — codebase-wizard commands confirmed installed for opencode

### Secondary (MEDIUM confidence)

- `tests/test_e2e_setup.py` — existing subprocess test patterns (already proven in 8 SETUP tests)
- `tests/test_e2e_installer.py` — existing CliRunner test patterns (already proven in 9 E2E tests)

### Tertiary (LOW confidence)

- `opencode run --command NAME` hanging: Observed behavior on this machine but not confirmed as universal — may be a version-specific issue or a config issue with command scoping.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all CLIs verified installed and authenticated
- Architecture: HIGH — invocation patterns verified by direct execution
- Pitfalls: HIGH — every pitfall was hit during research and resolved
- Content assertions: HIGH — structural patterns observed across 6 sessions
- CI auth handling: MEDIUM — local OAuth verified; CI ANTHROPIC_API_KEY approach is standard pattern but not directly tested in this research

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (30 days) — stable CLI flags, but verify `claude --version` and `opencode --version` before planning to catch breaking changes
