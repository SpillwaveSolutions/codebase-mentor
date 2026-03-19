# Codebase Wizard — Plan 1: Core Wizard Skill

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the core wizard skill — SKILL.md, question banks, and the universal answer loop — so the explainer works for codebases, markdown files, and any artifact through a conversational Q&A interface.

**Architecture:** The existing `plugin/SKILL.md` is extended (not replaced) with two new modes (Describe, Explore) and a File mode. Question logic lives in lazily-loaded reference files. Every answer follows the code-block-first anchor pattern. The skill is self-contained and testable before capture or permissions are added.

**Tech Stack:** Markdown skill files, Claude Code skill conventions, existing references (scan-patterns.md, chat-feel.md, navigation-commands.md, tutorial-mode.md, persistence.md)

**Spec:** `docs/superpowers/specs/2026-03-19-codebase-wizard-design.md` (Sections 1–2)

**Scope note — deferred to later plans:**
- `plugin/agents/codebase-wizard-agent.md` → Plan 3 (Permission Agents)
- `plugin/commands/*.md` → Plan 3 (Commands)
- `plugin/setup/setup.sh` and `agent-rulez-sample.yaml` → Plan 2 (Capture)
- `plugin/references/codex-tools.md` → Plan 3 (Multi-Platform)
- Session JSON capture and `/codebase-wizard-export` → Plan 2 (Capture + Synthesis)

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Modify | `plugin/SKILL.md` | Mode routing, answer loop, research priority, lazy reference loading, File mode, updated frontmatter |
| Create | `plugin/references/describe-questions.md` | Ordered question bank + follow-up logic + CODEBASE.md output schema |
| Create | `plugin/references/explore-questions.md` | Learning-order tour structure + follow-up logic + TOUR.md output schema |
| Keep (no changes) | `plugin/references/chat-feel.md` | Tone/formatting — referenced by all modes |
| Keep (no changes) | `plugin/references/scan-patterns.md` | Repo scan heuristics — referenced by Describe + Explore modes |
| Keep (no changes) | `plugin/references/navigation-commands.md` | Navigation — referenced by Explore mode |
| Keep (no changes) | `plugin/references/persistence.md` | Session save/load |

---

## Task 1: Add the Answer Loop to SKILL.md

The answer loop is the behavioral contract every response must follow. Define it first — all modes inherit it.

**Files:**
- Modify: `plugin/SKILL.md`

- [ ] **Step 1: Read existing SKILL.md and note its structure**

```bash
cat plugin/SKILL.md
```

Note: the existing file has frontmatter + Core Principles + 5 phases. New content goes between Core Principles and Phase 1.

- [ ] **Step 2: Define expected answer loop behavior (verification baseline)**

Before writing, document the invariants you'll check in Task 6:

```
INVARIANT-1: Every response shows a code block with anchor BEFORE explanation
INVARIANT-2: Anchor format = "// file → class/section → method → LOC"
INVARIANT-3: Every response ends with 2-3 specific next options
INVARIANT-4: Explanation paragraph is ≤5 sentences
INVARIANT-5: Code connections shown for code-mode responses
```

Write these to a scratch file for reference during Task 6:
```bash
cat > /tmp/wizard-invariants.txt << 'EOF'
INVARIANT-1: code block with anchor appears before explanation text
INVARIANT-2: anchor = "// file → class/section → method → LOC"
INVARIANT-3: 2-3 specific "Next — want to:" options at end
INVARIANT-4: explanation is ≤5 sentences
INVARIANT-5: "→ calls:" and "→ called by:" lines present for code responses
EOF
```

- [ ] **Step 3: Add the Answer Loop section to SKILL.md**

Insert this immediately after the `## Core Principles` block:

```markdown
## The Answer Loop (Every Response — No Exceptions)

Every single answer, regardless of mode, follows this exact pattern:

### Step 1 — Find the Artifact

Locate the relevant code, section, or passage using available tools
(see Research Priority below). Never explain something you haven't
found and shown.

### Step 2 — Show the Code Block with Anchor

Always show the artifact first, before any explanation. Format:

For code:
```
// src/auth/middleware.ts → AuthMiddleware → validate() → L14-31
<code block>
```

For markdown sections:
```
// docs/ROADMAP.md → Phase 3: Auth → "Requirements" section → L14-31
<quoted section>
```

The anchor format is: `// file → class/section → method/subsection → line range`
Include all parts you can determine. Never omit the file path.

