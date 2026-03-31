# Phase 15: Gemini E2E Integration Tests - Research

**Researched:** 2026-03-31
**Domain:** Python testing (pytest, Click CliRunner, subprocess), Gemini CLI headless invocation
**Confidence:** HIGH

## Summary

Phase 15 adds E2E integration tests for the Gemini converter (implemented in Phase 14). The project already has well-established patterns for both CliRunner-based E2E tests (`tests/test_e2e_installer.py`, 133 lines) and live CLI integration tests (`tests/test_wizard_live.py`, 348 lines), plus a comprehensive failure artifact bundle system (`tests/integration/test_agent_rulez_e2e.py`). This phase replicates those patterns for Gemini.

The Gemini CLI is confirmed installed (v0.33.0) and supports headless invocation via `gemini -p "prompt" --approval-mode yolo -o text`. The GeminiInstaller is fully wired into the CLI via `_get_converters()` and supports global (`~/.gemini/codebase-wizard/`), project (`./.gemini/codebase-wizard/`), install/uninstall/status, and `--for all` iteration.

**Primary recommendation:** Follow existing patterns exactly — `cli_env` fixture for CliRunner tests, `_probe_gemini()`/`run_gemini()` helpers for live tests. Update existing `--for all` and status tests to assert Gemini presence. Create `scripts/run_gemini_e2e_with_artifacts.sh` modeled on the OpenCode variant.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| E2E-01 | CliRunner e2e tests for `install --for gemini` — verify file output in temp dir (global + project) | Existing `cli_env` fixture pattern; GeminiInstaller writes to `.gemini/codebase-wizard/` with `agent/`, `command/`, `skill/` subdirs |
| E2E-02 | CliRunner e2e tests for `uninstall --for gemini` — verify clean removal | Same pattern as `test_cli_uninstall_opencode_project` (line 66-75 of test_e2e_installer.py) |
| E2E-03 | CliRunner e2e tests for `status` — verify Gemini install state reporting | Status output format: `gemini: installed at <path> (v<version>)` — same as other runtimes |
| E2E-04 | Verify generated TOML command files parse correctly (valid TOML syntax) | `tomllib.loads()` pattern already used in `test_gemini_installer.py` line 352-359; Python 3.11+ stdlib |
| E2E-05 | Verify agent files have correct `tools:` array with Gemini snake_case names | 10 tool mappings in `GEMINI_TOOL_MAP`; agent files use YAML `tools:` key (not `allowed_tools:`) |
| E2E-06 | Verify `--for all` includes Gemini alongside Claude and OpenCode | Existing test only checks `.opencode/` and `plugins/` — must add `.gemini/` assertion |
| E2E-07 | Live Gemini CLI integration test — headless invocation with fixture project | `gemini -p "prompt" --approval-mode yolo -o text` confirmed working; needs `_probe_gemini()`, artifact bundle |
| E2E-08 | All e2e tests MUST be executed and results reported | Per CLAUDE.md testing policy — writing is step 1, running is step 2 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | ≥7.0 | Test framework | Already in `[project.optional-dependencies] dev` |
| click.testing.CliRunner | (bundled with click ≥8.0) | CLI integration testing | Already used in `test_e2e_installer.py` |
| tomllib | (stdlib 3.11+) | TOML validation | Already used in `test_gemini_installer.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shutil | (stdlib) | File copying, CLI probe via `which()` | Live test probing, fixture setup |
| subprocess | (stdlib) | Gemini CLI headless invocation | Live test `run_gemini()` helper |
| tarfile | (stdlib) | Failure artifact bundle compression | `_collect_failure_artifacts()` |

### Alternatives Considered
None — this phase replicates existing proven patterns. No new libraries needed.

## Architecture Patterns

### Recommended Test Structure
```
tests/
├── test_e2e_installer.py         # ← ADD gemini tests here (or new file)
├── test_e2e_gemini_installer.py  # ← PREFERRED: new file to avoid bloating existing
├── test_wizard_live.py           # ← ADD gemini probe/fixture/test here
├── integration/
│   └── test_agent_rulez_e2e.py   # ← REFERENCE ONLY for artifact bundle pattern
└── fixtures/
    └── sample-wizard-project/     # ← Reuse existing fixture
