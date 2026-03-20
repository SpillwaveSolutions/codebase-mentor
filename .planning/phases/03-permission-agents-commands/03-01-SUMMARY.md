---
phase: 3
plan: 1
subsystem: permission-agents-commands
tags: [agents, commands, multi-platform, permissions, codex]
dependency_graph:
  requires: [02-01]
  provides: [codebase-wizard-agent, codebase-wizard-command, codex-tools, platform-detection]
  affects: [plugin/agents, plugin/commands, plugin/references, plugin/setup]
tech_stack:
  added: []
  patterns: [policy-island-agent, context-fork, platform-case-dispatch, exit-77-skip-convention]
key_files:
  created:
    - plugin/agents/codebase-wizard-agent.md
    - plugin/commands/codebase-wizard.md
    - plugin/references/codex-tools.md
  modified:
    - plugin/setup/setup.sh
decisions:
  - context:fork on main wizard command to isolate wizard from user's main context
  - exit 77 as the conventional skip code for Codex hook installation
  - install_codex writes AGENTS.md with manual export instructions
  - deploy_hooks() extracted as shared function used by claude/opencode/gemini but not codex
metrics:
  duration_seconds: 222
  tasks_completed: 5
  files_created: 4
  files_modified: 1
  completed_date: "2026-03-20"
---

# Phase 3 Plan 1: Permission Agents + Commands + Multi-Platform Summary

**One-liner:** Policy island agent with 15 scoped allowed_tools, main wizard command with context:fork, 4-platform codex-tools matrix, and RUNTIME-dispatched setup.sh with Codex exit-77 skip convention.

---

## Objective

Ship the policy island agent, the main wizard command, the cross-platform tool name reference, and platform detection in setup.sh — completing the permission and delivery layer for the Codebase Wizard.

---

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Write the Policy Island Agent | 92117f1 | plugin/agents/codebase-wizard-agent.md |
| 2 | Write the Main Wizard Command | fce4784 | plugin/commands/codebase-wizard.md |
| 3 | Write codex-tools.md | 86076b5 | plugin/references/codex-tools.md |
| 4 | Add Platform Detection to setup.sh | 8d7382e | plugin/setup/setup.sh |
| 5 | End-to-End Verification | — | No file changes; all checks passed |

---

## Deliverables

### plugin/agents/codebase-wizard-agent.md

Policy island agent with 15 allowed_tools entries organized into 5 permission groups:

1. **File exploration** (Read, Glob, Grep) — unrestricted paths; wizard must read any file it explains
2. **Session storage writes** — Write/Edit scoped to `.code-wizard/**` and `.claude/code-wizard/**` only
3. **Scan and synthesis helpers** — Bash restricted to `node*`, `grep*`, `find*`, `cat*`, `ls*`
4. **Agent Rulez hook management** — Bash(`rulez*`) for hook registration and query
5. **Research tools** — WebSearch and WebFetch pre-authorized; runtime availability-probed before use

Security boundary: the agent cannot write outside the two wizard directories. Any attempt to modify source files is blocked by the allowed_tools list.

### plugin/commands/codebase-wizard.md

Main wizard command with:
- `context: fork` in frontmatter (isolates wizard session from user's main context)
- `agent: codebase-wizard-agent` in frontmatter (loads the policy island)
- All three args documented: `--describe`, `--explore`, `--file <path>`
- Mode detection routing table with reference file loaded per mode
- SKILL.md identified as the driving logic; command is entry point only

### plugin/references/codex-tools.md

4-platform tool name matrix with all 8 pairs:

| Claude Code | OpenCode | Gemini CLI | Codex |
|-------------|----------|------------|-------|
| Read | read | read_file | file_read |
| Write | write | write_file | file_write |
| Edit | edit | replace | file_edit |
| Bash | bash | run_shell_command | shell |
| Grep | grep | search_file_content | grep_search |
| Glob | glob | glob | file_glob |
| WebSearch | websearch | google_web_search | web_search |
| WebFetch | webfetch | web_fetch | web_fetch |

Dedicated section on Codex lack of hook support with manual export instruction. Translation notes for Edit/replace/file_edit interface differences and Bash/shell sandboxing considerations.

### plugin/setup/setup.sh (extended)

Added `RUNTIME="${1:-claude}"` and a case statement with all 5 branches:
- `claude` — install_claude() (original Plan 2 logic, now in named function)
- `opencode` — install_opencode() (deploys hooks, notes lowercase tool names)
- `gemini` — install_gemini() (deploys hooks, notes snake_case tool names)
- `codex` — install_codex() (writes AGENTS.md, prints manual export notice, exits 77)
- `all` — install_all() (runs all four; catches exit 77 from codex branch)

Shared functions extracted: `resolve_storage()`, `write_config()`, `deploy_hooks()`.

---

## Verification Results

All checks pass:

- [x] `plugin/agents/codebase-wizard-agent.md` exists with 15 allowed_tools entries
- [x] `plugin/commands/codebase-wizard.md` has `context: fork` in frontmatter
- [x] `plugin/commands/codebase-wizard.md` has `agent: codebase-wizard-agent` in frontmatter
- [x] `plugin/references/codex-tools.md` has all 8 tool pairs across Claude Code / OpenCode / Gemini CLI / Codex
- [x] `plugin/setup/setup.sh` has `RUNTIME` case statement with all 5 branches
- [x] `install_codex` function prints manual export message and exits with code 77
- [x] Plan 2 commands (`codebase-wizard-export.md`, `codebase-wizard-setup.md`) still present and unmodified

---

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `context: fork` on main wizard command | Isolates wizard session from user's main Claude context; required for the policy island to take effect |
| Exit code 77 for Codex | Conventional "skip" signal in multi-platform install scripts; not an error; caught by `install_all` without failing overall install |
| `install_codex` writes `AGENTS.md` | Codex's instruction file mechanism; documents manual export requirement permanently in the repo |
| Shared `deploy_hooks()` function | DRY across claude/opencode/gemini installs; codex branch intentionally does not call it |
| Read-only tools unrestricted | Wizard must be able to read any file it explains — restricting Read paths would break core show-then-explain contract |

---

## Deviations from Plan

None — plan executed exactly as written.

---

## Self-Check

### Created files exist:
- plugin/agents/codebase-wizard-agent.md — confirmed (154 lines)
- plugin/commands/codebase-wizard.md — confirmed (100 lines)
- plugin/references/codex-tools.md — confirmed (122 lines)
- plugin/setup/setup.sh (modified) — confirmed (241 lines)

### Commits exist:
- 92117f1 — feat(03-01): create policy island agent with 15 scoped allowed_tools
- fce4784 — feat(03-01): create main wizard command with context:fork and agent reference
- 86076b5 — feat(03-01): create codex-tools.md with 4-platform tool name matrix
- 8d7382e — feat(03-01): add platform detection to setup.sh with RUNTIME case statement

## Self-Check: PASSED