### Step 3 — Explain in Plain English

One short paragraph (3-5 sentences max). Rules:
- Define every term on first use: "JWT (a signed token the server
  can verify later)"
- Cover: what it does, why it matters, what it hands off to
- No jargon left undefined

### Step 4 — Show Connections (Code Mode Only)

After explaining code, show what it calls and what calls it:

```
→ calls:     src/services/token.ts → TokenService → verify() → L8
→ called by: src/routes/api.ts → router.use() → L8
```

If connections cannot be determined: "I couldn't trace the full
call chain — want me to search deeper?"

### Step 5 — Predict Next

End every answer with 2-3 specific follow-up options:

> **Next — want to:**
> - **Trace back**: where does this token get created?
> - **Forward**: what happens when `req.user` hits the controller?
> - **Jump**: show me the DB save on signup

Options must be specific to what was just shown. Never use generic
options like "learn more" or "continue".
```

- [ ] **Step 4: Commit the answer loop**

```bash
git add plugin/SKILL.md
git commit -m "feat: add answer loop to SKILL.md"
```

- [ ] **Step 5: Add the Research Priority section**

Insert immediately after the Answer Loop block (before Phase 1):

```markdown
## Research Priority

When finding an artifact, check tools in this order:

1. **Agent Brain** (if installed + indexed)
   Check: `which agent-brain 2>/dev/null`
   If available: use semantic search first
   If unavailable: fall back to tier 3 silently
   Surface unavailability only when question requires it:
   > "I can answer this better with Agent Brain — want me to
   >  set it up? Or I can scan the codebase directly."

2. **Perplexity** (if available — for external context only)
   Use for: library docs, framework behavior, external APIs
   If unavailable: fall back to tier 3 silently
   Surface only when external knowledge is specifically needed:
   > "I can look this up in Perplexity for the official docs —
   >  want me to? Or I can explain from what I see in the code."

3. **Codebase scan** (always available — reliable baseline)
   Tools: grep, glob, file reads
   Use when: Agent Brain unavailable, question is code-specific

4. **Markdown parse** (always available)
   Use when: --file mode, README/docs scanning
```

- [ ] **Step 6: Commit research priority**

```bash
git add plugin/SKILL.md
git commit -m "feat: add research priority section to SKILL.md"
```

- [ ] **Step 7: Add Mode Detection section**

Insert immediately before Phase 1:

```markdown
## Mode Detection

On invocation, detect mode from args or opening question:

| Trigger | Mode | Reference to load |
|---|---|---|
| `--describe` | Describe | `references/describe-questions.md` |
| `--explore` | Explore | `references/explore-questions.md` |
| `--file <path>` | File | *(none — use markdown parse)* |
| No args | Ask user | Show mode options, then load |

If no args: ask once before scanning:
> "I can work in two ways — **describe** the codebase (you tell
>  me what's here) or **explore** it (I walk you through as a
>  new developer would). Which fits?"

After mode detection, load the relevant reference file before
proceeding. **Do not load both reference files simultaneously.**
```

- [ ] **Step 8: Commit mode detection**

```bash
git add plugin/SKILL.md
git commit -m "feat: add mode detection to SKILL.md"
```

---

## Task 2: Write the Describe Mode Question Bank

**Files:**
- Create: `plugin/references/describe-questions.md`

- [ ] **Step 1: Define verification criteria before writing**

```bash
cat > /tmp/describe-criteria.txt << 'EOF'
CHECK-1: Every question has a trigger condition (not always asked)
CHECK-2: Follow-up logic is deterministic (not "maybe ask this")
CHECK-3: Output schema includes all sections from spec:
  Overview, Entry Points, Auth, Data Layer, Key Concepts,
  Traced Call Chains, Constraints, Open Questions
