---
phase: 14-gemini-converter-implementation
plan: 01
subsystem: converters
tags: [gemini, cli, toml, yaml, tool-mapping, tdd]

requires:
  - phase: 08-opencode-converter
    provides: RuntimeInstaller ABC, _read_version(), converter registration pattern
provides:
  - GeminiInstaller class with install/uninstall/status
  - GEMINI_TOOL_MAP with 10 Claude-to-Gemini tool name mappings
  - Agent frontmatter converter (YAML array tools format)
  - Command-to-TOML converter
  - Content transform helpers (template var escape, sub tag strip, path rewrite)
  - 36-test TDD suite covering all GEMINI requirements
affects: [14-02-gemini-cli-registration, 15-gemini-hooks, 16-gemini-integration]

tech-stack:
  added: [tomllib (test-only, stdlib 3.11+)]
  patterns: [gemini-converter, toml-generation-via-json-dumps, yaml-array-tools-format]

key-files:
  created:
    - ai_codebase_mentor/converters/gemini.py
    - tests/test_gemini_installer.py
  modified: []

key-decisions:
  - "TOML generation uses json.dumps() for string escaping -- no tomli_w dependency needed"
  - "Content transforms applied to agent body only, not frontmatter"
  - "tools: output as YAML array (- tool_name) not object (tool: true) -- matches live Gemini format"
  - "color: stripped entirely, name: kept -- opposite of OpenCode behavior"
  - "PATH_REWRITES_GEMINI orders $HOME/.claude before ~/.claude for correct replacement"

patterns-established:
  - "Gemini converter pattern: line-by-line YAML parser with YAML array output for tools"
  - "TOML command conversion: description + prompt fields via json.dumps() escaping"
  - "Content transforms: _escape_template_vars, _strip_sub_tags, _rewrite_paths applied to body only"

requirements-completed: [GEMINI-01, GEMINI-02, GEMINI-03, GEMINI-04, GEMINI-05, GEMINI-06, GEMINI-07, GEMINI-08, GEMINI-09, GEMINI-10, GEMINI-11, GEMINI-12, GEMINI-15]

duration: 4min
completed: 2026-03-31
---

# Phase 14 Plan 01: Gemini Converter Implementation Summary

**TDD GeminiInstaller with 10 tool mappings, YAML array tools output, TOML command conversion, and content transforms (${VAR} escape, sub-tag strip, path rewriting)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-31T03:28:09Z
- **Completed:** 2026-03-31T03:31:50Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- 36-test TDD suite covering install/uninstall/status, agent conversion, 10 tool mappings, content transforms, and TOML command conversion
- GeminiInstaller converter class implementing RuntimeInstaller contract with GEMINI_CONFIG_DIR env var override
- Agent frontmatter conversion: tools as YAML array, color stripped, name kept, Task/Agent/mcp__ excluded
- Command-to-TOML conversion with valid TOML output (verified with tomllib)
- Content transforms applied to body only: ${VAR}->$VAR, <sub>->*(text)*, ~/.claude->~/.gemini

## Task Commits

Each task was committed atomically:

1. **Task 1: RED -- Write comprehensive test suite** - `aaa59d4` (test)
2. **Task 2: GREEN -- Implement GeminiInstaller** - `285f9df` (feat)

_TDD: RED phase committed all 36 tests failing, GREEN phase made all pass._

## Files Created/Modified
- `ai_codebase_mentor/converters/gemini.py` - GeminiInstaller converter class with all helpers
- `tests/test_gemini_installer.py` - 36-test TDD suite covering all GEMINI requirements

## Decisions Made
- Used `json.dumps()` for TOML string escaping instead of adding a `tomli_w` dependency -- JSON strings are valid TOML basic strings
- Applied content transforms to agent body only, not frontmatter -- prevents breaking YAML structure with ${VAR} escaping
- Ordered PATH_REWRITES_GEMINI with `$HOME/.claude` before `~/.claude` to avoid partial replacement issues
- Kept `name:` field in Gemini agents (unlike OpenCode which strips it) -- matches live Gemini agent format
- Stripped `color:` entirely (unlike OpenCode which converts to hex) -- Gemini validator rejects unknown fields

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness
- GeminiInstaller ready for registration in `_get_converters()` (Phase 14 Plan 02)
- All 36 tests pass, 107 total suite tests pass with 0 regressions
- GEMINI_CONFIG_DIR env var support ready for CLI integration

---
*Phase: 14-gemini-converter-implementation*
*Completed: 2026-03-31*
