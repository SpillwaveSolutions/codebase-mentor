# Phase 2: Capture + Synthesis - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers the auto-capture and synthesis pipeline. Its scope is:

- **Agent Rulez hook integration** — PostToolUse and Stop hooks that capture Q&A to raw JSON automatically during wizard sessions, without user action
- **Storage resolution and setup** — one-time `setup.sh` that resolves `.code-wizard/` vs `.claude/code-wizard/`, writes `config.json`, installs Agent Rulez, deploys the hook config, registers the hook, and writes `settings.local.json`
- **`/codebase-wizard-export` command** — reads raw session JSON, synthesizes SESSION-TRANSCRIPT.md and CODEBASE.md, TOUR.md, or FILE-NOTES.md depending on mode
- **`/codebase-wizard-setup` command** — one-time onboarding wrapper that runs `setup.sh` from main context (no `context: fork`)
- **`agent-rulez-sample.yaml`** — template hook config with `{resolved_storage}` placeholder; `setup.sh` substitutes the actual path when deploying

**Out of scope for Phase 2 (boundary vs Phase 1):**
- Phase 1 owns: `SKILL.md` wizard logic, answer loop, mode detection, `describe-questions.md`, `explore-questions.md`, `codex-tools.md`, the core Q&A conversational flow

**Out of scope for Phase 2 (boundary vs Phase 3):**
- Phase 3 owns: `plugin/agents/codebase-wizard-agent.md` (policy island), `plugin/commands/codebase-wizard.md` (main wizard command with `context: fork` + `agent:`), multi-platform support (OpenCode, Gemini, Codex), platform-specific setup variants

**Phase 2 success criteria (from ROADMAP.md):**
1. Sessions auto-captured to `.claude/code-wizard/` or `.code-wizard/` without user action
2. `/export` produces SESSION-TRANSCRIPT.md and structured CODEBASE.md from raw logs
3. `/setup` installs Agent Rulez and writes `settings.local.json` permissions

</domain>

<decisions>
## Implementation Decisions

### Storage Resolution
- 3-step resolution order: check `.code-wizard/` first → check `.claude/code-wizard/` second → if neither exists, ask user once, create chosen directory with `sessions/` and `docs/` subdirectories
- `config.json` format: `{ "version": 1, "resolved_storage": ".code-wizard", "created": "2026-03-19T14:00:00Z" }`
- Always check both locations on read (`.code-wizard/config.json` then `.claude/code-wizard/config.json`); write only to resolved location

### Agent Rulez Hook Config
- PostToolUse: `action: append` to `{resolved_storage}/sessions/{date}-{repo}.json`, `format: json`
- Stop: `action: notify` with message `"Session ended. Run /codebase-wizard-export to generate docs."`
- `on_error: warn` on PostToolUse hook — capture failures notify the user but do not abort the session
- `{date}` and `{repo}` are Agent Rulez native interpolation variables: `{date}` → YYYY-MM-DD at hook invocation time; `{repo}` → basename of current working directory
- In-memory buffer fallback if hooks fail — wizard maintains buffer and offers to flush it at session end if hooks failed
- `agent-rulez-sample.yaml` uses `{resolved_storage}` as placeholder; `setup.sh` uses `sed` to substitute the actual resolved path when copying it to `{resolved_storage}/agent-rulez.yaml`
- If Agent Rulez does not support `{date}` / `{repo}` natively, `setup.sh` pre-computes them and writes static values into the deployed YAML

### Raw Session JSON Format
- `version` field (value: `1`) for forward compatibility — export command detects and warns on unrecognized versions
- Top-level fields: `session_id` (YYYY-MM-DD-{repo}), `repo`, `artifact`, `mode` (describe | explore | file), `created` (ISO timestamp)
- `turns` array; each turn contains: `ts`, `question`, `anchor`, `code_shown`, `explanation`, `connections` (`calls` array + `called_by` array), `next_options` array

### setup.sh Responsibilities
5 operational steps in order:
1. Resolve storage — check `.code-wizard/` then `.claude/code-wizard/`; prompt user if neither exists; create chosen dir with `sessions/` and `docs/` subdirectories
2. Write `config.json` — `version`, `resolved_storage`, `created` timestamp — to `{resolved_storage}/config.json`
3. Install Agent Rulez — run `rulez install`
4. Deploy hook config — `sed "s|{resolved_storage}|$RESOLVED_STORAGE|g" agent-rulez-sample.yaml > {resolved_storage}/agent-rulez.yaml`
5. Register hook — run `rulez hook add --config {resolved_storage}/agent-rulez.yaml`
6. Write `settings.local.json` — scoped `Write(.code-wizard/**)` and `Write(.claude/code-wizard/**)` permissions plus `Bash(rulez*)` and `Bash(node .claude/plugins/codebase-wizard/**)`

Note: The plan checklist numbers these as 6 steps; the spec Section 5 also lists 6; the plan completion checklist refers to "5 operational steps" — all sources agree on the same 6 discrete operations.