CHECK-4: SESSION-TRANSCRIPT.md listed in output
CHECK-5: Output path uses {resolved_storage}/docs/{session_id}/
EOF
```

- [ ] **Step 2: Create describe-questions.md**

Create `plugin/references/describe-questions.md`:

```markdown
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
```

- [ ] **Step 3: Verify describe-questions.md against criteria**

```bash
cat /tmp/describe-criteria.txt
```

Check each criterion manually:
- [ ] CHECK-1: Every question has a trigger condition ✓
- [ ] CHECK-2: Follow-up logic is deterministic ✓
- [ ] CHECK-3: All 8 output sections present ✓
- [ ] CHECK-4: SESSION-TRANSCRIPT.md listed ✓
- [ ] CHECK-5: Path uses `{resolved_storage}/docs/{session_id}/` ✓

- [ ] **Step 4: Commit**

```bash
git add plugin/references/describe-questions.md
git commit -m "feat: add Describe mode question bank with output schema"
```

---

## Task 3: Write the Explore Mode Tour Structure

**Files:**
- Create: `plugin/references/explore-questions.md`

- [ ] **Step 1: Define verification criteria**

```bash
cat > /tmp/explore-criteria.txt << 'EOF'
CHECK-1: Steps are in learning order (not file/folder order)
CHECK-2: Each step references the Answer Loop
CHECK-3: Mid-tour interrupt handling specified
CHECK-4: Navigation commands referenced (not duplicated)
CHECK-5: TOUR.md output path = {resolved_storage}/docs/{session_id}/TOUR.md
CHECK-6: SESSION-TRANSCRIPT.md listed in output
EOF
```

- [ ] **Step 2: Create explore-questions.md**

Create `plugin/references/explore-questions.md`:

```markdown
# Explore Mode — Tour Structure

Load this file when `--explore` mode activates. Contains the
learning-order tour steps and follow-up logic for Explore mode.

## When to Load

Load after repo scan completes. Do not load during Describe or
File mode.

## Opening

After scan, greet with what you found — framed for a newcomer:

> "Okay — let me walk you through this like you've never seen it
>  before. I'll go in the order that makes sense to learn it, not
>  the order the files happen to be in. Say 'next' to advance,
>  or ask anything at any point."

## Tour Steps (Learning Order)

Work through these in order. At each step: apply the full Answer
Loop (show code block with anchor first, then explain, then show
connections, then predict next).

### Step 1: What the App Does

Show the README intro or the main entry point comment/docstring
with anchor. Explain in 3 sentences: what it does, who uses it,
what problem it solves.

### Step 2: Entry Point

Show the main entry file with anchor. Trace the first 10-20 lines.
Explain: how the app boots, what gets registered, startup sequence.
Show connections: what does the entry file call first?

### Step 3: Auth Flow

Find the auth entry point (from scan-patterns.md auth detection).
Show the login/token verification handler with anchor. Trace one
auth request from entry to response.

If no auth found:
> "I don't see an auth layer — this might be a public API or an
>  internal tool. Want to skip to how data flows? (Step 4)"

### Step 4: Data Flow

Find the main data access pattern (ORM, raw SQL, API calls).
Show one representative data fetch with anchor. Trace:
request → handler → data layer → response.

### Step 5: Where to Make a First Change

Find the simplest, most self-contained feature area (typically:
one route + handler + model). Show it with anchor. Explain what a
good first PR would look like here.

> "If I were new to this repo and had to make my first change,
>  I'd start in [file] — here's why..."

## Navigation During Tour

The navigation commands from navigation-commands.md work throughout:
- `"rewind"` / `"go back"` → return to previous step
- `"skip"` → jump to next step
- `"jump to [topic]"` → skip to specific step or topic
- `"hold on — what's X?"` → pause tour, answer question fully,
  then offer: "Back to Step [N]? Or keep exploring here?"

## Mid-Tour Interrupts

If user asks an off-topic question mid-tour:
1. Answer it fully (apply the full Answer Loop)
2. Offer: "Back to Step [N] ([step name])? Or want to keep
   exploring this area?"

## Output

After completing tour or when user says "done", offer:
> "Want me to save this as TOUR.md? It'll read like a guide a
>  new developer can follow on their own."

On confirmation, generate these files in `{resolved_storage}/docs/{session_id}/`:

**TOUR.md:**
Each step with its code block anchor, explanation, and any
follow-up Q&A. Formatted as a re-readable learning guide.