scripts/
└── run_gemini_e2e_with_artifacts.sh  # ← NEW: modeled on run_opencode_e2e_with_artifacts.sh
```

### Pattern 1: `cli_env` Fixture for CliRunner Tests
**What:** Creates `tmp_path/home` and `tmp_path/cwd`, monkeypatches `Path.home()` and `os.chdir()` for full CLI isolation.
**When to use:** All CliRunner-based tests that exercise install/uninstall/status.
**Example:**
```python
# Source: tests/test_e2e_installer.py, lines 12-21
@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """Redirect home() and cwd() to temp dirs for full CLI isolation."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    return tmp_path
```

### Pattern 2: Probe Function + Session Fixture for Live Tests
**What:** Probe function checks if CLI binary exists and can make a trivial API call. Session-scoped fixture caches the result.
**When to use:** Live tests that require real CLI availability.
**Example:**
```python
# Adapted from tests/test_wizard_live.py, lines 31-43
def _probe_gemini() -> bool:
    """Return True if gemini -p can make a real API call."""
    if shutil.which("gemini") is None:
        return False
    try:
        r = subprocess.run(
            ["gemini", "-p", "Say only: OK", "--approval-mode", "yolo", "-o", "text"],
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False

@pytest.fixture(scope="session")
def gemini_available() -> bool:
    return _probe_gemini()
```

### Pattern 3: Run Helper for Live Tests
**What:** Wraps subprocess invocation with standard arguments for headless CLI operation.
**When to use:** Live tests that invoke the Gemini CLI against a project.
**Example:**
```python
def run_gemini(
    prompt: str, cwd: Path, timeout: int = 180
) -> subprocess.CompletedProcess:
    """Run gemini -p in headless mode with auto-approve."""
    return subprocess.run(
        ["gemini", "-p", prompt, "--approval-mode", "yolo", "-o", "text"],
        cwd=str(cwd),
        capture_output=True, text=True, timeout=timeout,
    )
```

### Pattern 4: Failure Artifact Bundle
**What:** On live test failure, collects project snapshot, subprocess results, version info, diagnostics, and generates FAILURE_REPORT.md + .tar.gz archive.
**When to use:** Live Gemini E2E test (E2E-07) — critical for debugging failures in CI or when API access changes.
**Example:** See `_collect_failure_artifacts()` in `tests/integration/test_agent_rulez_e2e.py` lines 582-774.

### Anti-Patterns to Avoid
- **Sharing `cli_env` across files via conftest:** The existing pattern defines `cli_env` in the test file itself. A new Gemini E2E file should define its own identical fixture or import from a shared conftest. If creating a new file, duplicating the fixture is simpler and matches precedent.
- **Testing TOML validity by parsing output strings:** Always use `tomllib.loads()` — never manually check for syntax with regex.
- **Asserting exact file content:** Assert structural properties (keys exist, types correct, files present) rather than exact byte-for-byte content. Content details are covered by unit tests in `test_gemini_installer.py`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TOML validation | Custom TOML parser/regex | `tomllib.loads()` (stdlib) | Covers edge cases (multiline strings, escapes) |
| CLI testing | Manual subprocess for Click commands | `click.testing.CliRunner` | Captures exit code, output, handles exceptions |
| Failure artifacts | Ad-hoc print statements | `_collect_failure_artifacts()` pattern | Produces handoff-quality diagnostics |
| CLI availability check | `os.path.exists` on binary | `shutil.which()` + test invocation | `which()` respects PATH; invocation confirms auth |

## Common Pitfalls

### Pitfall 1: Gemini File Structure Differs from Claude/OpenCode
**What goes wrong:** Tests assert paths like `plugins/codebase-wizard/` or `.opencode/codebase-wizard/` for Gemini output.
**Why it happens:** Copy-pasting from existing tests without updating paths.
**How to avoid:** Gemini paths are:
- Global: `~/.gemini/codebase-wizard/` (or `$GEMINI_CONFIG_DIR/codebase-wizard/`)
- Project: `./.gemini/codebase-wizard/`
- Subdirs: `agent/` (not `agents/`), `command/` (not `commands/`), `skill/` (not `skills/`)
- Commands are `.toml` files, not `.md` files
**Warning signs:** Test passes for Claude/OpenCode but fails for Gemini with "file not found."

### Pitfall 2: TOML Validation Requires Python 3.11+
**What goes wrong:** `import tomllib` fails on Python 3.9/3.10.
**Why it happens:** `tomllib` was added in Python 3.11. The project supports `requires-python = ">=3.9"`.
**How to avoid:** Use conditional import: `try: import tomllib; except ImportError: import tomli as tomllib` — or skip TOML validation tests on older Python. The existing `test_gemini_installer.py` already uses `tomllib` without a fallback, suggesting 3.11+ is the de facto target.
**Warning signs:** CI matrix fails on Python 3.9/3.10.

### Pitfall 3: `--for all` and Status Tests Need Gemini Assertions
**What goes wrong:** Existing tests in `test_e2e_installer.py` pass but don't verify Gemini.
**Why it happens:** Tests were written before Gemini was added (Phase 12). They check `plugins/` and `.opencode/` but not `.gemini/`.
**How to avoid:** Update `test_cli_install_all` (line 53) to also assert `.gemini/codebase-wizard/` exists. Update `test_cli_status_after_install_all` (line 78) to assert `"gemini: installed"` in output.
**Warning signs:** `--for all` test passes but Gemini install is silently broken.

### Pitfall 4: Gemini CLI Noise in Headless Output
**What goes wrong:** Output parsing fails because Gemini CLI prints warning lines before the actual response.
**Why it happens:** Confirmed: `gemini -p` prints "YOLO mode is enabled..." and "Skill conflict detected..." before the response.
**How to avoid:** Don't assert exact output. Check `returncode == 0` and look for fixture-specific content (`calculate`, `src/main.py`) in stdout. Strip known noise prefixes.
**Warning signs:** Test fails intermittently due to changing warning messages.

### Pitfall 5: Gemini Install Needs Auth Credentials for Live Test
**What goes wrong:** Live test skips because probe fails — Gemini can't authenticate.
**Why it happens:** `isolated_home` fixture for Claude copies `.claude/auth.json`. Gemini stores auth in `~/.gemini/oauth_creds.json`.
**How to avoid:** The live test should either (a) copy `oauth_creds.json` to isolated home, or (b) not override HOME and instead just install to a project directory using `--project` flag, then run Gemini from that directory.
**Warning signs:** `_probe_gemini()` returns True (binary exists) but live test fails on auth.

### Pitfall 6: Gemini Skills Loading From Real HOME
**What goes wrong:** Gemini loads skills from `~/.gemini/skills/` and `~/.agents/skills/` even in test, causing conflicts.
**Why it happens:** Unlike Claude, Gemini doesn't have a `--plugin-dir` flag for isolation.
**How to avoid:** For the live test, accept that Gemini will load ambient skills. The test should verify wizard behavior (fixture-specific output), not skill isolation. The "Skill conflict detected" warning is benign.
**Warning signs:** Skill conflict warnings in output — harmless but noisy.

## Code Examples

### CliRunner Gemini Project Install Test
```python
# Pattern from test_e2e_installer.py, adapted for Gemini
def test_cli_install_gemini_project(cli_env):
    """E2E-01: CLI install --for gemini --project writes correct files to .gemini/."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "gemini", "--project"])
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    assert (
        cli_env / "cwd" / ".gemini" / "codebase-wizard" / "command" / "codebase-wizard.toml"
    ).exists(), "codebase-wizard.toml not found in command/ dir"
    assert (
        cli_env / "cwd" / ".gemini" / "codebase-wizard" / "agent" / "codebase-wizard-agent.md"
    ).exists(), "codebase-wizard-agent.md not found in agent/ dir"
    assert (
        cli_env / "cwd" / ".gemini" / "codebase-wizard" / "skill"
    ).is_dir(), "skill/ directory not found"
