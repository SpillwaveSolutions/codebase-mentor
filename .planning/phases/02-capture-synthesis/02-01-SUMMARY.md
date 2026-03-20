---
phase: 02-capture-synthesis
plan: 01
subsystem: plugin
tags: [agent-rulez, yaml, bash, markdown, hooks, capture, synthesis, wizard]

# Dependency graph
requires:
  - phase: 01-core-skill
    provides: SKILL.md wizard logic, describe-questions.md, explore-questions.md, and mode definitions (describe, explore, file)
provides:
  - plugin/setup/agent-rulez-sample.yaml — PostToolUse + Stop hook config template with {resolved_storage} placeholder
  - plugin/setup/setup.sh — storage resolution, Agent Rulez install, hook registration, settings.local.json writer (6 steps)
  - plugin/commands/codebase-wizard-export.md — /export command synthesizing raw session JSON into SESSION-TRANSCRIPT.md, CODEBASE.md, TOUR.md, or FILE-NOTES.md
  - plugin/commands/codebase-wizard-setup.md — one-time onboarding command running main context (no context:fork)
affects:
  - 03-permission-agents — will define codebase-wizard-agent.md that governs allowed_tools used by codebase-wizard-export.md
  - 03-permission-agents — will define codebase-wizard.md which runs in context:fork + agent: codebase-wizard-agent

# Tech tracking
tech-stack:
  added: [Agent Rulez hooks, bash, YAML hook config]
  patterns:
    - Template YAML with placeholder substituted at deploy time via sed
    - Storage resolution via ordered directory check (code-wizard/ then .claude/code-wizard/)
    - Command separation — main context for setup (install permissions), fork context for export (scoped agent)
    - Version-guarded session JSON format for forward compatibility

key-files:
  created:
    - plugin/setup/agent-rulez-sample.yaml
    - plugin/setup/setup.sh
    - plugin/commands/codebase-wizard-export.md
    - plugin/commands/codebase-wizard-setup.md
  modified: []

key-decisions:
  - "codebase-wizard-setup.md has no context:fork — main context required to write settings.local.json and install Agent Rulez"
  - "sed pipe separator | used in substitution (not /) to avoid conflicts with path slashes in resolved_storage"
  - "on_error: warn on PostToolUse hook — capture failures notify user but do not abort sessions"
  - "SESSION-TRANSCRIPT.md always generated regardless of mode — universal output for every session"
  - "{resolved_storage} placeholder used throughout — never bare {storage} — substituted by setup.sh at deploy time"

patterns-established:
  - "Template config with placeholder: agent-rulez-sample.yaml uses {resolved_storage}; setup.sh substitutes at deploy time"
  - "Dual-location storage check: always check .code-wizard/ then .claude/code-wizard/ in order"
  - "Command context separation: one-time install commands in main context, regular session commands in fork context"

requirements-completed: []

# Metrics
duration: 3min
completed: 2026-03-19
---

# Phase 2 Plan 1: Capture + Synthesis

**Agent Rulez hook config template, 6-step setup.sh installer, and two commands — /codebase-wizard-export synthesizing raw JSON into SESSION-TRANSCRIPT.md + CODEBASE.md/TOUR.md/FILE-NOTES.md, and /codebase-wizard-setup as one-time main-context onboarding**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-20T00:29:30Z
- **Completed:** 2026-03-20T00:32:13Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- PostToolUse + Stop hook config template with `{resolved_storage}` placeholder, `on_error: warn`, and native `{date}`/`{repo}` variable documentation
- 6-step setup.sh: storage resolution (check both locations, prompt user), config.json write, `rulez install`, sed-substituted YAML deploy, hook registration, settings.local.json with scoped permissions
- `/codebase-wizard-export` with `--latest`/`--session`/`--all` args, config.json discovery, version guard, and mode-aware synthesis (CODEBASE.md, TOUR.md, FILE-NOTES.md) plus universal SESSION-TRANSCRIPT.md
- `/codebase-wizard-setup` runs in main context (no `context: fork`) with comment explaining why — necessary for writing settings.local.json and installing Agent Rulez

## Task Commits

Each task was committed atomically:

1. **Task 1: Create plugin/setup/agent-rulez-sample.yaml** - `73ff741` (feat)
2. **Task 2: Create plugin/setup/setup.sh** - `33020ae` (feat)
3. **Task 3: Create plugin/commands/codebase-wizard-export.md** - `2e5f050` (feat)
4. **Task 4: Create plugin/commands/codebase-wizard-setup.md** - `2944372` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `plugin/setup/agent-rulez-sample.yaml` — PostToolUse and Stop hook config template with `{resolved_storage}` placeholder
- `plugin/setup/setup.sh` — executable bash script with 6-step wizard installation flow
- `plugin/commands/codebase-wizard-export.md` — slash command with `context: fork`, `agent: codebase-wizard-agent`, and full synthesis pipeline
- `plugin/commands/codebase-wizard-setup.md` — one-time onboarding slash command in main context (no `context: fork`)

## Decisions Made

- `codebase-wizard-setup.md` has no `context: fork` and no `agent:` field — it runs in main context because it must write `settings.local.json` and install Agent Rulez, which are outside the scoped wizard agent permissions
- `sed` uses pipe separator (`|`) for path substitution (`s|{resolved_storage}|$RESOLVED_STORAGE|g`) to avoid conflicts with forward slashes in directory paths
- `on_error: warn` on PostToolUse hook — capture failures display a warning but never abort wizard sessions; in-memory buffer fallback noted in YAML comments
- SESSION-TRANSCRIPT.md always generated for every mode, not conditionally — universal output regardless of describe/explore/file mode
- All output paths use `{resolved_storage}` consistently — no bare `{storage}` references anywhere

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required at this phase. Agent Rulez is installed by setup.sh at onboarding time.

## Next Phase Readiness

- Capture + synthesis pipeline is complete — hooks, setup script, export command, and setup command all delivered
- Phase 3 can now define `plugin/agents/codebase-wizard-agent.md` to provide the policy island referenced in `codebase-wizard-export.md` frontmatter (`agent: codebase-wizard-agent`)
- Phase 3 can also define `plugin/commands/codebase-wizard.md` (the main wizard command with `context: fork + agent: codebase-wizard-agent`)
- No blockers for Phase 3

---
*Phase: 02-capture-synthesis*
*Completed: 2026-03-19*

## Self-Check: PASSED

- FOUND: plugin/setup/agent-rulez-sample.yaml
- FOUND: plugin/setup/setup.sh
- FOUND: plugin/commands/codebase-wizard-export.md
- FOUND: plugin/commands/codebase-wizard-setup.md
- FOUND: .planning/phases/02-capture-synthesis/02-01-SUMMARY.md
- FOUND commit 73ff741: feat(02-01): add agent-rulez-sample.yaml hook config template
- FOUND commit 33020ae: feat(02-01): add setup.sh
- FOUND commit 2e5f050: feat(02-01): add /codebase-wizard-export command with session synthesis
- FOUND commit 2944372: feat(02-01): add /codebase-wizard-setup command — one-time onboarding
