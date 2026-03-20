# Phase 1: Core Wizard Skill - Context

**Gathered:** 2026-03-19
**Status:** Complete ✓

<domain>
## Phase Boundary

Phase 1 delivered the core conversational explainer skill — the behavioral engine that makes the wizard work. Specifically:

- Answer Loop behavioral contract (5-step pattern enforced on every response without exception)
- Research Priority tier system (4 tiers: Agent Brain → Perplexity → codebase scan → markdown parse)
- Mode detection routing (`--describe`, `--explore`, `--file <path>`, no-args)
- Describe mode question bank (`describe-questions.md`) with 7-question ordered set and CODEBASE.md output schema (8 sections)
- Explore mode 5-step learning-order tour (`explore-questions.md`) with navigation and mid-tour interrupt handling, and TOUR.md output schema
- File mode (`--file <path>`) — section-by-section walk of any markdown artifact with FILE-NOTES.md output
- Updated SKILL.md frontmatter (renamed from `codebase-mentor` to `codebase-wizard`, full trigger list, all 4 output artifacts documented)

What Phase 1 did NOT include: Agent Rulez hook integration, `/codebase-wizard-export` synthesis command, `/codebase-wizard-setup` command, storage resolution, raw session JSON capture, multi-platform support, or `codex-tools.md`. Those belong to Phases 2 and 3.

</domain>

<decisions>
## Implementation Decisions

### SKILL.md Extension Strategy
- Extend existing SKILL.md rather than replace it — the 5-phase foundation (scan → Q&A → nav → tutorial → persist) was already solid; new sections (Answer Loop, Research Priority, Mode Detection, Phase 2b File Mode) were inserted between existing phases
- Rename from `codebase-mentor` to `codebase-wizard` in frontmatter only — the underlying file path stays `plugin/SKILL.md`
- SKILL.md contains: mode detection, the answer loop, research tool priority, session stack management, and calls to load reference files on-demand; question logic lives in reference files, not SKILL.md

### Answer Loop
- Enforced on every response without exception — all modes, all artifact types
- Five steps in fixed order: (1) find artifact, (2) show code block with anchor, (3) explain in plain English, (4) show connections (code mode only), (5) predict next
- INVARIANT-1: Code block with anchor must appear before any explanation text — never explain something you haven't found and shown
- INVARIANT-2: Anchor format is `// file → class/section → method/subsection → line range` — all parts that can be determined must be included; file path is never omitted
- INVARIANT-3: Every response ends with "Next — want to:" followed by exactly 2-3 options that are specific to what was just shown — generic options like "learn more" or "continue" are banned
- INVARIANT-4: Explanation is limited to 3-5 sentences in one short paragraph
- INVARIANT-5: `→ calls:` and `→ called by:` lines are shown after code explanations; if call chain cannot be traced, offer to search deeper rather than omitting silently

### Mode Detection
- Mode is detected from invocation args or opening question before any scanning begins
- `--describe` → loads `references/describe-questions.md`, runs repo scan first, asks questions for context Claude cannot infer
- `--explore` → loads `references/explore-questions.md`, runs same scan, guides through learning order
- `--file <path>` → no reference file loaded; uses markdown parse directly; walks section by section
- No args → ask user once before scanning: "I can work in two ways — describe the codebase or explore it. Which fits?"
- Do not load both reference files simultaneously — load only the one relevant to the active mode

### Reference File Loading
- Lazy loading — one reference file per mode, loaded on-demand when mode activates, not all at once
- `chat-feel.md` is always in context across all phases (unchanged from original skill design)
- `describe-questions.md` and `explore-questions.md` are never loaded together
- File mode loads no additional reference file — markdown parse is sufficient

### Output Storage Contract
- All output paths use `{resolved_storage}/docs/{session_id}/` consistently — single storage contract across all modes
- SESSION-TRANSCRIPT.md is always generated alongside every mode's primary output document
- Output document per mode: CODEBASE.md (Describe), TOUR.md (Explore), FILE-NOTES.md (File)
- Each session gets its own subdirectory under `docs/` — no overwrites between sessions
- Storage resolution itself (`.code-wizard/` vs `.claude/code-wizard/`) is deferred to Phase 2

### Claude's Discretion
- Research tier fallback is silent when Agent Brain or Perplexity are unavailable — Claude falls back to the next tier without announcing it unless the user's question genuinely requires external context the fallback cannot provide
- Describe mode question skipping: skip any question whose answer is already clear from the scan or a prior answer — no fixed minimum number of questions required
- Explore mode allows mid-tour detours and follow-up questions; user can say "next" to advance or ask freely

</decisions>

<specifics>
## Specific Ideas

