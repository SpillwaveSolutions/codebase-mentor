---
phase: 13-live-wizard-cli-integration-tests
verified: 2026-03-26T05:30:00Z
status: passed
score: 6/6 must-haves verified
gaps: []
human_verification:
  - test: "Run slow tests against a live authenticated environment"
    expected: "claude -p creates SESSION-TRANSCRIPT.md in .code-wizard/docs/claude-test-001/ with >200 bytes and at least one # heading; opencode run creates SESSION-TRANSCRIPT.md in .code-wizard/docs/opencode-test-001/"
    why_human: "Tests make real LLM API calls that produce non-deterministic output; can only verify structural presence and minimum size at runtime"
---

# Phase 13: Live Wizard CLI Integration Tests — Verification Report

**Phase Goal:** Create live E2E integration tests that invoke `claude -p` and `opencode run` in headless mode against a sample fixture project, verifying that the codebase-wizard skill produces SESSION-TRANSCRIPT.md output with expected structural content. Tests are marked @pytest.mark.slow and skip gracefully when auth is not available.
**Verified:** 2026-03-26T05:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                        | Status     | Evidence                                                                                                    |
| --- | ---------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------- |
| 1   | `pytest -m slow` collects tests from test_wizard_live.py                    | VERIFIED   | `pytest --co -q` collected exactly 5 tests; collection took 15.20s (probes run at import)                  |
| 2   | `pytest -m 'not slow'` skips all live wizard tests                          | VERIFIED   | `pytest -m 'not slow' tests/` shows "49 passed, 5 deselected" — all slow tests excluded                    |
| 3   | Tests skip gracefully when claude/opencode CLI not authenticated             | VERIFIED   | `skip_no_claude` / `skip_no_opencode` skipif markers gate on `CLAUDE_AVAILABLE` / `OPENCODE_AVAILABLE` bools evaluated at module import; `test_claude_skip_when_no_auth` and `test_opencode_skip_when_no_auth` prove skip logic without auth |
| 4   | claude -p describe mode test creates SESSION-TRANSCRIPT.md with structural content | VERIFIED | `test_claude_describe_creates_transcript` asserts: returncode==0, file exists at .code-wizard/docs/claude-test-001/SESSION-TRANSCRIPT.md, len>200, at least one line starts with "# " |
| 5   | opencode run describe mode test creates SESSION-TRANSCRIPT.md               | VERIFIED   | `test_opencode_describe_creates_transcript` asserts: returncode==0, file exists at .code-wizard/docs/opencode-test-001/SESSION-TRANSCRIPT.md, len>200 |
| 6   | Fixture project exists with README.md and src/main.py                       | VERIFIED   | Both files present: README.md (7 lines), src/main.py (9 lines, contains `def calculate`)                   |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact                                                    | Expected                                     | Min Lines | Status     | Details                                             |
| ----------------------------------------------------------- | -------------------------------------------- | --------- | ---------- | --------------------------------------------------- |
| `tests/fixtures/sample-wizard-project/README.md`           | Minimal project README for wizard to describe | 5         | VERIFIED   | 7 lines; contains "# Sample Wizard Project"        |
| `tests/fixtures/sample-wizard-project/src/main.py`         | Minimal Python source for wizard to analyze  | 8         | VERIFIED   | 9 lines; contains `def calculate(a, b)` with docstring and return |
| `tests/test_wizard_live.py`                                 | Live integration tests with @pytest.mark.slow | 120       | VERIFIED   | 236 lines; 5 tests collected, all @pytest.mark.slow |
| `pyproject.toml`                                            | slow marker registration                     | —         | VERIFIED   | `[tool.pytest.ini_options]` section present at line 47; `markers = ["slow: ..."]` at line 48–50 |

### Key Link Verification

| From                        | To                                                  | Via                                            | Status     | Details                                                                                                       |
| --------------------------- | --------------------------------------------------- | ---------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| `tests/test_wizard_live.py` | `tests/fixtures/sample-wizard-project/`            | `FIXTURE_PROJECT` path constant + `shutil.copytree` | WIRED  | Line 19: `FIXTURE_PROJECT = Path(__file__).parent / "fixtures" / "sample-wizard-project"`; line 83: `shutil.copytree(FIXTURE_PROJECT, project)` |
| `tests/test_wizard_live.py` | `claude -p` subprocess                             | `run_claude` helper calling `subprocess.run`   | WIRED      | Lines 33, 103: `subprocess.run(["claude", "-p", prompt, "--dangerously-skip-permissions", "--max-budget-usd", ...])` |
| `tests/test_wizard_live.py` | `opencode run` subprocess                          | `run_opencode` helper calling `subprocess.run` | WIRED      | Lines 52, 119: `subprocess.run(["opencode", "run", message, "--dir", str(cwd)])` — no `--command` flag       |
| `pyproject.toml`            | `tests/test_wizard_live.py`                        | pytest marker registration enables `-m slow`   | WIRED      | Lines 48–50 of pyproject.toml register `slow` marker; `pytest -m 'not slow'` deselects 5 tests confirming registration works |

### Requirements Coverage

Phase 13 has no formal requirement IDs (self-describing test phase as documented in PLAN frontmatter: `requirements: []`). All goal behaviors are directly verified via must-haves above.

### Anti-Patterns Found

No anti-patterns detected. Scan of all four created/modified files found:
- No TODO / FIXME / XXX / HACK / PLACEHOLDER comments
- No stub implementations (return null / return {} / empty handlers)
- No slash commands (`/codebase-wizard` count: 0)
- No `--command` flag usage (count: 0)

### Human Verification Required

#### 1. Live Slow Test Execution

**Test:** With `claude` CLI installed and authenticated, run: `pytest -m slow tests/test_wizard_live.py -v`
**Expected:** `test_claude_describe_creates_transcript` passes with SESSION-TRANSCRIPT.md written to `.code-wizard/docs/claude-test-001/`, content >200 bytes, at least one `# ` heading present. `test_claude_describe_creates_codebase_md` passes similarly. `test_claude_skip_when_no_auth` passes (either confirming `shutil.which("claude")` is not None, or skipping with the expected skip message).
**Why human:** Tests make real LLM API calls over the network; output is non-deterministic. Cannot verify the actual SESSION-TRANSCRIPT.md content shape programmatically without auth.

#### 2. OpenCode Live Test

**Test:** With `opencode` CLI installed and authenticated, run: `pytest -m slow tests/test_wizard_live.py::test_opencode_describe_creates_transcript -v`
**Expected:** `opencode run` completes with returncode 0 and writes SESSION-TRANSCRIPT.md to `.code-wizard/docs/opencode-test-001/` with >200 bytes.
**Why human:** Requires opencode auth; non-deterministic LLM output.

### Gaps Summary

No gaps. All six observable truths are verified at all three artifact levels (exists, substantive, wired). The test collection run confirms pytest correctly gates 5 slow tests behind `-m slow` and the fast suite of 49 tests runs cleanly with `5 deselected`. Key links are all confirmed present in the actual source. No anti-patterns found in any created file.

The only remaining work is live execution with real CLI auth, which is inherently a human/CI verification step and not a gap in the implementation.

---

_Verified: 2026-03-26T05:30:00Z_
_Verifier: Claude (gsd-verifier)_
