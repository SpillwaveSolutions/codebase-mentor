---
phase: 12-e2e-integration-tests
plan: 01
subsystem: opencode-converter
tags: [tdd, opencode, context-fork, subtask, json-merge]
dependency_graph:
  requires: []
  provides: [_has_context_fork, _write_opencode_subtasks, opencode-subtask-mapping]
  affects: [ai_codebase_mentor/converters/opencode.py, tests/test_opencode_installer.py]
tech_stack:
  added: []
  patterns: [tdd-red-green, json-merge, frontmatter-parsing]
key_files:
  created: []
  modified:
    - ai_codebase_mentor/converters/opencode.py
    - tests/test_opencode_installer.py
decisions:
  - "_has_context_fork uses regex against raw frontmatter text — no YAML library needed (consistent with existing opencode.py patterns)"
  - "_write_opencode_subtasks writes after _write_opencode_permissions so both share the same opencode.json merge pattern"
  - "fork_commands collected as list during command iteration loop — O(n) with no second file read"
metrics:
  duration: "~2 minutes"
  completed: "2026-03-25"
  tasks_completed: 2
  files_modified: 2
---

# Phase 12 Plan 01: Context:Fork to Subtask Mapping Summary

**One-liner:** TDD fix mapping `context: fork` Claude frontmatter to `subtask: true` in OpenCode's `opencode.json` via `_has_context_fork()` and `_write_opencode_subtasks()`.

## What Was Built

The OpenCode converter previously silently dropped `context: fork` from Claude command frontmatter. All three codebase-wizard commands (`codebase-wizard`, `codebase-wizard-export`, `codebase-wizard-setup`) have `context: fork` in their frontmatter, meaning they were running in the primary session context instead of forking — polluting the user's conversation history.

This plan adds detection of `context: fork` during command iteration and merges `subtask: true` entries into `opencode.json`, fixing the behavior end-to-end.

## Tasks Completed

| Task | Description | Commit | Type |
|------|-------------|--------|------|
| 1 (RED) | Add 4 failing tests for context:fork subtask mapping | f704eb4 | test |
| 2 (GREEN) | Implement _has_context_fork() and _write_opencode_subtasks() | adcf47c | feat |

## Verification Results

- `python -m pytest tests/test_opencode_installer.py -v` — 18 passed (14 existing + 4 new)
- `python -m pytest tests/test_claude_installer.py -v` — 14 passed (zero regressions)
- `python -m pytest tests/ -v` — 32 passed, 0 failed

## Decisions Made

1. `_has_context_fork` uses regex against raw frontmatter text — no YAML library (consistent with existing `_convert_agent_frontmatter` pattern in the same file).
2. `_write_opencode_subtasks` is called after `_write_opencode_permissions` so both methods share the same merge-into-opencode.json pattern and the permission keys are already written before subtask keys are added.
3. `fork_commands` is collected as a list during the existing command copy loop — O(n) with no second file read pass.
4. `list` type annotation used instead of `list[str]` for Python 3.8 compatibility alignment with existing code style.

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check

- [x] `_has_context_fork` function exists in opencode.py
- [x] `_write_opencode_subtasks` method exists in opencode.py
- [x] 4 new test functions added to test_opencode_installer.py
- [x] All 18 OpenCode tests pass
- [x] All 14 Claude tests pass (zero regressions)
- [x] Full suite: 32 passed, 0 failed

## Self-Check: PASSED