- Anchor format decided explicitly: `// src/auth/middleware.ts → AuthMiddleware → validate() → L14-31` — the double-slash comment prefix, arrow separators, and line range suffix are all literal format requirements
- Connections format decided explicitly: `→ calls: src/services/token.ts → TokenService → verify() → L8` and `→ called by: src/routes/api.ts → router.use() → L8` — arrow prefix, space, label, colon, space, full anchor
- "Next — want to:" header followed by bolded action label and specific question — e.g., `**Trace back**: where does this token get created?`
- Describe mode starts with a scan-first announcement: "I can see [X] in [file], [Y] in [folder] — let me ask a few things I can't figure out from the code alone." — then enters the question bank
- Describe mode question bank has 7 questions across 4 categories: Ownership (Q1 folder ownership, Q2 folder intent), Intent (Q3 original purpose, Q4 current purpose vs. original), Domain Terms (Q5 domain vocabulary), Constraints (Q6 tech constraints, Q7 missing pieces)
- Explore mode follows a strict 5-step learning order: (1) what the app does, (2) where it starts, (3) how auth works, (4) how data flows, (5) where to make a first change — this is not file order
- File mode walks heading structure: parses all headings into a section list, then visits each one in document order showing the content block, explaining it, and offering follow-up before advancing
- CODEBASE.md output schema has exactly 8 sections: Overview, Entry Points, Auth, Data Layer, Key Concepts (from Q&A), Traced Call Chains, Constraints, Open Questions
- Greet with concrete offer after scan — do NOT say "How can I help you today?"; instead name what you found: "Hey — I can see auth in `/src/auth.js`, login in `/routes/user.js`, and a README tutorial on onboarding."
- No-args mode selection prompt is word-for-word specified: "I can work in two ways — **describe** the codebase (you tell me what's here) or **explore** it (I walk you through as a new developer would). Which fits?"
- Research tier 1 availability check: `which agent-brain 2>/dev/null` — lightweight probe before use
- Research tier 2 surface message is word-for-word specified: "I can look this up in Perplexity for the official docs — want me to? Or I can explain from what I see in the code."

</specifics>

<canonical_refs>
## Canonical References

### Spec
- `docs/superpowers/specs/2026-03-19-codebase-wizard-design.md` §1-2 — Architecture, answer loop, modes, research priority
- `docs/superpowers/plans/2026-03-19-codebase-wizard-plan1-core-skill.md` — Detailed task steps and invariants

### Built artifacts
- `plugin/SKILL.md` — Extended with answer loop, research priority, mode detection, File mode, updated frontmatter
- `plugin/references/describe-questions.md` — Describe mode question bank + CODEBASE.md output schema
- `plugin/references/explore-questions.md` — Explore mode learning-order tour + TOUR.md output schema

</canonical_refs>

<deferred>
## Deferred Ideas

The following were explicitly scoped out of Phase 1 and pushed to Phase 2 (Capture + Synthesis) and Phase 3 (Multi-Platform):

**Phase 2 — Capture + Synthesis:**
- Agent Rulez PostToolUse and Stop hook integration for auto-capture of Q&A turns to JSON
- Raw session JSON format (`{resolved_storage}/sessions/YYYY-MM-DD-{repo}.json`) — structure defined in spec §3 but not implemented
- `/codebase-wizard-export` command — synthesizes raw session JSON into SESSION-TRANSCRIPT.md + CODEBASE.md / TOUR.md / FILE-NOTES.md
- `/codebase-wizard-setup` command — installs Agent Rulez, writes `settings.local.json`, creates storage directory
- `setup/setup.sh` — storage resolution, Agent Rulez YAML deployment with `{resolved_storage}` substitution
- `setup/agent-rulez-sample.yaml` — hook config template
- `agents/codebase-wizard-agent.md` — policy island with pre-authorized tools
- `commands/codebase-wizard.md`, `commands/codebase-wizard-export.md`, `commands/codebase-wizard-setup.md`
- Storage resolution logic (`.code-wizard/` vs `.claude/code-wizard/`, `config.json` format)
- Hook error handling with in-memory buffer fallback on `on_error: warn`

**Phase 3 — Multi-Platform:**
- OpenCode, Gemini CLI, and Codex platform support
- `references/codex-tools.md` — tool name equivalents for Codex
- `setup.sh` platform detection (`claude` / `opencode` / `gemini` / `codex` / `all`)
- Per-platform config file generation (TOML for Gemini, AGENTS.md for Codex)
- Tool name mapping across platforms (PascalCase Claude Code → lowercase OpenCode → snake_case Gemini)
- Codex hook skip (exit 77 convention, manual export step documented in AGENTS.md)

</deferred>

---

*Phase: 01-core-wizard-skill*
*Context gathered: 2026-03-19*
