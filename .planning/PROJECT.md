# Codebase Wizard

## Current Milestone: v1.2 — OpenCode + PyPI

**Goal:** Expand the `ai-codebase-mentor` Python package to support OpenCode (via a new `opencode.py` converter) and publish the package to PyPI on semver tag via a GitHub Actions publish workflow.

**Target features:**
- ✓ `opencode.py` — converts Claude Code plugin format (agents, commands) to OpenCode native format (Phase 8 complete 2026-03-22)
- ✓ `ai-codebase-mentor install --for opencode` works end-to-end with clean install/uninstall (Phase 8 complete)
- ✓ `publish-pypi.yml` — GitHub Actions workflow that publishes to PyPI on semver tag push (Phase 9 complete 2026-03-22)
- ✓ `pip install ai-codebase-mentor` works from PyPI (v1.2.0 published)

## What This Is

A multi-runtime AI plugin and Python package that transforms codebases into well-documented knowledge bases through a wizard-style Q&A interface. The plugin runs in Claude Code, OpenCode, Codex, Gemini, and LangChain DeepAgent. The `ai-codebase-mentor` Python package installs the correct format for each runtime via per-runtime converters.

## Core Value

A developer can run one command and walk away with a documented codebase — without clicking "Approve" fifteen times or writing documentation by hand.

## Requirements

### Validated

<!-- Existing plugin/SKILL.md already ships these capabilities -->

- ✓ Repo scanning (entry points, folder roles, auth, data layer, docs) — existing
- ✓ Conversational Q&A about code (show snippet → explain → predict next) — existing
- ✓ Session history stack with navigation (rewind, jump, bookmarks) — existing
- ✓ Tutorial mode (parse docs into steps, walk user through) — existing
- ✓ Session persistence (save/load as markdown, restore session state) — existing
- ✓ Tone and formatting rules (chat-feel.md governs all phases) — existing

### Validated in Phase 03: permission-agents-commands

- ✓ Pre-authorized agent definitions (policy islands) for zero-approval execution — `plugin/agents/codebase-wizard-agent.md` with 15 scoped allowed_tools
- ✓ `/setup` command: installs Agent Rulez, writes `settings.local.json` permissions, creates agent definition files — `plugin/commands/codebase-wizard-setup.md`
- ✓ `/export` command: manual trigger to synthesize raw logs → formatted docs — `plugin/commands/codebase-wizard-export.md`
- ✓ Cross-platform tool name mapping (Claude Code / OpenCode / Gemini CLI / Codex) — `plugin/references/codex-tools.md`
- ✓ Main `/codebase-wizard` command with `context: fork` + agent reference — `plugin/commands/codebase-wizard.md`

### Active

- [ ] Two-mode wizard: **Describe mode** (repo owner) and **Explore mode** (new developer)
- [ ] Wizard asks follow-up questions to fill context Claude cannot infer (ownership, intent, constraints)
- [ ] Raw Q&A auto-captured as JSON/YAML to `.claude/code-wizard/` or `.code-wizard/`
- [ ] Check both storage locations; ask user preference on first run if neither exists
- [ ] On-demand synthesis: transcript `.md` + structured `CODEBASE.md` generated from raw logs
- [ ] Agent Rulez integration for hook-based auto-capture (PostToolUse/Stop hooks)
- [ ] Sample Agent Rulez YAML config ships with the plugin

### Out of Scope

- Real-time collaboration / multi-user sessions — single-developer tool
- Cloud sync of captured sessions — local-only storage
- IDE integrations (VS Code extension, etc.) — Claude Code CLI only
- Automatic git commits of generated docs — user decides what to commit

## Context

The existing `plugin/SKILL.md` provides a strong 5-phase foundation (scan → Q&A → nav → tutorial → persist). The new work extends this foundation rather than replacing it. The codebase map in `.planning/codebase/` provides architecture context for planning.

Agent Rulez (https://github.com/SpillwaveSolutions/agent_rulez) provides the hook infrastructure for auto-capture. The setup command bootstraps it so users don't have to configure hooks manually.

The policy islands pattern (documented in the article provided) is the architectural model for permission management: skills contain automation logic, agents define permission boundaries, commands are thin wrappers that fork into agents.

## Constraints

- **Platform**: Claude Code (v1.0 ✓), OpenCode (v1.2), Codex (v1.3), Gemini (v1.4), LangChain DeepAgent (v1.5)
- **Storage**: Local filesystem only (`.claude/code-wizard/` or `.code-wizard/`)
- **Hook infrastructure**: Agent Rulez must be installable without elevated permissions
- **Agent Rulez**: Hooks declared in YAML, not hardcoded in settings.json

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two separate modes (Describe/Explore) | Repo owners and newcomers have different goals and question sets | — Pending |
| Raw storage as JSON/YAML, docs generated on-demand | Avoids reprocessing; raw log is source of truth | — Pending |
| Check both `.claude/code-wizard/` and `.code-wizard/` | Users with multiple agents prefer top-level; Claude Code users may prefer `.claude/` | — Pending |
| Agent Rulez for hooks instead of hardcoded hooks | Declarative YAML config is portable and auditable | — Pending |
| Policy islands pattern for all agents | Eliminates approval fatigue; permissions declared once upfront | — Pending |

| Approach A (monorepo + converters) | Claude format is canonical; converters generate runtime-specific artifacts on install — no duplication | ✓ Good — shipping v1.0 |
| Separate plugin.json and marketplace.json | install manifest stays clean; marketplace server adds discovery metadata separately | ✓ Good |
| `runtime: "claude-code"` in plugin.json | converter selector key consumed by CLI to dispatch correct RuntimeInstaller subclass | ✓ Good |
| Lazy import in `_get_converters()` | adding new runtimes requires only adding to the dict — no CLI structural change | ✓ Good |

---
*Last updated: 2026-03-22 — Milestone v1.2 complete: opencode.py + PyPI publish (v1.2.0)*
