---
created: 2026-03-23T22:00:03.578Z
title: Number next-options and add free-text fallback in answer loop
area: general
files:
  - plugins/codebase-wizard/skills/explaining-codebase/SKILL.md
---

## Problem

The "Next — want to:" block at the end of every answer shows 2-5 follow-up options but they are
bullet points with no labels. Users have to read and retype (or copy-paste) to pick one. Two UX
issues:

1. **No numbers** — options should be labeled 1, 2, 3 so the user can just reply "2" or "1" to
   navigate. Fast keyboard-driven flow, especially useful in terminal.

2. **No escape hatch** — if none of the predicted options match what the user wants, they have
   no obvious path. Adding a "or describe what you want" prompt makes it clear they can always
   type free text.

Current format in SKILL.md:
```
> **Next — want to:**
> - **Trace back**: where does this token get created?
> - **Forward**: what happens when `req.user` hits the controller?
> - **Jump**: show me the DB save on signup
```

Desired format:
```
> **Next — want to:**
> 1. **Trace back**: where does this token get created?
> 2. **Forward**: what happens when `req.user` hits the controller?
> 3. **Jump**: show me the DB save on signup
>
> *(or just tell me what you want)*
```

## Solution

Update `Step 5 — Predict Next` in the Answer Loop section of
`plugins/codebase-wizard/skills/explaining-codebase/SKILL.md`:

- Change bullet list (`- **Label**: ...`) to numbered list (`1. **Label**: ...`)
- Add a trailing soft prompt: `*(or just tell me what you want)*`
- Update the Phase 2 "Predict Next" section to match the same format
- Update SESSION-TRANSCRIPT.md output format in the exporting-conversation skill to
  preserve the numbered format in `next_options[]`

Also sync the change to `ai_codebase_mentor/plugin/` (bundled copy).
