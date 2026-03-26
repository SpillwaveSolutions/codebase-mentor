---
phase: 13-live-wizard-cli-integration-tests
plan: 01
subsystem: testing
tags: [pytest, subprocess, claude-cli, opencode-cli, integration-tests, slow-marker, fixture-project]

# Dependency graph
requires:
  - phase: 12-e2e-integration-tests
    provides: test patterns (CliRunner, subprocess, tmp_path fixtures) used as reference
provides:
  - Live integration test suite (tests/test_wizard_live.py) with 5 @pytest.mark.slow tests
  - Auth probe functions that detect claude/opencode CLI availability at import time
  - Sample fixture project (tests/fixtures/sample-wizard-project/) for wizard invocation
  - pytest slow marker registered in pyproject.toml for CI gating
affects: [ci-configuration, test-workflows, developer-onboarding]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Auth probe pattern: module-level _probe_claude()/_probe_opencode() detect CLI auth via cheap probe call at import time
    - Natural language invocation: claude -p uses NL prompts (not slash commands) to trigger wizard skill
    - Graceful skip: pytest.mark.skipif gates live tests on CLAUDE_AVAILABLE/OPENCODE_AVAILABLE booleans
    - Fixture isolation: shutil.copytree from static fixtures dir into tmp_path; pre-create .code-wizard/ storage

key-files:
  created:
    - tests/test_wizard_live.py
    - tests/fixtures/sample-wizard-project/README.md
    - tests/fixtures/sample-wizard-project/src/main.py
  modified:
    - pyproject.toml

key-decisions:
  - "Natural language prompts used for claude -p invocation -- slash commands (/codebase-wizard) not supported in -p mode"
  - "opencode run uses --dir flag without --command flag (--command hangs silently)"
  - "Auth probe runs at module import time (not fixture) so skip decisions are made at collection time"
  - "Fixture project pre-creates .code-wizard/ with config.json to ensure wizard writes to expected path"
  - "Content assertions: file existence + minimum byte count (>200) + at least one # heading -- no exact string matching"
  - "--max-budget-usd 0.50 used for claude -p tests (0.01 for probe, 0.50 for actual wizard tests)"

patterns-established:
  - "Slow test gate: @pytest.mark.slow + pytest -m 'not slow' skips all live tests in fast CI"
  - "Auth probe: shutil.which() check + cheap subprocess call (timeout=30) + try/except returning False"
  - "Structural assertions only: never assert on exact LLM output text, only existence + size + heading presence"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-03-26
---

# Phase 13 Plan 01: Live Wizard CLI Integration Tests Summary

**Live E2E test suite with 5 @pytest.mark.slow tests invoking claude -p and opencode run against a sample fixture project via subprocess, with auth probe guards and structural output assertions**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-26T04:53:57Z
- **Completed:** 2026-03-26T04:56:30Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `tests/test_wizard_live.py` with 5 live integration tests (2 claude, 1 opencode, 2 skip-logic verification)
- Auth probe functions `_probe_claude()` and `_probe_opencode()` detect CLI availability at module import time; tests skip gracefully when auth is missing
- Sample fixture project (`tests/fixtures/sample-wizard-project/`) provides minimal 2-file Python project for wizard invocation
- Registered `slow` pytest marker in `pyproject.toml` so `pytest -m 'not slow'` excludes all live tests from fast CI
- All 49 existing fast tests continue to pass with 5 slow tests deselected

## Task Commits

Each task was committed atomically:

1. **Task 1: Create fixture project and register slow marker** - `40e4787` (feat)
2. **Task 2: Create tests/test_wizard_live.py with live integration tests** - `f35da3f` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `tests/test_wizard_live.py` - 5 live integration tests with auth probes, skip guards, run_claude()/run_opencode() helpers, wizard_project fixture
- `tests/fixtures/sample-wizard-project/README.md` - Minimal project README for wizard to describe (7 lines)
- `tests/fixtures/sample-wizard-project/src/main.py` - Minimal Python source with calculate() function (9 lines)
- `pyproject.toml` - Added [tool.pytest.ini_options] section with slow marker registration

## Decisions Made

- Natural language prompts used for `claude -p` -- slash commands (`/codebase-wizard`) return "Unknown skill" in -p mode and are not supported
- `opencode run` uses `--dir` flag to set working directory; `--command` flag hangs silently and is excluded
- Auth probe runs at module import time (not per-test fixture) so pytest collection-time skip decisions work correctly
- Fixture project pre-creates `.code-wizard/sessions/`, `.code-wizard/docs/`, and `config.json` with `resolved_storage: .code-wizard` to ensure wizard writes output to expected location
- Content assertions check only: file existence, minimum byte count (>200), at least one `# ` heading line -- no exact string matching (LLM output is non-deterministic)
- `--max-budget-usd 0.50` for wizard tests; `0.01` for probe calls (verified sufficient for 3-file fixture project)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Running slow tests requires `claude` and `opencode` CLIs to be installed and authenticated, but this is documented in the test file's module docstring.

## Next Phase Readiness

- Phase 13 Plan 01 is the only plan in Phase 13; phase is complete
- Live tests can be run with: `pytest -m slow tests/test_wizard_live.py`
- Fast CI can exclude live tests with: `pytest -m 'not slow'`
- For CI with ANTHROPIC_API_KEY available, a separate `test-wizard-live.yml` workflow could gate on the secret presence (noted as open question in RESEARCH.md)

---
*Phase: 13-live-wizard-cli-integration-tests*
*Completed: 2026-03-26*
