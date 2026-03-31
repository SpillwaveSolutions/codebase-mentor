---
phase: 15-gemini-e2e-integration-tests
plan: 02
status: complete
commit: eb79df6
---

# Plan 15-02 Summary: Live Gemini CLI Integration Test

## What was done

### Task 1: Added probe, fixture, and helper to `test_wizard_live.py`
- `_probe_gemini()` — checks `shutil.which("gemini")` then runs `gemini -p "Say only: OK" --approval-mode yolo -o text` with 30s timeout
- `gemini_available` fixture — session-scoped, caches probe result
- `run_gemini()` helper — wraps `subprocess.run` with `--approval-mode yolo -o text`

### Task 2: Added live test and artifact script
- `test_gemini_describe_creates_transcript` (WIZARD-06) — installs wizard with `--project`, runs `gemini -p "describe this codebase"`, asserts returncode 0 and fixture-specific content (calculate, main.py, sample, wizard, src/)
- `test_gemini_skip_when_no_auth` (WIZARD-07) — validates probe returns bool, skips gracefully when gemini unavailable
- `scripts/run_gemini_e2e_with_artifacts.sh` — prerequisite probes, runs slow test, captures FAILURE_REPORT.md + tarball on failure

## Test results

```
Gemini slow tests: 2 passed in 78.71s (gemini available and authenticated)
Full non-slow suite: 114 passed, 10 deselected in 10.87s
```

Both Gemini live tests ran to completion (not skipped). The live test:
1. Installed wizard into fixture project via `ai-codebase-mentor install --for gemini --project`
2. Ran `gemini -p "describe this codebase"` headless
3. Verified output contained fixture-specific content

## Requirements satisfied
- E2E-07: Live Gemini headless test exists, runs, and verifies fixture-specific output
