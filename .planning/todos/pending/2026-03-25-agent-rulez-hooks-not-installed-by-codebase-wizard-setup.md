---
created: 2026-03-25T22:35:07.776Z
title: Agent Rulez hooks not installed by codebase-wizard-setup
area: general
files:
  - plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/setup.sh
  - plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/agent-rulez-sample.yaml
  - plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/capture-session.sh
---

## Problem

After running `/codebase-wizard-setup` and `/codebase-wizard-export` on the `~/linkedin` project,
the export skill logged: **"No session JSON was captured (hooks aren't installed)"**.

This means Agent Rulez is not being installed / activated by `setup.sh`, so `capture-session.sh`
never runs on PostToolUse events and `.code-wizard/sessions/` stays empty.

Observed session log excerpt:
```
⏺ No session JSON was captured (hooks aren't installed), so I'll synthesize the export
  directly from our conversation.
```

The export fell back to synthesizing from conversation history, which works but loses structured
session data (tool use events, file reads, exact timestamps).

**What Phase 10 fixed:**
- Rewrote `agent-rulez-sample.yaml` to use correct `rules:` schema (not `hooks:`)
- Fixed `setup.sh` to use `rulez install` instead of nonexistent `rulez hook add --config`
- Created `capture-session.sh` that reads PostToolUse JSON from stdin

**What is still broken:**
- The skill/plugin installed in `.opencode/codebase-wizard/` or `~/.claude/plugins/` may have
  the OLD version of `setup.sh` (pre Phase 10 fix)
- OR `rulez install` is not being triggered during the wizard setup step
- OR the Agent Rulez schema still doesn't match what the installed version expects
- No way to confirm hooks are active without checking `~/.config/rulez/` or the project's
  `.claude/hooks.yaml` after a setup run

**Positive finding from this same session:**
- `/codebase-wizard-export` DID write to `.code-wizard/docs/2026-03-25-job-search-walkthrough/SESSION-TRANSCRIPT.md`
  (correct location!) — this is an improvement over the evinova-agent-3 run where it wrote
  to `.planning/codebase-wizard-export.md` (wrong location). The export path issue may be fixed
  in the latest install, but session capture is still broken.

## Solution

1. **Verify installed version**: Check what version of `setup.sh` is installed in:
   - `~/.claude/plugins/cache/codebase-mentor/codebase-wizard/*/` (Claude global)
   - `.opencode/codebase-wizard/skill/configuring-codebase-wizard/scripts/setup.sh` (OpenCode project)
   - `~/.opencode/codebase-wizard/` (OpenCode global, if applicable)

2. **Re-install to pick up Phase 10 fixes**: Run `ai-codebase-mentor install --for all` to
   push the updated `setup.sh` and `capture-session.sh` to installed locations.

3. **Re-run setup in a test project**: Run `/codebase-wizard-setup` in a test project after
   reinstall, then check:
   - Did `rulez install` run? (`rulez status` or check for `.rulez/` or hooks config)
   - Did hooks get written? (check `~/.config/rulez/hooks.yaml` or project `.claude/hooks.yaml`)
   - Does `.code-wizard/sessions/` get populated after tool use?

4. **Add E2E test for setup**: The new `tests/test_e2e_installer.py` (Phase 12) tests CLI install
   but not the wizard setup flow. Consider adding a test that runs the setup skill and verifies
   Agent Rulez config is written.
