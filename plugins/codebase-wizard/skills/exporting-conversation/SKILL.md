---
name: Exporting Conversation
description: >
  Synthesizes raw wizard session JSON into structured documentation. Use when
  the user runs /codebase-wizard-export, says "export session", "generate docs",
  "create CODEBASE.md", or "turn the session into docs".
version: 1.0.0
---

# Exporting Conversation

Synthesizes one or more raw session JSON files into structured documentation.

---

## Args

`--latest` (default) | `--session <filename>` | `--all`

- `--latest` — synthesize the most recent session file in `{resolved_storage}/sessions/`
- `--session <filename>` — synthesize a specific session file by name
- `--all` — synthesize every session file independently; each gets its own output directory

---

## Step 1 — Read config.json

Find config.json by checking both storage locations in order:
1. `.code-wizard/config.json`
2. `.claude/code-wizard/config.json`

Read `resolved_storage` from the config. If neither file exists, tell the user:
> "No wizard storage found. Run /codebase-wizard-setup first."

---

## Step 2 — Select Session File(s)

- `--latest`: list files in `{resolved_storage}/sessions/`, sort by name (ISO date prefix),
  take the most recent.
- `--session <filename>`: read `{resolved_storage}/sessions/<filename>` directly.
- `--all`: collect all `.json` files in `{resolved_storage}/sessions/`.

If no session files exist:
> "No sessions found in {resolved_storage}/sessions/. Run /codebase-wizard to
>  start a session first."

---

## Step 3 — Read and Validate Session JSON

For each selected session file, read and parse the JSON. Expected schema:

```json
{
  "version": 1,
  "session_id": "YYYY-MM-DD-{repo}",
  "repo": "...",
  "artifact": "...",
  "mode": "describe | explore | file",
  "created": "...",
  "turns": [
    {
      "ts": "...",
      "question": "...",
      "anchor": "...",
      "code_shown": "...",
      "explanation": "...",
      "connections": { "calls": [], "called_by": [] },
      "next_options": []
    }
  ]
}
```

If `version` field is missing or higher than 1, warn:
> "Session file uses an unrecognized version. Attempting synthesis anyway — some
>  fields may be missing."

---

## Step 4 — Synthesize Output Documents

Output directory: `{resolved_storage}/docs/{session_id}/`

Create the directory if it does not exist.

### SESSION-TRANSCRIPT.md (always — every mode)

Format each turn as:

```markdown
## Q: {question}

*{ts}*

// {anchor}
```
{code_shown}
```

{explanation}

→ calls:     {connections.calls joined with newlines}
→ called by: {connections.called_by joined with newlines}

**Next options explored:**
- {next_options[0]}
- {next_options[1]}
- {next_options[2]}

---
```

Omit connections block if both `calls` and `called_by` are empty.
Omit next options block if `next_options` is empty.

### CODEBASE.md (describe mode: `mode == "describe"`)

```markdown
# Codebase: {repo}

## Overview
## Entry Points
## Auth
## Data Layer
## Key Concepts
## Traced Call Chains
## Constraints
## Open Questions
```

Each section extracted from the relevant turns.

### TOUR.md (explore mode: `mode == "explore"`)

```markdown
# Tour: {repo}

## What the App Does
## Entry Point
## Auth Flow
## Data Flow
## Where to Start
## Q&A Detours
```

### FILE-NOTES.md (file mode: `mode == "file"`)

One section per turn, with anchor and code block preserved.

---

## Step 5 — Report Completion

> "Export complete. Files written to {resolved_storage}/docs/{session_id}/:"
> - SESSION-TRANSCRIPT.md
> - CODEBASE.md (if describe mode)
> - TOUR.md (if explore mode)
> - FILE-NOTES.md (if file mode)
