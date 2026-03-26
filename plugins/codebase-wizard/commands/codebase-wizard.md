---
description: "Start a wizard session — explain, explore, or document any codebase or artifact."
context: fork
agent: codebase-wizard-agent
---

# /codebase-wizard

Run the Codebase Wizard — a conversational, tutor-style explainer for any
codebase, spec, design doc, or markdown artifact.

---

## Arguments

| Arg | Mode | What happens |
|-----|------|-------------|
| `--describe` | Describe | Wizard scans repo, then asks structured questions to help the owner document what's here |
| `--explore` | Explore | Wizard guides a new developer through the codebase in learning order |
| `--file <path>` | File | Wizard walks through a specific markdown artifact section by section |
| *(none)* | Ask | Wizard asks which mode before scanning |

If no args are provided, the wizard asks once:
> "I can work in two ways — **describe** the codebase (you tell me what's
>  here) or **explore** it (I walk you through as a new developer would).
>  Which fits?"

---

## Mode Detection and Reference File Loading

After detecting the mode, load the corresponding reference file before
proceeding. Never load more than one mode reference at once.

| Mode | Reference loaded | Purpose |
|------|-----------------|---------|
| `--describe` | `references/describe-questions.md` | Ordered question bank, follow-up logic, CODEBASE.md output schema |
| `--explore` | `references/explore-questions.md` | Learning-order tour structure, follow-up logic, TOUR.md output |
| `--file <path>` | *(none — use markdown parse)* | Heading extraction, section-by-section walk |
| *(no args)* | Load after user selects | Same as above based on selection |

---

## Driving Logic

All wizard behavior is governed by `SKILL.md`. This command is the entry
point only; it forks context, loads the policy agent, then hands control
to SKILL.md.

Key behaviors from SKILL.md:
- **Answer Loop** (every response): find artifact → show code block with
  anchor → explain in plain English → show connections → predict next
- **Research Priority**: Agent Brain → Perplexity → codebase scan → markdown parse
- **Session stack**: maintained in working memory; max 20 entries
- **Navigation commands**: "rewind", "jump to", "go back" trigger
  `references/navigation-commands.md`
- **Tutorial mode**: README found or user says "teach me" triggers
  `references/tutorial-mode.md`
- **Persistence**: "save", "export", "load session" triggers
  `references/persistence.md`

---

## Output

The wizard workflow produces docs in two stages:

**Stage 1 — Session capture** (during this command):
Structured session turns are written to `{resolved_storage}/sessions/{session_id}.json`
via the Write tool at each Answer Loop step. Agent Rulez PostToolUse hooks also append
raw tool events to that file.

**Stage 2 — Export** (via `/codebase-wizard-export`):
The export command reads the session JSON and synthesizes the final doc files:

| Mode | Documents generated |
|------|-------------------|
| Describe | `{resolved_storage}/docs/{session_id}/SESSION-TRANSCRIPT.md` + `CODEBASE.md` |
| Explore | `{resolved_storage}/docs/{session_id}/SESSION-TRANSCRIPT.md` + `TOUR.md` |
| File | `{resolved_storage}/docs/{session_id}/SESSION-TRANSCRIPT.md` + `FILE-NOTES.md` |

`SESSION-TRANSCRIPT.md` is always generated in every mode.

Run `/codebase-wizard-export` after the session ends to produce the final docs.

`{resolved_storage}` is read from `{resolved_storage}/config.json`,
written during `/codebase-wizard-setup`.

---

## Session Capture

During the session, Agent Rulez PostToolUse hooks automatically append each
turn to `{resolved_storage}/sessions/YYYY-MM-DD-{repo}.json`.

When the session ends, the Agent Rulez Stop hook fires:
> "Session ended. Run /codebase-wizard-export to generate docs."

If hooks are not installed, the wizard maintains an in-memory buffer and
offers to flush it when the session ends.

---

## Security Context

This command runs in a forked context under `codebase-wizard-agent`. The
agent's `allowed_tools` list restricts all writes to `.code-wizard/**` and
`.claude/code-wizard/**` only. The wizard cannot modify source files,
`.claude/settings.local.json`, or any path outside the wizard directories.

See `agents/codebase-wizard-agent.md` for the full permission manifest.
