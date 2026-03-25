---
created: 2026-03-25T19:15:24.392Z
title: Map context:fork to OpenCode subtask:true in converter
area: general
files:
  - ai_codebase_mentor/converters/opencode.py
  - plugins/codebase-wizard/command/codebase-wizard-export.md
  - plugins/codebase-wizard/command/codebase-wizard.md
---

## Problem

Claude Code commands use `context: fork` in their frontmatter to run the command
in an isolated context (prevents polluting the primary session). Example from
our `codebase-wizard-export.md`:

```yaml
---
description: "Synthesize captured session logs into CODEBASE.md, TOUR.md, or FILE-NOTES.md."
context: fork
agent: codebase-wizard-agent
---
```

The OpenCode converter (`opencode.py`) currently strips `context: fork` during
conversion because it has no equivalent frontmatter field. The converted
`command/*.md` files silently drop this isolation behavior.

OpenCode's equivalent is `opencode.json` with a `command` entry:

```json
{
  "command": {
    "codebase-wizard-export": {
      "subtask": true
    }
  }
}
```

From OpenCode docs (https://opencode.ai/docs/commands/):
> **Subtask** — Use the `subtask` boolean to force the command to trigger a subagent
> invocation. This is useful if you want the command to not pollute your primary
> context and will force the agent to act as a subagent, even if mode is set to
> primary on the agent configuration.

Currently: `context: fork` in Claude command → silently dropped in OpenCode output.
Expected: `context: fork` in Claude command → `subtask: true` in `opencode.json`.

## Solution

**Step 1: Detect `context: fork` during command conversion in `opencode.py`**

In `_convert_command()` (or equivalent), read the `context:` frontmatter field.
If value is `fork`, record the command name as needing `subtask: true`.

**Step 2: Write (or merge) `opencode.json` in the install directory**

After converting all commands, write a `opencode.json` in the install root with
entries for every command that had `context: fork`:

```json
{
  "command": {
    "codebase-wizard-export": {
      "subtask": true
    },
    "codebase-wizard-setup": {
      "subtask": true
    }
  }
}
```

If `opencode.json` already exists (prior install or pre-existing project config),
**merge** the `command` keys — do not overwrite the entire file. This is consistent
with how we handle `opencode.json` permissions (OPENCODE-06).

**Step 3: Add tests to `tests/test_opencode_installer.py`**

- Assert that after install, `opencode.json` contains `command.codebase-wizard-export.subtask = true`
- Assert idempotent: second install produces same `opencode.json` (no duplicate keys)
- Assert merge: if `opencode.json` pre-existed with unrelated keys, they are preserved

## Notes

- Still needs research to confirm `subtask: true` is the full API (e.g., does it
  accept other keys like `model` or `timeout`?). The OpenCode docs page
  https://opencode.ai/docs/commands/ is the canonical source.
- The `context:` field in Claude commands can also have other values (e.g., no
  value = runs in primary context). Only `fork` → `subtask: true` mapping is needed.
- This is a correctness fix — without it, `codebase-wizard-export` runs in the
  primary OpenCode session context instead of forking, which contaminates the
  user's conversation history.
