# Phase 3: Permission Agents + Commands + Multi-Platform - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

From ROADMAP — Phase 3 delivers pre-authorized agent definitions (policy islands) that eliminate the approval loop, the main wizard command, and multi-platform support. Scope:

- **Policy island agent**: `plugin/agents/codebase-wizard-agent.md` — single source of truth for what tools the wizard may use without prompting
- **3 commands**: main wizard (`codebase-wizard.md` — created in Phase 3), export (`codebase-wizard-export.md` — file created in Phase 2), setup (`codebase-wizard-setup.md` — file created in Phase 2); Phase 3 wires all three to the agent
- **`codex-tools.md`**: full platform tool name matrix (Claude Code / OpenCode / Gemini CLI / Codex), lazy-loaded only on non-Claude Code runtimes
- **`setup.sh` platform detection**: RUNTIME case statement with 5 branches (claude / opencode / gemini / codex / all)
- **Platform support**: Claude Code, OpenCode, Gemini CLI, Codex

**Success criteria (from ROADMAP):**
1. Running /setup once eliminates all "May I?" prompts for subsequent wizard sessions
2. Agents cover: file read/write, bash scan scripts, git read ops
3. Multi-platform support via codex-tools.md

</domain>

<decisions>
## Implementation Decisions

### Policy Island Agent (codebase-wizard-agent.md)

Exact `allowed_tools` entries (15 total):

```yaml
allowed_tools:
  # File exploration (read-only, unrestricted paths)
  - "Read"
  - "Glob"
  - "Grep"

  # Session storage writes (scoped to wizard dirs only — cannot write elsewhere)
  - "Write(.code-wizard/**)"
  - "Write(.claude/code-wizard/**)"
  - "Edit(.code-wizard/**)"
  - "Edit(.claude/code-wizard/**)"

  # Scan and synthesis (no destructive operations)
  - "Bash(node*)"
  - "Bash(grep*)"
  - "Bash(find*)"
  - "Bash(cat*)"
  - "Bash(ls*)"

  # Agent Rulez hook management
  - "Bash(rulez*)"

  # Research tools (pre-authorized; wizard probes availability before use)
  - "WebSearch"
  - "WebFetch"
```

Entry count breakdown: Read, Glob, Grep (3) + Write×2, Edit×2 (4) + Bash×6 (6) + WebSearch, WebFetch (2) = **15 entries total**

- Write scoped to `.code-wizard/**` and `.claude/code-wizard/**` only — cannot write source files or config outside wizard dirs
- Bash limited to safe prefixes: `node*`, `grep*`, `find*`, `cat*`, `ls*`, `rulez*`
- No destructive bash — wizard never deletes anything (`rm`, `mv`, `pkill`, `chmod`, `sudo` are intentionally absent)
- WebSearch/WebFetch pre-authorized at plugin-install time, not session time; wizard gates their use behind an availability probe before invoking

### Main Wizard Command (codebase-wizard.md)

```yaml
---
context: fork
agent: codebase-wizard-agent
---
```

- `context: fork` — forks into a new context; policy island applies for entire session
- `agent: codebase-wizard-agent` — all tool access delegated to the policy island
- Args: `--describe | --explore | --file <path>` (no args → wizard asks which mode)
- Mode routing: `--describe` loads `references/describe-questions.md`; `--explore` loads `references/explore-questions.md`; `--file <path>` reads file and parses heading structure
- Drives `SKILL.md` wizard logic — entry point only; SKILL.md handles answer loop, research priority, session stack

### Command Files from Phase 2 (already created)

- `codebase-wizard-export.md` — `context: fork`, `agent: codebase-wizard-agent`; synthesizes raw JSON → docs on demand
- `codebase-wizard-setup.md` — **NO `context: fork`** (runs in main context intentionally); needs main-context permissions to write `settings.local.json` and install Agent Rulez
- Phase 3 wires these to the agent; the file content was created in Phase 2. Phase 3 verifies agent wiring is correct and files exist unmodified.

### codex-tools.md Tool Mapping

All 8 tool pairs across all 4 platforms:

| Claude Code | OpenCode | Gemini CLI | Codex |
|---|---|---|---|
| `Read` | `read` | `read_file` | `read_file` |
| `Write` | `write` | `write_file` | `write_file` |
| `Edit` | `edit` | `replace` | `replace` |
| `Bash` | `bash` | `run_shell_command` | `shell` |
| `Grep` | `grep` | `search_file_content` | `search_file_content` |
| `Glob` | `glob` | `glob` | `list_files` |
| `WebSearch` | `websearch` | `google_web_search` | `web_search` |
| `WebFetch` | `webfetch` | `web_fetch` | `web_fetch` |

- File lives at `plugin/references/codex-tools.md` — lazy-loaded only on non-Claude Code runtimes
- Codex has no hook support — manual `/export` required — documented in `AGENTS.md`
- Detection: `setup.sh` writes `RUNTIME` value into `config.json` at install time; wizard reads it on startup

### Platform Detection in setup.sh

```bash
RUNTIME="${1:-claude}"

case "$RUNTIME" in
  claude)   install_claude   ;;   # copy plugin to ~/.claude/plugins/
  opencode) install_opencode ;;   # flatten names, lowercase tools
  gemini)   install_gemini   ;;   # convert to TOML, snake_case tools
  codex)    install_codex    ;;   # write AGENTS.md, skip hooks (exit 77)
  all)      install_all      ;;
esac
```