### Export Command Design
- 3 args: `--latest` (default — most recent file in `sessions/` by ISO date sort), `--session <filename>` (specific file by name), `--all` (every `.json` in `sessions/`, each independently)
- No merging across sessions — each session gets its own output directory
- Output always goes to `{resolved_storage}/docs/{session_id}/`; directory created if it does not exist
- `SESSION-TRANSCRIPT.md` always generated for every mode (full Q&A in order with code blocks and anchors)
- `CODEBASE.md` generated for `mode == "describe"` sessions (sections: Overview, Entry Points, Auth, Data Layer, Key Concepts, Traced Call Chains, Constraints, Open Questions)
- `TOUR.md` generated for `mode == "explore"` sessions (re-readable learning guide in 5-step learning order plus Q&A Detours)
- `FILE-NOTES.md` generated for `mode == "file"` sessions (section-by-section breakdown with captured Q&A)
- Frontmatter: `context: fork`, `agent: codebase-wizard-agent`
- If `config.json` not found in either location: tell user to run `/codebase-wizard-setup` first
- If no session files exist: tell user to run `/codebase-wizard` first

### /codebase-wizard-setup Has No context:fork
- Reason: needs main-context permissions to write `settings.local.json` and install Agent Rulez — operations outside the scoped `codebase-wizard-agent` policy island
- One-time use — not used in regular sessions; `codebase-wizard.md` (Phase 3) is the regular-session command with `context: fork`
- No `agent:` field in frontmatter — runs with full main-context permissions

### Claude's Discretion
- Synthesis formatting details — how turns are assembled into CODEBASE.md sections (e.g., which turns map to Overview vs Entry Points vs Auth) is left to Claude's judgment during export; the command spec provides the output schema, not a mechanical mapping rule
- Exact `sed` substitution approach in `setup.sh` — `sed "s|{resolved_storage}|$RESOLVED_STORAGE|g"` is the specified approach; pipe separator `|` used (not `/`) to avoid conflicts with path slashes

</decisions>

<specifics>
## Specific Ideas

- Session files named: `YYYY-MM-DD-{repo}.json` in `{resolved_storage}/sessions/`
- Each session gets its own docs subdirectory (`{resolved_storage}/docs/{session_id}/`) — no overwrites between sessions; running `--all` produces one subdirectory per session
- `setup.sh` is a template deliverable (user runs it once during onboarding via `/codebase-wizard-setup`)
- `agent-rulez-sample.yaml` uses `{resolved_storage}` as placeholder; `setup.sh` substitutes actual path using `sed` — the sample itself in `plugin/setup/` is never deployed directly
- Open question: Does Agent Rulez support `{date}` and `{repo}` natively? If not, `setup.sh` pre-computes them and writes static paths into the deployed YAML (noted in spec as a known conditional)
- `connections` block in SESSION-TRANSCRIPT.md is omitted if both `calls` and `called_by` are empty arrays; `next_options` block omitted if array is empty — clean output for markdown/file mode sessions that have no call graph
- Export version guard: if `version` field is missing or higher than 1, warn user but attempt synthesis anyway
- `plugin/setup/` directory holds both `setup.sh` and `agent-rulez-sample.yaml` — two files, one directory

</specifics>

<canonical_refs>
## Canonical References

### Spec
- `docs/superpowers/specs/2026-03-19-codebase-wizard-design.md` §3 — Complete Capture + Synthesis spec: storage resolution, hook config, raw session format, synthesis pipeline
- `docs/superpowers/specs/2026-03-19-codebase-wizard-design.md` §5 — Commands spec: `/codebase-wizard-setup` frontmatter (no `context: fork`), `settings.local.json` content, 6-step setup flow
- `docs/superpowers/plans/2026-03-19-codebase-wizard-plan2-capture-synthesis.md` — Step-by-step task execution plan with verification criteria per task

### Dependencies from Phase 1
- `plugin/SKILL.md` — Wizard logic; export command reads sessions produced during wizard sessions; mode field in session JSON must match modes defined in SKILL.md (`describe`, `explore`, `file`)
- `plugin/references/describe-questions.md` — CODEBASE.md output schema (synthesized from Describe mode sessions); export command's CODEBASE.md section structure mirrors this
- `plugin/references/explore-questions.md` — TOUR.md output schema (synthesized from Explore mode sessions); TOUR.md 5-step structure mirrors the explore learning order

### Agent Rulez
- Agent Rulez docs: https://github.com/SpillwaveSolutions/agent_rulez — hook YAML format, `{date}`/`{repo}` variable support, `rulez install` / `rulez hook add --config` CLI commands

</canonical_refs>

<deferred>
## Deferred Ideas

- Platform-specific setup variants (opencode/gemini/codex) — Phase 3
- Policy island agent definition (`plugin/agents/codebase-wizard-agent.md`) — Phase 3
- `/codebase-wizard` main command (with `context: fork` + `agent: codebase-wizard-agent`) — Phase 3
- Export `--format pdf` (via pdf skill) — v2, out of scope
- Merging sessions from different dates into a single output document — out of scope (each session is independent by design)
- Non-markdown file support for `--file` mode (JSON schemas, OpenAPI specs) — deferred to v2 unless trivial
- Real-time collaboration / multi-user sessions — non-goal
- Cloud sync of captured sessions — non-goal (local-only)

</deferred>

---

*Phase: 02-capture-synthesis*
*Context gathered: 2026-03-19*