**SESSION-TRANSCRIPT.md:**
Full conversational flow in order with all code blocks.
Always generated alongside TOUR.md.
```

- [ ] **Step 3: Verify against criteria**

```bash
cat /tmp/explore-criteria.txt
```

Check each criterion manually:
- [ ] CHECK-1: Learning order (app → entry → auth → data → first change) ✓
- [ ] CHECK-2: Each step references Answer Loop ✓
- [ ] CHECK-3: Mid-tour interrupt handling present ✓
- [ ] CHECK-4: Navigation referenced, not duplicated ✓
- [ ] CHECK-5: Path = `{resolved_storage}/docs/{session_id}/TOUR.md` ✓
- [ ] CHECK-6: SESSION-TRANSCRIPT.md listed ✓

- [ ] **Step 4: Commit**

```bash
git add plugin/references/explore-questions.md
git commit -m "feat: add Explore mode tour structure with navigation support"
```

---

## Task 4: Add File Mode to SKILL.md

**Files:**
- Modify: `plugin/SKILL.md`

- [ ] **Step 1: Define verification criteria**

```bash
cat > /tmp/file-mode-criteria.txt << 'EOF'
CHECK-1: File mode produces FILE-NOTES.md
CHECK-2: Output path = {resolved_storage}/docs/{session_id}/FILE-NOTES.md
CHECK-3: SESSION-TRANSCRIPT.md also produced
CHECK-4: Answer loop applied to each section
CHECK-5: "next" advances through sections
EOF
```

- [ ] **Step 2: Add File Mode phase to SKILL.md**

Insert after Phase 2 (Question Handling):

```markdown
## Phase 2b: File Mode (`--file <path>`)

Triggered by `--file <path>` arg, or when user says "explain this
file" / "walk me through this doc" while pointing at a .md file.

### Step 1 — Parse Structure

Read the file. Extract heading hierarchy as a section list:
```
[ "## Overview", "## Requirements", "### Auth", ... ]
```

Report to user:
> "This doc has [N] sections. I'll walk through them one at a
>  time. Say 'next' to advance or ask anything about what I
>  just showed."

### Step 2 — Walk Each Section (apply Answer Loop)

For each section:
1. Quote the section content as a code block with anchor:
   `// ROADMAP.md → Phase 3: Auth → "Requirements" → L14-31`
2. Explain it (Answer Loop steps 3-5, omit connections step)
3. Ask one follow-up question if context warrants:
   > "The spec says 'email verification required' — is that
   >  already in the codebase or still to-build?"

### Step 3 — Capture Answers

Every user answer is added to session stack (captured by
Agent Rulez or in-memory buffer — see Plan 2).

### Step 4 — Section Transitions

After each section:
> **Next — want to:**
> - **Next section**: [section name]
> - **Deeper here**: ask me more about this section
> - **Jump to**: [specific section name]

### File Mode Output

After completing or when user says "done", offer:
> "Want me to save FILE-NOTES.md? It'll have each section with
>  my explanation and your follow-up Q&A."

On confirmation, generate in `{resolved_storage}/docs/{session_id}/`:

**FILE-NOTES.md:**
Each section with anchor, explanation, and captured Q&A.
"Still open" items where questions couldn't be answered.

**SESSION-TRANSCRIPT.md:**
Full conversational flow with all code blocks.
Always generated alongside FILE-NOTES.md.

### Anti-Patterns

- Never explain the whole file at once before the user asks
- Never skip sections silently — always offer to skip explicitly
- Never invent content not in the document
```

- [ ] **Step 3: Verify against criteria**

```bash
cat /tmp/file-mode-criteria.txt
```

Check each criterion manually against the written content.

- [ ] **Step 4: Commit**

```bash
git add plugin/SKILL.md
git commit -m "feat: add File mode (--file <path>) to SKILL.md"
```

---

## Task 5: Update SKILL.md Frontmatter

**Files:**
- Modify: `plugin/SKILL.md`

- [ ] **Step 1: Replace the frontmatter block**

Update to:

```yaml
---
name: codebase-wizard
description: >
  Universal explainer for codebases, specs, design docs, and markdown files.
  Activates when a user wants to understand how their code works, explore a
  new codebase, document an existing one, or get walked through any markdown
  artifact (specs, roadmaps, design docs, milestone plans).

  Trigger on: "explain this codebase", "walk me through this", "describe
  this code", "I'm new to this repo", "how does X work", "what calls this",
  "where does this get used", "explain this spec", "walk me through this
  roadmap", "what does this milestone mean", "explain this design doc",
  "--describe", "--explore", "--file <path>".

  Also triggers when user pastes code or a markdown file and asks questions
  about it — treat as a micro-artifact.

  Produces (written to {resolved_storage}/docs/{session_id}/):
    - SESSION-TRANSCRIPT.md (all modes — always generated)
    - CODEBASE.md (describe mode)
    - TOUR.md (explore mode)
    - FILE-NOTES.md (file mode)
