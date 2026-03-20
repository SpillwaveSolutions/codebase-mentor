---
context: fork
agent: codebase-wizard-agent
---

# /codebase-wizard-export

Synthesizes one or more raw session JSON files into structured documentation.

## Args

`--latest` (default) | `--session <filename>` | `--all`

- `--latest` — synthesize the most recent session file in `{resolved_storage}/sessions/`
- `--session <filename>` — synthesize a specific session file by name
- `--all` — synthesize every session file independently; each gets its own output directory

## Step 1 — Read config.json

Find config.json by checking both storage locations in order:
1. `.code-wizard/config.json`
2. `.claude/code-wizard/config.json`

Read `resolved_storage` from the config. If neither file exists, tell the user:
> "No wizard storage found. Run /codebase-wizard-setup first."

## Step 2 — Select Session File(s)

- `--latest`: list files in `{resolved_storage}/sessions/`, sort by name (ISO date prefix),
  take the most recent.
- `--session <filename>`: read `{resolved_storage}/sessions/<filename>` directly.
- `--all`: collect all `.json` files in `{resolved_storage}/sessions/`.

If no session files exist:
> "No sessions found in {resolved_storage}/sessions/. Run /codebase-wizard to
>  start a session first."

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

## Step 4 — Synthesize Output Documents

Output directory: `{resolved_storage}/docs/{session_id}/`

Create the directory if it does not exist.

### SESSION-TRANSCRIPT.md (always generated — every mode)

Format each turn as:

```markdown
## Q: {question}

*{ts}*

// {anchor}
`​`​`
{code_shown}
`​`​`

{explanation}

→ calls:     {connections.calls joined with newlines}
→ called by: {connections.called_by joined with newlines}

**Next options explored:**
- {next_options[0]}
- {next_options[1]}
- {next_options[2]}

---
```

Omit connections block if both `calls` and `called_by` are empty arrays.
Omit next options block if `next_options` is empty.

### CODEBASE.md (describe mode sessions: `mode == "describe"`)

```markdown
# Codebase: {repo}

## Overview
[Synthesize from early turns: what it does, who uses it, tech stack]

## Entry Points
[Extract from turns covering entry point questions]

## Auth
[Extract from turns covering auth questions. Include code block with anchor.]

## Data Layer
[Extract from turns covering data/ORM questions]

## Key Concepts
[Extract domain term definitions from Q5-style turns]

## Traced Call Chains
[Extract traced call sequences with anchors]

## Constraints
[Extract from turns covering off-limits areas, fragile code, dead code]

## Open Questions
[Collect any next_options not followed up on, or questions marked unresolved]
```

### TOUR.md (explore mode sessions: `mode == "explore"`)

Format as a re-readable learning guide:

```markdown
# Tour: {repo}

*Generated from explore session on {created}*

## What the App Does
[Extract from Step 1 turn]

## Entry Point
[Extract from Step 2 turn with anchor]

## Auth Flow
[Extract from Step 3 turn with anchor]

## Data Flow
[Extract from Step 4 turn with anchor]

## Where to Start
[Extract from Step 5 turn with anchor]

## Q&A Detours
[Any off-topic turns answered during the tour]
```

### FILE-NOTES.md (file mode sessions: `mode == "file"`)

```markdown
# File Notes: {artifact}

*Generated from file session on {created}*

[For each turn, in order:]
## {question}

// {anchor}
`​`​`
{code_shown}
`​`​`

{explanation}

[Follow-up Q&A captured under this section if any]

---
```

## Step 5 — Report Completion

After writing all files:
> "Export complete. Files written to {resolved_storage}/docs/{session_id}/:"
> - SESSION-TRANSCRIPT.md
> - CODEBASE.md (if describe mode)
> - TOUR.md (if explore mode)
> - FILE-NOTES.md (if file mode)