```

### TOML Validation
```python
# Pattern from test_gemini_installer.py, lines 352-359
import tomllib

def test_gemini_toml_valid(cli_env):
    """E2E-04: Generated TOML command files parse as valid TOML."""
    runner = CliRunner()
    runner.invoke(main, ["install", "--for", "gemini", "--project"])
    toml_files = list((cli_env / "cwd" / ".gemini" / "codebase-wizard" / "command").glob("*.toml"))
    assert len(toml_files) > 0, "No TOML files found after install"
    for toml_file in toml_files:
        content = toml_file.read_text()
        parsed = tomllib.loads(content)
        assert "prompt" in parsed, f"{toml_file.name} missing 'prompt' key"
```

### Agent Tool Name Validation
```python
import re

VALID_GEMINI_TOOLS = {
    "read_file", "write_file", "replace", "run_shell_command",
    "glob", "search_file_content", "google_web_search", "web_fetch",
    "write_todos", "ask_user",
}

def test_gemini_agent_snake_case_tools(cli_env):
    """E2E-05: Agent files have correct tools: array with Gemini snake_case names."""
    runner = CliRunner()
    runner.invoke(main, ["install", "--for", "gemini", "--project"])
    agent_dir = cli_env / "cwd" / ".gemini" / "codebase-wizard" / "agent"
    for agent_file in agent_dir.glob("*.md"):
        content = agent_file.read_text()
        # Extract tools from YAML frontmatter
        tools = re.findall(r'^\s+-\s+(\S+)', content, re.MULTILINE)
        for tool in tools:
            assert tool in VALID_GEMINI_TOOLS, (
                f"Agent {agent_file.name} has non-snake_case tool: {tool}"
            )
