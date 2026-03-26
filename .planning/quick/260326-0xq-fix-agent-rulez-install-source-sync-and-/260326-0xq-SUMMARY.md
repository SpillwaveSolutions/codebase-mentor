---
quick_task: 260326-0xq
title: Fix 3 high-severity Agent Rulez integration issues
completed: 2026-03-26
commits:
  - 74c8e9c
  - b626f1a
  - 7549eaa
tags: [agent-rulez, setup.sh, skill-md, integration-tests]
---

# Quick Task 260326-0xq: Fix 3 High-Severity Agent Rulez Integration Issues

## Summary

Fixed three bugs that would prevent the Agent Rulez pipeline from working correctly
after a `ai-codebase-mentor install`: the install-source setup.sh was missing the
runtime parameter and hooks.yaml copy step, the SKILL.md Step 6 had conditional logic
that caused wizard turns to be skipped when Agent Rulez was present, and the integration
test had a hardcoded install path that would never match the actual Claude cache layout.

---

## Fix 1 — Sync setup.sh and SKILL.md to ai_codebase_mentor/plugin/ install source

**Commit:** `74c8e9c`

**Problem:** The installer (`ai_codebase_mentor/converters/base.py`) installs from
`ai_codebase_mentor/plugin/`, but previous fixes had only been applied to the dev tree
(`plugins/codebase-wizard/`). The actual install source still had the old, broken behavior.

**Files changed:**
- `ai_codebase_mentor/plugin/skills/configuring-codebase-wizard/scripts/setup.sh`
- `ai_codebase_mentor/plugin/skills/explaining-codebase/SKILL.md`

**setup.sh changes:**
- `deploy_hooks()` now accepts `$1 = runtime` parameter (default: `claude`)
- Added `mkdir -p .claude && cp "$DEPLOYED_YAML" .claude/hooks.yaml` before rulez install
- Added `case "$runtime"` dispatch: `rulez opencode install` for opencode, `rulez install` for all others
- `install_opencode()` now calls `deploy_hooks opencode` instead of `deploy_hooks`

**SKILL.md Step 6 changes:**
- Removed the conditional "If Agent Rulez is installed / NOT installed" logic
- Step 6 now unconditionally writes structured wizard turns via the Write tool
- Clarified that Agent Rulez captures raw tool events (different schema), not mentoring turns
- The wizard is now documented as the sole source of structured session data

---

## Fix 2 — Fix integration test setup_sh path to use actual Claude cache install location

**Commit:** `b626f1a`

**Problem:** The `integration_env` fixture built the path to `setup.sh` as:
```
home / ".claude" / "plugins" / "codebase-wizard" / "skills" / ...
```
But `ClaudeInstaller._resolve_dest()` installs to:
```
~/.claude/plugins/cache/codebase-mentor/codebase-wizard/{version}/
```
This meant `plugin_setup_sh` would never exist and the test would silently use a
broken path.

**File changed:**
- `tests/integration/test_agent_rulez_e2e.py` (lines 140-150, `integration_env` fixture)

**Fix:** Replaced the hardcoded path with a dynamic lookup:
1. Checks `~/.claude/plugins/cache/codebase-mentor/codebase-wizard/` exists, or `pytest.skip()`
2. Lists versioned subdirectories, `pytest.skip()` if none found
3. Takes `version_dirs[-1]` (latest version)
4. Checks that `setup.sh` exists at the expected path inside that version dir, or `pytest.skip()`

---

## Fix 3 — Add Agent Rulez hook event assertions to integration test

**Commit:** `7549eaa`

**Problem:** `assert_phase3_session_captured()` only checked for wizard turns (turns with
a `question` field). The test could pass even if Agent Rulez `capture-session.sh` never
fired at all, because wizard turns and rulez hook events are written to separate session
files with different schemas.

**File changed:**
- `tests/integration/test_agent_rulez_e2e.py`

**Fix:** Added `assert_phase3_rulez_fired(project)` helper function that:
1. Loads all session JSON files from `.code-wizard/sessions/`
2. Collects all turns across all session files
3. Finds turns with `hook_event_name` or `tool_name` fields (Agent Rulez schema)
4. Asserts at least one hook event exists (with detailed failure message listing possible causes)
5. Asserts at least one hook event has `tool_name` (proves hook fired on a real tool call)

Called in the main test immediately after `assert_phase3_session_captured()`:
```python
sessions = assert_phase3_session_captured(project)
assert_phase3_rulez_fired(project)  # NEW: verify rulez hook events, not just wizard turns
```

---

## Self-Check

- [x] `ai_codebase_mentor/plugin/skills/configuring-codebase-wizard/scripts/setup.sh` — modified
- [x] `ai_codebase_mentor/plugin/skills/explaining-codebase/SKILL.md` — modified
- [x] `tests/integration/test_agent_rulez_e2e.py` — modified
- [x] Commit `74c8e9c` exists
- [x] Commit `b626f1a` exists
- [x] Commit `7549eaa` exists