---
```

- [ ] **Step 2: Read the full SKILL.md and verify end-to-end flow**

```bash
wc -l plugin/SKILL.md
```

Expected: substantially longer than original (300+ lines). Read fully and verify:
- [ ] Frontmatter at top
- [ ] Core Principles block
- [ ] Answer Loop (new)
- [ ] Research Priority (new)
- [ ] Mode Detection (new)
- [ ] Phase 1 (existing, unchanged)
- [ ] Phase 2 (existing, updated to reference Answer Loop)
- [ ] Phase 2b: File Mode (new)
- [ ] Phase 3-5 (existing, unchanged)

- [ ] **Step 3: Commit**

```bash
git add plugin/SKILL.md
git commit -m "feat: update SKILL.md frontmatter with modes, triggers, and output docs"
```

---

## Task 6: Manual Skill Verification Against Invariants

**Files:**
- No changes — verification only

- [ ] **Step 1: Verify Answer Loop invariants against SKILL.md**

```bash
cat /tmp/wizard-invariants.txt
```

For each invariant, grep the SKILL.md to confirm it's enforced:

```bash
grep -n "code block" plugin/SKILL.md | head -5
grep -n "anchor" plugin/SKILL.md | head -5
grep -n "Next — want to" plugin/SKILL.md | head -5
grep -n "calls:" plugin/SKILL.md | head -5
```

All four should return hits. If any return empty, the invariant is not enforced.

- [ ] **Step 2: Verify SESSION-TRANSCRIPT.md appears in all output schemas**

```bash
grep -rn "SESSION-TRANSCRIPT" plugin/
```

Expected hits:
- `plugin/SKILL.md` (frontmatter Produces section)
- `plugin/references/describe-questions.md` (output schema)
- `plugin/references/explore-questions.md` (output schema)
- `plugin/SKILL.md` (Phase 2b output section)

If any are missing, add them before proceeding.

- [ ] **Step 3: Verify output paths use `{resolved_storage}`**

```bash
grep -rn "resolved_storage" plugin/
```

Expected: appears in describe-questions.md, explore-questions.md, SKILL.md Phase 2b.
No `{storage}` should appear without `resolved_` prefix.

```bash
grep -rn '"{storage}' plugin/
```

Expected: zero hits. If any found, replace with `{resolved_storage}`.

- [ ] **Step 4: Verify CODEBASE.md schema has all 8 sections**

```bash
grep -A 50 "CODEBASE.md" plugin/references/describe-questions.md | grep "^##"
```

Expected sections: Overview, Entry Points, Auth, Data Layer, Key Concepts, Traced Call Chains, Constraints, Open Questions.
If Constraints is missing, add it.

- [ ] **Step 5: Run `/improving-skills` on the skill**

In a Claude Code session:
```
/improving-skills plugin/SKILL.md
```

Grade target: ≥70.

If score is 60-69: review feedback, address top 3 issues, re-run.
If score is <60: surface to human for guidance — do not proceed to Plan 2.

- [ ] **Step 6: Commit any fixes**

```bash
git add plugin/SKILL.md plugin/references/
git commit -m "fix: address issues found during skill verification"
```

---

## Plan 1 Completion Checklist

- [ ] `plugin/SKILL.md` has: answer loop, research priority, mode detection, file mode, updated frontmatter
- [ ] `plugin/references/describe-questions.md` exists with question bank + output schema
- [ ] `plugin/references/explore-questions.md` exists with learning-order tour
- [ ] All mode output schemas include SESSION-TRANSCRIPT.md
- [ ] All output paths use `{resolved_storage}/docs/{session_id}/`
- [ ] CODEBASE.md schema has all 8 sections including Constraints
- [ ] `/improving-skills` score ≥70
- [ ] All invariant grep checks pass

**Next:** Plan 2 — Capture + Synthesis (`agent-rulez-sample.yaml`, session JSON, `/codebase-wizard-export`)