```

### Live Gemini Headless Invocation
```python
def run_gemini(
    prompt: str, cwd: Path, timeout: int = 180
) -> subprocess.CompletedProcess:
    """Run gemini in headless mode with auto-approve."""
    return subprocess.run(
        ["gemini", "-p", prompt, "--approval-mode", "yolo", "-o", "text"],
        cwd=str(cwd),
        capture_output=True, text=True, timeout=timeout,
    )
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ≥7.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_e2e_gemini_installer.py -v` |
| Full suite command | `pytest -m '' --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| E2E-01 | Gemini install (global + project) writes correct files | e2e (CliRunner) | `pytest tests/test_e2e_gemini_installer.py::test_cli_install_gemini_project -x` | ❌ Wave 0 |
| E2E-02 | Gemini uninstall removes directory cleanly | e2e (CliRunner) | `pytest tests/test_e2e_gemini_installer.py::test_cli_uninstall_gemini_project -x` | ❌ Wave 0 |
| E2E-03 | Status reports Gemini install state | e2e (CliRunner) | `pytest tests/test_e2e_gemini_installer.py::test_cli_status_gemini -x` | ❌ Wave 0 |
| E2E-04 | TOML command files are valid TOML | e2e (CliRunner) | `pytest tests/test_e2e_gemini_installer.py::test_gemini_toml_valid -x` | ❌ Wave 0 |
| E2E-05 | Agent files have snake_case tool names | e2e (CliRunner) | `pytest tests/test_e2e_gemini_installer.py::test_gemini_agent_snake_case_tools -x` | ❌ Wave 0 |
| E2E-06 | `--for all` includes Gemini | e2e (CliRunner) | `pytest tests/test_e2e_gemini_installer.py::test_cli_install_all_includes_gemini -x` | ❌ Wave 0 |
| E2E-07 | Live gemini headless produces wizard output | integration (slow) | `pytest -m slow tests/test_wizard_live.py::test_gemini_describe_creates_transcript -x` | ❌ Wave 0 |
| E2E-08 | All tests executed with results reported | meta | All above commands run and results captured | N/A |

