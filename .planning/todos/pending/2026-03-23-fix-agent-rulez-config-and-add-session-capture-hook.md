---
created: 2026-03-23T21:58:27.953Z
title: Fix Agent Rulez config and add session capture hook
area: general
files:
  - plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/agent-rulez-sample.yaml
  - plugins/codebase-wizard/skills/configuring-codebase-wizard/SKILL.md
---

## Problem

Two issues found during live testing of /codebase-wizard-setup:

1. **Agent Rulez file looks malformed**: The `agent-rulez-sample.yaml` generated/deployed by the
   setup wizard appears broken — likely wrong YAML structure, wrong field names, or wrong hook
   event format. Needs inspection and comparison against actual Agent Rulez hook schema to confirm
   it will work.

2. **Missing session capture hook**: The wizard is supposed to capture each Q&A turn into a
   session JSON file (schema: version, session_id, repo, mode, turns[]) so that
   `/codebase-wizard-export` can later synthesize CODEBASE.md / TOUR.md / FILE-NOTES.md. But
   there is no PostToolUse or Stop hook that actually listens to conversation turns and writes
   them to `{resolved_storage}/sessions/`. Without this, session capture never happens and export
   has nothing to work with.

The setup wizard (configuring-codebase-wizard skill) calls `setup.sh` which deploys
`agent-rulez-sample.yaml` and registers it via `rulez hook add`. If the YAML is wrong, hooks
won't fire. Even if hooks fire, the hook action needs to write the turn data to the session file
in the correct JSON schema.

## Solution

1. Read `agent-rulez-sample.yaml` and validate against Agent Rulez hook schema:
   - Correct event names (PreToolUse, PostToolUse, Stop, etc.)
   - Correct action format for writing session JSON
   - Substitution of `{resolved_storage}` at deploy time

2. Design and implement the session capture hook:
   - Event: likely `Stop` (fires when Claude finishes a turn) or `PostToolUse`
   - Action: append turn data (question, anchor, code_shown, explanation, connections, next_options)
     to `{resolved_storage}/sessions/{session_id}.json`
   - The hook script or command needs to extract turn content from the conversation context

3. Test end-to-end: run `/codebase-wizard`, answer a few questions, check that session JSON
   is written, then run `/codebase-wizard-export` and confirm docs are generated.
