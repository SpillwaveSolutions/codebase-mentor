---
created: 2026-03-29T01:27:44.014Z
title: OpenCode skill activation gap - wizard not invoked
area: testing
files:
  - tests/integration/test_agent_rulez_e2e.py:1010
  - ai_codebase_mentor/converters/opencode.py
  - artifacts/opencode-rulez-failure-20260328T180509.tar.gz
---

## Problem

When running `opencode run -m opencode/claude-sonnet-4-6 --dir <project> "describe this codebase"`, OpenCode answers the prompt directly instead of invoking the codebase-wizard skill. The full pipeline works up to skill activation:

1. Setup pipeline: Working (hooks.yaml, opencode settings, capture-session.sh deploy correctly)
2. OpenCode invocation: Working (model auth, LLM call succeeds)
3. Agent Rulez hooks: Working (cch fires, session events ARE captured to JSON)
4. Wizard skill activation: NOT working — session files contain raw hook events (`content`, `details`, `role`, `turn`) instead of structured wizard turns (`question`, `anchor`, `explanation`)

The e2e test `test_agent_rulez_opencode_capture_to_export` fails at Phase 3 with: "No turns have 'question' field. Session contains only raw hook events."

## Solution

Investigate how OpenCode discovers and activates installed skills/commands. Options:

- Wire up the codebase-wizard as an OpenCode command (may need `opencode.json` command config with a template that references the SKILL.md)
- Use the `--agent` flag to route to a codebase-wizard agent
- Modify the prompt to explicitly invoke a slash command if OpenCode supports them
- Check if OpenCode has a skill/plugin system analogous to Claude Code's

Full diagnostic bundle: `artifacts/opencode-rulez-failure-20260328T180509.tar.gz`
