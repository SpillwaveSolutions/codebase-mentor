---
phase: 08-opencode-converter
verified: 2026-03-21T00:00:00Z
status: human_needed
score: 13/13 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 12/13
  gaps_closed:
    - "subagent_type: general-purpose converted to general in agent frontmatter (OPENCODE-05)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Install for opencode globally and open a wizard session in OpenCode"
    expected: "Agent loads with correct tool permissions, no approval prompts for scoped write/edit tools"
    why_human: "Permission pre-authorization in opencode.json can only be confirmed interactively in the OpenCode runtime"
---

# Phase 8: OpenCode Converter Verification Report

**Phase Goal:** Implement `ai_codebase_mentor/converters/opencode.py` — the install-time converter that reads the bundled Claude plugin source and generates OpenCode-native files at `~/.config/opencode/codebase-wizard/` (global) or `./.opencode/codebase-wizard/` (project). Wire the converter into the CLI alongside the existing Claude installer.

**Verified:** 2026-03-21

**Status:** human_needed

**Re-verification:** Yes — after OPENCODE-05 gap closure

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Global install writes converted files to `~/.config/opencode/codebase-wizard/` | VERIFIED | `_resolve_dest("global")` returns `Path.home() / ".config" / "opencode" / "codebase-wizard"`; test_global_install_creates_agent_files passes |
| 2 | Project install writes converted files to `./.opencode/codebase-wizard/` | VERIFIED | `_resolve_dest("project")` returns `Path.cwd() / ".opencode" / "codebase-wizard"`; test_project_install_creates_agent_files passes |
| 3 | `tools:` object with lowercase keys replaces `allowed_tools:` array | VERIFIED | `_convert_agent_frontmatter()` parses allowed_tools block, builds `tools:` with `{name}: true` entries; test_agent_tool_names_lowercased confirms `read: true` present |
| 4 | Five special tool mappings applied (AskUserQuestion -> question, etc.) | VERIFIED | `SPECIAL_MAPPINGS` dict present with all 5 entries; `_convert_tool_name()` checks them; test_special_tool_mapping_applied injects AskUserQuestion and confirms `question: true` |
| 5 | `name:` field removed from agent frontmatter | VERIFIED | Parser skips lines matching `^name:`; test_name_field_stripped confirms absence in frontmatter section |
| 6 | Named colors converted to hex (e.g., `cyan` -> `#00FFFF`) | VERIFIED | `COLOR_MAP` with 13 entries implemented; `_convert_agent_frontmatter()` applies color rewrite; logic correct |
| 7 | `subagent_type: "general-purpose"` converted to `"general"` | VERIFIED | Lines 155-157 of opencode.py: `re.sub(r'"?general-purpose"?', '"general"', line)` applied when `^subagent_type:` matches; test_subagent_type_normalized injects field and asserts output contains `subagent_type: "general"` and not `general-purpose`; passes |
| 8 | Command directory uses `command/` (singular) not `commands/` | VERIFIED | `install()` uses `destination / "command"` for output dir; test_command_directory_singular asserts `command/` exists, `commands/` absent, and `command/codebase-wizard.md` present |
| 9 | Content paths rewritten from `~/.claude` to `~/.config/opencode` | VERIFIED | `PATH_REWRITES` list applied by `_rewrite_paths()`; longer match listed first to avoid partial replacement |
| 10 | Skills copied verbatim with no transformation | VERIFIED | `shutil.copytree(skills_src, destination / "skills")` — no conversion applied |
| 11 | `opencode.json` written with permission pre-authorization | VERIFIED | `_write_opencode_permissions()` writes `permission.read` and `permission.external_directory` entries; merges with existing JSON |
| 12 | Uninstall removes directory; no-op if missing | VERIFIED | `uninstall()` checks `destination.exists()` before `shutil.rmtree()`; tests 4, 5, 6 all pass |
| 13 | All tests pass | VERIFIED | `python -m pytest tests/ -q` shows 23 passed, 0 failed (14 opencode + 9 claude) |

