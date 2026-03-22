---
phase: 08-opencode-converter
plan: 01
subsystem: converters
tags: [opencode, tdd, installer, converter, yaml, frontmatter, cli]

# Dependency graph
requires:
  - phase: 07-github-actions
    provides: "ClaudeInstaller pattern, RuntimeInstaller ABC, test_claude_installer.py structure"
provides:
  - "OpenCodeInstaller class implementing RuntimeInstaller ABC"
  - "13-case TDD test suite for OpenCode converter"
  - "CLI wired to support --for opencode and --for all"
affects:
  - "08-02 (CLI wiring plan)"
  - "09-pypi-publish"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED->GREEN cycle: write 13 failing tests, then implement to pass all"
    - "YAML frontmatter line-by-line parsing with block scalar state tracking"
    - "Tool name conversion: strip path scope, apply SPECIAL_MAPPINGS, lowercase default"
    - "idempotent install: rmtree then recreate destination"

key-files:
  created:
    - "tests/test_opencode_installer.py"
    - "ai_codebase_mentor/converters/opencode.py"
  modified:
    - "ai_codebase_mentor/cli.py"

key-decisions:
  - "YAML frontmatter parsed line-by-line with block scalar state tracking (no YAML library dependency)"
  - "description: > block scalar lines are skipped entirely during frontmatter parsing to avoid false positives"
  - "tools: block prepended before other frontmatter fields in output"
  - "opencode.json written to parent of install dir (e.g., ~/.config/opencode/opencode.json)"
  - "CLI wired in same plan (08-01) rather than deferred to 08-02 per CONTEXT.md"

patterns-established:
  - "RuntimeInstaller pattern: implement install/uninstall/status/_resolve_dest"
  - "Frontmatter conversion: detect block scalars to avoid processing their content as YAML"

requirements-completed:
  - OPENCODE-01
  - OPENCODE-02
  - OPENCODE-03
  - OPENCODE-04
  - OPENCODE-05
  - OPENCODE-06
  - OPENCODE-07
  - OPENCODE-08
  - OPENCODE-09
  - OPENCODE-10
  - OPENCODE-13

# Metrics
duration: 3min
completed: 2026-03-22
---

# Phase 8 Plan 1: OpenCode Converter Summary

**OpenCodeInstaller converts Claude Code plugin format to OpenCode-native files at install time: allowed_tools->tools object, name removed, colors hex-encoded, commands/ renamed to command/, paths rewritten, skills verbatim — all 13 TDD tests pass with zero regressions**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-22T03:21:31Z
- **Completed:** 2026-03-22T03:24:17Z
- **Tasks:** 3 (RED + GREEN + verify)
- **Files modified:** 3

## Accomplishments

- 13-case TDD test suite written and confirmed failing (RED phase)
- OpenCodeInstaller fully implemented — all 13 tests pass (GREEN phase)
- Zero regressions against existing 9 Claude installer tests
- CLI `_get_converters()` wired to include `opencode: OpenCodeInstaller`

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Write 13 failing tests** - `a6bbfad` (test)
2. **Task 2 (GREEN): Implement OpenCodeInstaller** - `77fcf15` (feat)
3. **Task 3 (CLI wiring)** - `4f8fcd1` (feat)

_Note: TDD tasks have separate RED and GREEN commits._

## Files Created/Modified

- `tests/test_opencode_installer.py` - 13 TDD test cases mirroring test_claude_installer.py structure
- `ai_codebase_mentor/converters/opencode.py` - OpenCodeInstaller class: install/uninstall/status, frontmatter conversion, tool mapping, path rewriting, opencode.json permissions
- `ai_codebase_mentor/cli.py` - Added opencode to `_get_converters()` registry

## Decisions Made

- YAML frontmatter parsed with custom line-by-line state machine rather than a YAML library — handles block scalars (`description: >`) by tracking indent state to avoid processing block scalar content as YAML keys
- `tools:` block prepended before other fields in output frontmatter for readability
- CLI wiring done in plan 01 (not deferred to 08-02) since it's a 2-line change with no new tests needed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed frontmatter parser incorrectly processing block scalar content**
- **Found during:** Task 2 (GREEN implementation) — tests 9 and 10 failed
- **Issue:** The `description: >` block scalar in agent files caused the parser to treat description body lines as YAML fields. Lines matching `- "Read"` pattern inside the description were misidentified as tool list items and stripped; the `allowed_tools:` block was never reached.
- **Fix:** Added block scalar state tracking — when a top-level YAML key has value `>` or `|`, subsequent indented lines are skipped until indentation returns to 0. The parser now correctly skips description content and processes `allowed_tools:` as intended.
- **Files modified:** `ai_codebase_mentor/converters/opencode.py`
- **Verification:** Tests 9 and 10 pass after fix; all 13 pass
- **Committed in:** `77fcf15` (part of GREEN phase commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in frontmatter parser)
**Impact on plan:** Fix was essential for correct tool name conversion. No scope creep.

## Issues Encountered

The initial frontmatter parser implementation used a simple `in_allowed_tools` state variable but did not account for multi-line block scalars (`description: >`). The `codebase-wizard-agent.md` file has a `description: >` block that spans multiple lines including comment lines and list items — these looked identical to `allowed_tools:` list items to the naive parser. Fixed by adding block scalar state tracking.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- OpenCodeInstaller is complete and wired into CLI
- `--for opencode` and `--for all` flags work for install/uninstall/status
- Plan 08-02 (if it exists) can build on this foundation
- Phase 09 (PyPI publish) can proceed — opencode.py is part of the package

---
*Phase: 08-opencode-converter*
*Completed: 2026-03-22*
