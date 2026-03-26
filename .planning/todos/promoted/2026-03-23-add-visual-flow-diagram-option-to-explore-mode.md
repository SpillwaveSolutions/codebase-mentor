---
created: 2026-03-23T23:15:00.000Z
title: Add visual flow diagram as numbered option in explore mode Answer Loop
area: general
files:
  - plugins/codebase-wizard/skills/explaining-codebase/SKILL.md
---

## Problem

When the wizard explains pipeline, orchestration, or multi-step flow concepts, it generates
a wall of text with code anchors. Visual learners (and developers new to a codebase) benefit
far more from an ASCII flow diagram than from a prose explanation. The wizard never offers
"show me a visual flow" as a numbered option.

Observed in first real run (book_generator, 2026-03-23): after explaining the 5-stage pipeline
(generate_book → TOC → refine → chapters → finalize), the wizard ended with open-ended bullets
instead of offering a visual diagram as a follow-up option. The missing option was:

```
> **Next — want to:**
> 1. Visual Flow — show me the pipeline as an ASCII diagram
> 2. Prompt system: how do templates get loaded?
> 3. Data models: TableOfContents, Chapter, Section
>
> *(or just tell me what you want)*
```

## What "Visual Flow" Means

A Visual Flow response generates an ASCII diagram showing the call/data flow through the system.
Example for book_generator:

```
BookGenerator.generate_book()
  │
  ▼
1. PromptProcessor.process_prompt()      ← reads prompt.md
  │
  ▼
2. TOCGenerator.generate_initial_toc()   ← LLM → TableOfContents
  │
  ▼
3. TOCGenerator.refine_toc()             ← feedback loop
  │                                         refine_toc_recency() via Perplexity
  ▼
4. ChapterGenerator.generate_chapters()
  │
  ├── For each chapter (sequential):
  │    │
  │    ├── _generate_chapter_outline()   ← Anthropic
  │    │
  │    └── For each section (parallel, 3 workers):
  │         ├── _generate_section_draft()   ← Anthropic
  │         ├── _refine_section()           ← Anthropic
  │         └── _check_section_recency()    ← OpenAI
  │
  ▼
5. _finalize_book()                      ← copy to book/ output
```

This diagram was missing from the explore session output. The TOUR.md that was generated
manually after the session included it, but the live session Answer Loop did not offer it.

## Solution

In `plugins/codebase-wizard/skills/explaining-codebase/SKILL.md`, add a new option type to the
`Step 5 — Predict Next` section:

**New option type: Visual Flow**

> When explaining a pipeline, orchestration, data flow, or multi-step process:
> - Always include a "Visual Flow" option as one of the numbered follow-ups.
> - When the user picks "Visual Flow", generate an ASCII diagram using `│`, `▼`, `├──`,
>   `└──` box-drawing characters to show the execution flow.
> - Label each node with: function name, file anchor (filename:line), and brief purpose.
> - Show parallel vs sequential branching with indentation and `├──`/`└──`.
> - After the diagram, offer the standard numbered follow-ups again.

**Updated Step 5 example for pipeline contexts:**

```
> **Next — want to:**
> 1. **Visual Flow** — show me the pipeline as an ASCII diagram
> 2. **Prompt system**: how do the markdown templates get loaded?
> 3. **Data models**: what do TableOfContents and Chapter look like in Pydantic?
>
> *(or just tell me what you want)*
```

## Context: UX Rule Reinforcement

This todo is filed alongside the numbered-options todo. Both reinforce the same UX rule:

> **The wizard NEVER ends with an open question or bare bullets. Every response ends with
> numbered options (1–5) plus `*(or just tell me what you want)*`. The options are predictions,
> not requirements — the user can always type anything.**

In the first real session, the export step ended with:
```
▎ Want to continue exploring? We left off with these options:
▎ - Prompt system: how do the markdown templates get loaded and filled?
▎ - Data models: what do TableOfContents, Chapter, and Section look like?
▎ - Config flow: how does config.json control providers and models?
```

This violates the rule on two counts: no numbers and no free-text escape hatch.
