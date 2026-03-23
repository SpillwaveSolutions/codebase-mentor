---
phase: quick
plan: 260323-mew
type: execute
subsystem: planning
tags: [state, hotfix, v1.2.1, v1.2.2, v1.2.3, documentation]
dependency_graph:
  requires: []
  provides: [accurate-project-history-through-v1.2.3]
  affects: [.planning/STATE.md]
tech_stack:
  added: []
  patterns: []
key_files:
  modified:
    - .planning/STATE.md
decisions:
  - "STATE.md is the single source of truth for hotfix history; no separate SUMMARY artifact needed beyond this file"
metrics:
  completed: 2026-03-23
---

# Quick Task 260323-mew: Document v1.2.1/v1.2.2/v1.2.3 Hotfix Releases Summary

**One-liner:** Updated STATE.md to record three post-v1.2.0 hotfix releases (OpenCode directory fix, Claude registry fix, marketplace ID + frontmatter fix) with v1.2.3 as current published version.

## What Was Done

Updated `.planning/STATE.md` with the three hotfix releases shipped after the v1.2.0 milestone:

- **v1.2.1** — OpenCode singular directory fix (`agents/` → `agent/`, `skills/` → `skill/`); 6 test assertions updated; all 14 OpenCode tests pass
- **v1.2.2** — Claude plugin registry fix; installer now writes registry entries via `_register_plugin()`, `_register_marketplace()`, and related helpers; 4 new tests; all 13 Claude tests pass
- **v1.2.3** — Correct marketplace ID (`codebase-wizard@codebase-mentor`) and plugin component frontmatter fix (description fields, model+color fields, kebab-case skill names); all 27 tests pass; tagged and GitHub release created

## Changes to STATE.md

1. `last_updated` updated to 2026-03-23T00:00:00.000Z
2. Three rows added to Quick Tasks Completed table (260323-v121, 260323-v122, 260323-v123)
3. Notes section updated: v1.2.3 is current published version; 27 tests pass; v1.3 milestone is next

## Tasks

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Update STATE.md with v1.2.1/1.2.2/1.2.3 hotfix history | COMPLETE | 957779b |

## Verification

- `v1.2.1`, `v1.2.2`, `v1.2.3` each appear in STATE.md: 5 matches total
- `codebase-wizard@codebase-mentor` appears: 2 matches
- `27 tests pass` appears: 2 matches
- `v1.3 milestone` appears: 1 match

All four verification checks from the plan passed.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `.planning/STATE.md` exists and contains all required content
- Commit 957779b exists in git log