- `RUNTIME="${1:-claude}"` — reads from first arg, defaults to `claude`
- `install_codex`: prints manual-export notice, exits with code 77 (conventional "feature not supported on this platform, skip gracefully")
- `install_all`: calls all four platform functions using `|| true` so codex exit-77 does not abort the all-platforms run
- Claude Code install: copy plugin to `~/.claude/plugins/codebase-wizard`
- All 5 install functions must be defined (stubs acceptable for opencode and gemini initially)

### Platform Matrix

| Platform | Config Dir | Tool Casing | Install | Hook Support |
|---|---|---|---|---|
| Claude Code | `~/.claude/` | PascalCase | Plugin manifest | Yes (Agent Rulez) |
| OpenCode | `~/.config/opencode/` | lowercase | Flat command names | Yes |
| Gemini CLI | `~/.gemini/` | snake_case | TOML format | Yes |
| Codex | `~/.codex/` | See codex-tools.md | AGENTS.md | No |

### Per-Platform Config Files

- `CLAUDE.md` — skill invocation instructions, agent reference
- `GEMINI.md` — `activate_skill` mapping + tool equivalents auto-loaded at session start
- `AGENTS.md` — Codex instruction file; documents manual export step (no hooks)

### settings.local.json Written by setup.sh

```json
{
  "permissions": {
    "allow": [
      "Bash(rulez*)",
      "Bash(node .claude/plugins/codebase-wizard/**)",
      "Write(.code-wizard/**)",
      "Write(.claude/code-wizard/**)"
    ]
  }
}
```

### Plugin Delivery Path

Build skill → `/improving-skills` grade (target ≥70) → `/creating-plugin-from-skill` → `setup.sh` cross-platform

### Claude's Discretion

- Exact `install_opencode` and `install_gemini` implementations (stubs acceptable initially)
- `CLAUDE.md` / `GEMINI.md` / `AGENTS.md` exact content
- Whether to create per-platform config files in Phase 3 or defer to plugin publishing step

</decisions>

<specifics>
## Specific Ideas

- Policy island eliminates ALL "May I?" prompts during regular wizard sessions
- `/codebase-wizard-setup` runs ONCE during onboarding and never again
- The three commands form a complete user workflow: setup → wizard → export
- `codex-tools.md` lives in `plugin/references/` (lazy-loaded only on Codex or other non-Claude Code platforms)
- `setup.sh` exit code 77 is a convention meaning "feature not supported on this platform, skip gracefully"
- `install_all` uses `|| true` so the codex exit-77 doesn't abort the all-platforms run
- `codebase-wizard-setup.md` intentionally omits `context: fork` — it needs main-context permissions; this is the only command that does
- WebSearch/WebFetch permission decision is made at plugin install time (via `allowed_tools`), not at session time — wizard probes availability before use but does not prompt for permission
- Worst-case outcome of a compromised session: an unexpected file in `.code-wizard/` or `.claude/code-wizard/` — source files are safe
- Open question from spec: What `/improving-skills` score threshold is acceptable before publishing?

</specifics>

<canonical_refs>
## Canonical References

### Spec
- `docs/superpowers/specs/2026-03-19-codebase-wizard-design.md` §4 — Platform matrix, tool name mapping, command name conversion, setup script platform detection, per-platform config files
- `docs/superpowers/specs/2026-03-19-codebase-wizard-design.md` §5 — Policy island agent (full allowed_tools list), command frontmatter specs, settings.local.json written by setup

### Plan
- `docs/superpowers/plans/2026-03-19-codebase-wizard-plan3-permission-agents.md` — Step-by-step task execution plan with verification criteria for each deliverable

### Dependencies from Phase 1
- `plugin/SKILL.md` — Wizard logic driven by codebase-wizard-agent; answer loop, mode routing, session stack management
- `plugin/references/` — All reference files (chat-feel, scan-patterns, navigation, tutorial-mode, persistence, describe-questions, explore-questions)

### Dependencies from Phase 2
- `plugin/commands/codebase-wizard-export.md` — Already created; Phase 3 verifies agent wiring (`context: fork`, `agent: codebase-wizard-agent`)
- `plugin/commands/codebase-wizard-setup.md` — Already created; Phase 3 verifies no `context: fork` (intentional — runs in main context)
- `plugin/setup/setup.sh` — Created in Phase 2 with Agent Rulez install logic, storage resolution, and `settings.local.json` writing; extended in Phase 3 with platform detection
- `plugin/setup/agent-rulez-sample.yaml` — Hook config template; `setup.sh` substitutes `{resolved_storage}` when deploying

### External
- Claude Code plugin manifest format — `~/.claude/plugins/` install structure
- Agent Rulez: https://github.com/SpillwaveSolutions/agent_rulez — PostToolUse/Stop hook mechanism; `rulez` CLI

</canonical_refs>

<deferred>
## Deferred Ideas

- Full `install_opencode` / `install_gemini` implementations (stubs acceptable in Phase 3)
- `/improving-skills` grading run — happens after Phase 3 as part of plugin delivery path
- `/creating-plugin-from-skill` — final publishing step, after grading
- Per-platform config files (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`) exact content — may defer to plugin publishing step
- Export `--format pdf` — v2
- Real-time multi-user sessions — out of scope
- Cloud sync — out of scope
- `--file` mode support for non-markdown files (JSON schemas, OpenAPI specs) — defer to v2
- Automatic git commits of generated docs — out of scope
- Merging sessions from different dates into a single output document — out of scope

</deferred>

---

*Phase: 03-permission-agents-commands*
*Context gathered: 2026-03-19*
