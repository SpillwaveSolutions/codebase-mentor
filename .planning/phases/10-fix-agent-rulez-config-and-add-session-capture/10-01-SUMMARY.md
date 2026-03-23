---
phase: 10-fix-agent-rulez-config-and-add-session-capture
plan: 01
subsystem: agent-config
tags: [agent-rulez, session-capture, hooks, bash-script, codebase-wizard]

# Dependency graph
requires: []
provides:
  - Correct Agent Rulez rules: schema with block-force-push, block-recursive-delete, capture-session rules
  - capture-session.sh script reads PostToolUse JSON from stdin and appends to session file
  - setup.sh deploy_hooks() using rulez install (not rulez hook add) and deploying capture-session.sh
  - SKILL.md Answer Loop Step 6 with Write-tool fallback for environments without Agent Rulez
affects: [configuring-codebase-wizard, explaining-codebase, codebase-wizard-setup]

# Tech tracking
tech-stack:
  added: [agent-rulez rules: schema, capture-session.sh bash script]
  patterns:
    - Agent Rulez run: action with stdin JSON capture script
    - Write-tool fallback for session logging when Agent Rulez absent
    - Source/installed copy sync pattern (ai_codebase_mentor/plugin/ mirrors plugins/codebase-wizard/)

key-files:
  created:
    - ai_codebase_mentor/plugin/skills/configuring-codebase-wizard/scripts/capture-session.sh
    - plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/capture-session.sh
  modified:
    - ai_codebase_mentor/plugin/skills/configuring-codebase-wizard/scripts/agent-rulez-sample.yaml
    - plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/agent-rulez-sample.yaml
    - ai_codebase_mentor/plugin/skills/configuring-codebase-wizard/scripts/setup.sh
    - plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/setup.sh
    - ai_codebase_mentor/plugin/skills/explaining-codebase/SKILL.md
    - plugins/codebase-wizard/skills/explaining-codebase/SKILL.md

key-decisions:
  - "Agent Rulez rules: top-level key (not hooks:) with version/settings/rules structure — confirmed via rulez debug first-run testing"
  - "capture-session.sh uses export SESSION_FILE/INPUT before python3 block to avoid shell interpolation inside Python string"
  - "rulez install is the correct activation command — rulez hook add subcommand does not exist"
  - "Write-tool fallback in SKILL.md Answer Loop Step 6 ensures session logging works even without Agent Rulez installed"

patterns-established:
  - "Agent Rulez run: action pattern: script reads stdin via INPUT=$(cat), extracts fields via python3 JSON parse"
  - "Session file path pattern: .code-wizard/sessions/{session_id}.json with version/session_id/turns structure"
  - "Deploy pattern: cp (not sed) for YAML deployment since template variables removed"

requirements-completed: [RULEZ-01, RULEZ-02, RULEZ-03, RULEZ-04]

# Metrics
duration: 2min
completed: 2026-03-23
---

# Phase 10 Plan 01: Fix Agent Rulez Config and Add Session Capture Summary

**Rewrote agent-rulez-sample.yaml with correct rules: schema (3 rules: 2 block + 1 capture-session run:), created capture-session.sh for PostToolUse stdin capture, fixed setup.sh to use rulez install, and added Write-tool fallback in SKILL.md Answer Loop Step 6.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-23T23:04:38Z
- **Completed:** 2026-03-23T23:06:17Z
- **Tasks:** 3
- **Files modified:** 8 (4 source + 4 installed copies)

## Accomplishments

- Replaced wrong hooks: YAML schema with correct version/settings/rules: structure containing 3 rules
- Created capture-session.sh that reads PostToolUse JSON from stdin and appends turns to session file
- Fixed setup.sh deploy_hooks() to use rulez install, plain cp (not sed), and deploy capture-session.sh
- Added Step 6 to SKILL.md Answer Loop with Write-tool fallback for Agent Rulez-absent environments

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite agent-rulez-sample.yaml and create capture-session.sh** - `67cec28` (feat)
2. **Task 2: Fix setup.sh — remove rulez hook add, deploy capture-session.sh** - `22a3d0c` (fix)
3. **Task 3: Add Write-tool session capture fallback to SKILL.md Answer Loop** - `669664a` (feat)

**Plan metadata:** *(final docs commit to follow)*

## Files Created/Modified

- `ai_codebase_mentor/plugin/skills/configuring-codebase-wizard/scripts/agent-rulez-sample.yaml` — Rewritten with rules: schema; 3 rules: block-force-push, block-recursive-delete, capture-session
- `ai_codebase_mentor/plugin/skills/configuring-codebase-wizard/scripts/capture-session.sh` — NEW: reads PostToolUse JSON from stdin, extracts session_id, appends turn to .code-wizard/sessions/{id}.json
- `ai_codebase_mentor/plugin/skills/configuring-codebase-wizard/scripts/setup.sh` — Fixed deploy_hooks(): uses rulez install, cp (not sed), deploys capture-session.sh to $RESOLVED_STORAGE/scripts/
- `ai_codebase_mentor/plugin/skills/explaining-codebase/SKILL.md` — Added Step 6 (Capture Turn) to Answer Loop with Agent Rulez / Write-tool fallback pattern
- `plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/agent-rulez-sample.yaml` — Synced installed copy
- `plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/capture-session.sh` — Synced installed copy (NEW)
- `plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/setup.sh` — Synced installed copy
- `plugins/codebase-wizard/skills/explaining-codebase/SKILL.md` — Synced installed copy

## Decisions Made

- **rules: not hooks:** — Agent Rulez YAML top-level key is `rules:` not `hooks:`. Confirmed via first-run testing and `rulez debug`. All old `hooks:`, `action: append`, `action: notify` keys removed.
- **rulez install only** — The `rulez hook add` subcommand does not exist. The correct command is `rulez install` which reads `.claude/hooks.yaml`. Removed all references to the nonexistent subcommand.
- **Export via environment variables** — The capture-session.sh python3 inline script uses `export SESSION_FILE` and `export INPUT` before the python3 -c call rather than shell interpolation inside the Python string (avoids quoting hazards with JSON content).
- **Write-tool fallback for portability** — Step 6 in SKILL.md ensures session logging works in environments where Agent Rulez is not installed, using the Write tool directly after each answer turn.

## Deviations from Plan

None — plan executed exactly as written. All acceptance criteria met on first attempt.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. Agent Rulez must be installed separately by the user (`pip install agent-rulez` or equivalent), but this was already the case before this plan.

## Next Phase Readiness

- Phase 10 complete — all 4 requirements satisfied (RULEZ-01 through RULEZ-04)
- Agent Rulez configuration is now correct and functional
- Session capture works via both Agent Rulez run: hook and Write-tool fallback
- Both source and installed copies are in sync (all diffs return 0)
- Ready for v1.3 milestone (Codex subagents) per STATE.md notes

---
*Phase: 10-fix-agent-rulez-config-and-add-session-capture*
*Completed: 2026-03-23*
