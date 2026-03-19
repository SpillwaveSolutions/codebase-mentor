---
phase: 01-core-wizard-skill
plan: 01
subsystem: skill
tags: [markdown, skill, wizard, answer-loop, question-bank, file-mode, describe, explore]

# Dependency graph
requires: []
provides:
  - Answer loop behavioral contract (code-block-first anchor pattern on every response)
  - Research priority tier system (Agent Brain → Perplexity → scan → parse)
  - Mode detection (--describe, --explore, --file, no-args)
  - Describe mode question bank with CODEBASE.md output schema
  - Explore mode learning-order tour with TOUR.md output schema
  - File mode (--file <path>) with FILE-NOTES.md output schema
  - Updated SKILL.md frontmatter (name: codebase-wizard, full trigger list, output docs)
affects: [plugin/SKILL.md, plugin/references]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Answer loop: find artifact → show code block with anchor → explain → connections → predict next"
    - "Lazy reference loading: one reference file per mode, loaded on-demand"
    - "Anchor format: // file → class/section → method/subsection → line range"

key-files:
  created:
    - plugin/references/describe-questions.md
    - plugin/references/explore-questions.md
  modified:
    - plugin/SKILL.md

key-decisions:
  - "Extend existing SKILL.md rather than replace — preserves the 5-phase foundation already in place"
  - "Lazy-load reference files per mode — avoids context bloat when only one mode is active"
  - "Answer loop enforced on every response with no exceptions — consistent UX across all modes"
  - "Use {resolved_storage}/docs/{session_id}/ for all output paths — consistent storage contract"

patterns-established:
  - "Code block with anchor shown BEFORE any explanation text (INVARIANT-1)"
  - "Every response ends with 2-3 specific 'Next — want to:' options (INVARIANT-3)"
  - "SESSION-TRANSCRIPT.md generated alongside every mode's primary output"

# Metrics
duration: 85min
completed: 2026-03-19
---

# Phase 01 Plan 01: Core Wizard Skill Summary

**Answer loop, mode detection, question banks, and File mode built — codebase-mentor skill renamed to codebase-wizard with full trigger list and output doc contracts.**

## Performance

- **Duration:** ~85 min (parallel wave execution)
- **Started:** 2026-03-19T16:47:09Z
- **Completed:** 2026-03-19T18:12:45Z
- **Tasks:** 6 (across 2 parallel waves)
- **Files modified:** 3 (SKILL.md + 2 new references)

## Accomplishments

- Added **Answer Loop** section to SKILL.md — 5-step behavioral contract (find artifact → show code block with anchor → explain → connections → predict next) enforced on every response
- Added **Research Priority** section — 4-tier tool order: Agent Brain → Perplexity → codebase scan → markdown parse, each with fallback and surfacing rules
- Added **Mode Detection** section — routes `--describe`, `--explore`, `--file <path>`, and no-args to the correct reference file
- Created **`describe-questions.md`** — 7-question bank (Ownership, Intent, Domain Terms, Constraints) with deterministic follow-up logic and CODEBASE.md output schema (8 sections)
- Created **`explore-questions.md`** — 5-step learning-order tour (app → entry → auth → data → first change) with navigation, mid-tour interrupts, and TOUR.md output schema
- Added **Phase 2b: File Mode** to SKILL.md — section-by-section walk-through of markdown files with FILE-NOTES.md output
- Updated **SKILL.md frontmatter** — renamed from `codebase-mentor` to `codebase-wizard`, expanded trigger list, documented all 4 output artifacts

## Task Commits

Each task was committed atomically (parallel wave execution):

1. **Task 1: Answer loop + research priority + mode detection** - `155369d` (feat)
2. **Task 2: Describe mode question bank** - `1cc3087` (feat)
3. **Task 3: Explore mode tour structure** - `ec8affb` (feat)
4. **GSD sync: Initialize planning structure** - `3a2d454` (chore)
5. **Task 4+5: File mode + frontmatter update** - `46989dd` (feat)
6. **STATE.md: Mark phase complete** - `b8cb41a` (chore)

## Files Created/Modified

- `plugin/SKILL.md` — Extended with Answer Loop, Research Priority, Mode Detection, Phase 2b (File Mode), updated frontmatter
- `plugin/references/describe-questions.md` — Describe mode question bank with CODEBASE.md output schema (8 sections)
- `plugin/references/explore-questions.md` — Explore mode 5-step learning-order tour with TOUR.md output schema

## Decisions Made

- Extended rather than replaced existing SKILL.md — the 5-phase foundation (scan → Q&A → nav → tutorial → persist) was already solid; new sections added between existing phases
- Lazy reference loading kept — `describe-questions.md` and `explore-questions.md` are loaded on-demand per mode, not both at once
- `{resolved_storage}/docs/{session_id}/` used consistently across all mode output schemas — single storage contract for all artifacts

## Deviations from Plan

None — all 6 tasks executed as specified. Verification (Task 6) confirmed all 8 invariants pass.

## Verification Results

All invariants verified PASS:
- INVARIANT-1: Code block with anchor appears before explanation ✓
- INVARIANT-2: Anchor format `// file → class/section → method → LOC` defined ✓
- INVARIANT-3: "Next — want to:" with 2-3 specific options ✓
- INVARIANT-4: Explanation limited to 3-5 sentences ✓
- INVARIANT-5: `→ calls:` and `→ called by:` lines present ✓
- SESSION-TRANSCRIPT.md referenced in all 4 expected locations ✓
- `{resolved_storage}` used consistently (4 occurrences, identical path) ✓
- CODEBASE.md schema has all 8 sections ✓

## Issues Encountered

None.

## User Setup Required

None — no external dependencies or configuration required.

## Next Phase Readiness

Phase 2 (Capture + Synthesis) is ready to start:
- Agent Rulez integration for hook-based auto-capture (PostToolUse/Stop hooks)
- `/export` command to synthesize raw JSON/YAML logs → SESSION-TRANSCRIPT.md + CODEBASE.md
- `/setup` command to install Agent Rulez and write `settings.local.json`
- Sample Agent Rulez YAML config ships with the plugin

---
*Phase: 01-core-wizard-skill*
*Completed: 2026-03-19*

## Self-Check: PASSED
