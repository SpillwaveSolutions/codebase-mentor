---
plan: 04-01
phase: 04-claude-code-plugin-manifest-and-marketplace-listing
status: complete
completed: 2026-03-20
---

# Summary: Phase 04-01 — Finalize plugin.json and Create marketplace.json

## What Was Done

Two files were written/updated in `plugins/codebase-wizard/.claude-plugin/`:

### Task 1: `plugin.json` — finalized install manifest

Added 8 fields to the existing 4-field stub:

| Field | Value |
|-------|-------|
| `author` | `{ "name": "Spillwave Solutions", "url": "https://github.com/SpillwaveSolutions" }` |
| `license` | `"MIT"` |
| `homepage` | `"https://github.com/SpillwaveSolutions/codebase-mentor"` |
| `repository` | `{ "type": "git", "url": "..." }` |
| `runtime` | `"claude-code"` |
| `commands` | 3 entries (codebase-wizard, -export, -setup) |
| `agents` | 2 entries (codebase-wizard-agent, codebase-wizard-setup-agent) |
| `skills` | 3 entries (explaining-codebase, configuring-codebase-wizard, exporting-conversation) |

`keywords` expanded from 4 → 7 items (added "explain", "tour", "ai-codebase-mentor").

### Task 2: `marketplace.json` — new marketplace listing record

Created with 15 required fields. Key conventions:

- **`entry: ".claude-plugin/plugin.json"`** — relative path from `plugins/codebase-wizard/` to the install manifest. Phase 5 installer reads this field to locate plugin.json.
- **`runtime: "claude-code"`** — consumed by Phase 6 Python package as the converter selector key (`claude.py` vs `opencode.py` etc.)
- **`install.method: "python-package"`** — signals preferred install path via `ai-codebase-mentor install --for claude`
- **`short_description`**: 89 chars (under 120 limit)
- **`commands`**: inline summaries (name + description) for marketplace UI cards, NOT the full command files

## Verification

All three checks passed:
- `plugin.json`: PASS — 12 required fields, 3 commands, 2 agents, 3 skills, runtime="claude-code"
- `marketplace.json`: PASS — 15 required fields, entry resolves to real plugin.json, 3 commands, short_description 89 chars
- Cross-file consistency: PASS — name, version, runtime consistent between both files

## Downstream Consumers

| Phase | What it reads | Field used |
|-------|--------------|------------|
| Phase 5 (claude.py installer) | `plugin.json` | Copies file verbatim to `~/.claude/plugins/codebase-wizard/` |
| Phase 6 (Python CLI) | `plugin.json` `runtime` field | Selects which converter class to invoke |
| Phase 6 (Python CLI) | `marketplace.json` `entry` field | Locates plugin.json from the bundle |
