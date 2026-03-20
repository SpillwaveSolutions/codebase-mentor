---
status: testing
phase: 03-permission-agents-commands
source: [03-01-SUMMARY.md]
started: 2026-03-20T00:00:00Z
updated: 2026-03-20T00:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: /codebase-wizard runs with zero approval prompts
expected: |
  Run `/codebase-wizard` (or `/codebase-wizard --describe`) in a Claude Code session.
  The wizard should start without any "May I use this tool?" approval prompts.
  The policy island agent pre-authorizes all needed tools, so you should be able to
  complete a full scan/Q&A session without clicking Approve once.
awaiting: user response

## Tests

### 1. /codebase-wizard runs with zero approval prompts
expected: Run `/codebase-wizard` in Claude Code. The wizard starts and completes a session with no tool approval prompts — the policy island agent pre-authorizes Read, Glob, Grep, Bash (node/grep/find/cat/ls/rulez), and WebSearch/WebFetch.
result: [pending]

### 2. Agent write boundary is enforced
expected: While the wizard is running, any attempt to write or edit a file outside `.code-wizard/**` or `.claude/code-wizard/**` should be blocked. The agent's allowed_tools list scopes Write and Edit to those two directories only — writing a source file like `plugin/SKILL.md` should be refused.
result: [pending]

### 3. ./setup.sh codex exits 77 with manual notice
expected: Run `./setup.sh codex` from the `plugin/setup/` directory. It should print a manual export notice (explaining that Codex doesn't support hooks and how to run export manually), then exit with code 77. It should NOT attempt to install hooks or modify any config files.
result: [pending]

### 4. ./setup.sh all completes cleanly
expected: Run `./setup.sh all` from `plugin/setup/`. It should complete the install for claude, opencode, and gemini. The codex branch exits 77 internally, but `install_all` catches it — the overall script should exit 0 (success), not fail because of the codex skip.
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0

## Gaps

[none yet]
