# Describe Mode — Question Bank

Load this file when `--describe` mode activates. Contains the ordered
question set, follow-up logic, and output schema for Describe mode.

## When to Load

Load after repo scan completes (Phase 1 scan-patterns.md logic). Do
not load during Explore or File mode.

## Pre-Question: Scan First

Before asking any questions, run the Phase 1 scan and produce the
tour map (Entry, Auth, Data, Docs). Show the user what you found:

> "I can see [X] in [file], [Y] in [folder], and [Z] in [file].
>  Let me ask a few things I can't figure out from the code alone."

## Question Order

Ask in this order. Skip any question whose answer is already clear
from the scan or a previous answer.

### Category: Ownership

**Q1 — Folder ownership** (ask if ambiguous folders exist):
> "I see `[folder]/` — is this [interpretation A] or [interpretation B]?"

Ask about: `jobs/`, `workers/`, `tasks/`, `background/`, `queue/`,
`events/`, `handlers/`, `utils/` (if large), `legacy/`, `archive/`.
Do NOT ask about folders whose role is obvious from filenames/contents.

**Q2 — Dead code** (ask only if these exist: `legacy/`, `archive/`,
`deprecated/`, `_old`, `_backup`, `.disabled`):
> "Is `[folder/file]` still active or is it safe to ignore?"

### Category: Intent

**Q3 — Dual/ambiguous patterns** (ask if 2+ auth strategies, 2+ DB
connections, or 2+ semantically similar patterns exist):
> "I see both `[thing A]` and `[thing B]`. Are these both active,
>  or is one deprecated/in-migration?"

**Q4 — The core flow** (always ask):
> "What's the one thing this service/app absolutely must do correctly?
>  If I had to trace one path through the code, which would it be?"

### Category: Domain Terms

**Q5 — Unexplained domain nouns** (ask for each noun that appears
frequently but isn't a standard programming term):
> "I keep seeing `[term]` — what does that mean in this codebase?"

Identify domain nouns by: frequency in variable/function names,
presence in route paths, presence in DB schema/model names.
Limit to 3 questions max. Ask the most frequent ones first.

### Category: Constraints

**Q6 — Off-limits areas** (ask if `legacy/`, `vendor/`, `generated/`
or similar exist):
> "Is `[folder]` off-limits for changes, or fair game?"

**Q7 — Untraced error handling** (ask if no global error handler found):
> "I couldn't find where errors from [X] end up. Where should I look?"

## Follow-Up Logic

After each answer:
1. If answer resolves a related pending question → skip that question
2. If answer introduces a new unknown term → add it to Q5 queue
3. If answer references an unscanned file/folder → add to tour map,
   offer to explore it

## Output Schema

After all questions answered (or user says "done"), offer:
> "Want me to save this as CODEBASE.md? I'll structure it around
>  what we covered."

On confirmation, generate these files in `{resolved_storage}/docs/{session_id}/`:

**CODEBASE.md:**
```markdown
# Codebase: {repo}

## Overview
[2-3 sentences: what it does, who it's for, tech stack]

## Entry Points
[file → what it does, one line each]

## Auth
[How users authenticate. Main auth code block with anchor.]

## Data Layer
[ORM/DB. Main models. How data is stored/fetched.]

## Key Concepts
[Domain terms from Q5 answers. One paragraph each.]

## Traced Call Chains
[1-3 core flows traced end-to-end with code block anchors]

## Constraints
[Answers from Q6, Q7. What's off-limits, what's fragile.]

## Open Questions
[Anything unresolved during the session]
```

**SESSION-TRANSCRIPT.md:**
Full Q&A in order with all code blocks and anchors shown.
Always generated alongside CODEBASE.md.