**Score:** 13/13 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ai_codebase_mentor/converters/opencode.py` | OpenCodeInstaller class implementing RuntimeInstaller ABC | VERIFIED | 381 lines; class OpenCodeInstaller(RuntimeInstaller) present; all methods implemented including subagent_type normalization at lines 155-157 |
| `tests/test_opencode_installer.py` | TDD test cases for OpenCode converter | VERIFIED | 216 lines; 14 test functions (13 original + test_subagent_type_normalized); all pass |
| `ai_codebase_mentor/cli.py` | CLI with opencode in _get_converters() and status output | VERIFIED | `_get_converters()` returns `{"claude": ClaudeInstaller, "opencode": OpenCodeInstaller}`; help text reads "claude, opencode, all" on both install and uninstall |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `opencode.py` | `base.py` | `class OpenCodeInstaller(RuntimeInstaller)` | WIRED | Pattern `class OpenCodeInstaller(RuntimeInstaller):` found at line 205 |
| `tests/test_opencode_installer.py` | `opencode.py` | `from ai_codebase_mentor.converters.opencode import OpenCodeInstaller` | WIRED | Import at line 8; all 14 tests instantiate and exercise the class |
| `cli.py` | `opencode.py` | `from ai_codebase_mentor.converters.opencode import OpenCodeInstaller` | WIRED | Import inside `_get_converters()`; `"opencode": OpenCodeInstaller` present |
| `cli.py` | `_get_converters()` | `"opencode": OpenCodeInstaller` dict entry | WIRED | Confirmed via import check — passes |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| OPENCODE-01 | 08-01 | Global install path `~/.config/opencode/codebase-wizard/` | SATISFIED | `_resolve_dest("global")` correct; test 1 passes |
| OPENCODE-02 | 08-01 | Project install path `./.opencode/codebase-wizard/` | SATISFIED | `_resolve_dest("project")` correct; test 2 passes |
| OPENCODE-03 | 08-01 | Agent frontmatter conversion: `allowed_tools:` array -> `tools:` object | SATISFIED | Full line-by-line parser with block scalar state tracking; tests 9, 10, 11 pass |
| OPENCODE-04 | 08-01 | Five special tool name mappings | SATISFIED | `SPECIAL_MAPPINGS` dict with all 5 entries; `_convert_tool_name()` applied; test 10 passes |
| OPENCODE-05 | 08-01 | Agent metadata normalization: name removal + color hex + subagent_type rewrite | SATISFIED | name removal tested; color->hex implemented; subagent_type normalization added at lines 155-157; test_subagent_type_normalized passes |
| OPENCODE-06 | 08-01 | Permission auto-configuration via `opencode.json` | SATISFIED | `_write_opencode_permissions()` writes correct structure; merge logic present |
| OPENCODE-07 | 08-01 | Command directory renamed `commands/` -> `command/` | SATISFIED | `install()` writes to `command/`; test 12 passes |
| OPENCODE-08 | 08-01 | Content path rewriting `~/.claude` -> `~/.config/opencode` | SATISFIED | `PATH_REWRITES` applied by `_rewrite_paths()` on all output files |
| OPENCODE-09 | 08-01 | Skills copied verbatim | SATISFIED | `shutil.copytree(skills_src, destination / "skills")` |
| OPENCODE-10 | 08-01 | Clean uninstall; no-op when not installed | SATISFIED | tests 4, 5, 6 all pass |
| OPENCODE-11 | 08-02 | Status reporting includes OpenCode | SATISFIED | `status` command iterates `_get_converters()`, outputs `opencode: not installed` line |
| OPENCODE-12 | 08-02 | `--for all` includes OpenCode | SATISFIED | `_get_converters()` dict includes `opencode`; `--for all` iterates all keys |
| OPENCODE-13 | 08-01 | TDD test suite | SATISFIED | 14 test functions in test_opencode_installer.py; all 23 suite-wide tests pass |

**Coverage:** 13/13 requirements satisfied.

---

### Anti-Patterns Found

No anti-patterns detected.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | No TODOs, stubs, placeholder returns, or empty implementations found |

---

### Human Verification Required

#### 1. OpenCode Session Approval Prompts

**Test:** Install globally with `ai-codebase-mentor install --for opencode`, then open OpenCode and start a codebase wizard session. Attempt a Write operation to `.code-wizard/`.

**Expected:** No per-file approval prompt appears — the `opencode.json` permission pre-authorization silences prompts for paths under `~/.config/opencode/codebase-wizard/*`.

**Why human:** Permission dialog suppression is runtime behavior that can only be verified interactively in the OpenCode application.

---

### Re-verification Summary

The single gap from the initial verification (OPENCODE-05 — `subagent_type` normalization) has been closed:

- `_convert_agent_frontmatter()` in `opencode.py` now detects `^subagent_type:` lines at lines 155-157 and rewrites `"general-purpose"` to `"general"` via `re.sub`.
- A new test `test_subagent_type_normalized` (lines 184-209 of `test_opencode_installer.py`) injects `subagent_type: "general-purpose"` into a source agent, runs install, and asserts the output contains `subagent_type: "general"` and does not contain `general-purpose`.
- No regressions: all 23 tests pass (`python -m pytest tests/ -q`), up from 22 (14 opencode tests, 9 claude tests).

All 13 requirements are now fully satisfied. The only remaining item is the human-only runtime test for permission pre-authorization in the OpenCode application.

---

## Test Results

```
python -m pytest tests/ -q
23 passed in 0.35s
```

---

_Verified: 2026-03-21_
_Verifier: Claude (gsd-verifier)_