### Sampling Rate
- **Per task commit:** `pytest tests/test_e2e_gemini_installer.py -v` (Plan 15-01)
- **Per wave merge:** `pytest -m '' --tb=short` (all tests including existing)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_e2e_gemini_installer.py` — covers E2E-01 through E2E-06
- [ ] Update `tests/test_e2e_installer.py` — existing `--for all` and status tests need Gemini assertions
- [ ] `tests/test_wizard_live.py` — add `_probe_gemini()`, `gemini_available`, `run_gemini()`, live tests
- [ ] `scripts/run_gemini_e2e_with_artifacts.sh` — artifact bundle script for E2E-07

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | All tests | ✓ | 3.12+ (inferred from tomllib usage) | — |
| pytest | All tests | ✓ | ≥7.0 (per pyproject.toml) | — |
| click | CliRunner tests | ✓ | ≥8.0 (per pyproject.toml) | — |
| tomllib | TOML validation | ✓ | stdlib (3.11+) | — |
| gemini CLI | E2E-07 live test | ✓ | 0.33.0 | Skip test if not available |
| Gemini API auth | E2E-07 live test | ✓ | oauth_creds.json present | Skip test if probe fails |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None — all dependencies are available.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `--allowed-tools` for Gemini CLI | `--policy` via Policy Engine | Gemini v0.30+ | `--allowed-tools` is deprecated but still works. Live test uses `--approval-mode yolo` instead. |

## Open Questions

1. **Gemini skill loading in isolated environments**
   - What we know: Gemini loads skills from `~/.gemini/skills/` and `~/.agents/skills/` automatically. No `--plugin-dir` flag exists.
   - What's unclear: Whether Gemini respects `GEMINI_CONFIG_DIR` env var for ALL config (including skills/agents), or just for some things.
   - Recommendation: For E2E-07 live test, don't try to isolate Gemini from ambient skills. Accept the "Skill conflict detected" warnings as benign. Test wizard behavior via fixture-specific content assertions.

2. **Gemini install to isolated home for live test**
   - What we know: Claude live tests use `isolated_home` fixture with HOME override. Gemini's `_resolve_dest("global")` respects `GEMINI_CONFIG_DIR` env var.
   - What's unclear: Whether overriding HOME or GEMINI_CONFIG_DIR breaks Gemini's auth flow.
   - Recommendation: Use `--project` install for the live test to avoid HOME override complexity. Install to the fixture project's `.gemini/` directory, then run `gemini -p` from that directory. Gemini will discover the project-local config automatically.

## Sources

### Primary (HIGH confidence)
- `tests/test_e2e_installer.py` — existing CliRunner pattern (9 tests, all passing)
- `tests/test_wizard_live.py` — existing live test pattern (probe, fixture, assert)
- `tests/integration/test_agent_rulez_e2e.py` — failure artifact bundle pattern
- `ai_codebase_mentor/converters/gemini.py` — GeminiInstaller API (install paths, file structure)
- `ai_codebase_mentor/cli.py` — CLI entry point confirming Gemini registration
- `gemini --help` output — confirmed `-p` flag, `--approval-mode yolo`, `-o text`
- `gemini -p "Say only: OK" --approval-mode yolo -o text` — confirmed working

### Secondary (MEDIUM confidence)
- `scripts/run_opencode_e2e_with_artifacts.sh` — shell script pattern for artifact runner

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are already in use in the project
- Architecture: HIGH — replicating established patterns with no new design decisions
- Pitfalls: HIGH — identified from direct code reading and live testing
- Validation: HIGH — test framework and commands are proven patterns

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable; no external dependency changes expected)
