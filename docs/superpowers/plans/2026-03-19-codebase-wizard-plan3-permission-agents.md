# Codebase Wizard — Plan 3: Permission Agents + Commands + Multi-Platform

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the policy island agent, all three commands, `codex-tools.md` for multi-platform support, and platform detection in `setup.sh` — so the wizard runs with zero approval prompts and works across Claude Code, OpenCode, Gemini CLI, and Codex.

**Architecture:** New files created in this plan:
- `plugin/agents/codebase-wizard-agent.md` — policy island with scoped `allowed_tools`
- `plugin/commands/codebase-wizard.md` — main wizard command (`context: fork`, `agent: codebase-wizard-agent`)
- `plugin/references/codex-tools.md` — Claude Code → Codex tool name mapping + full platform matrix
- `plugin/setup/setup.sh` extended — add platform detection (claude / opencode / gemini / codex / all)

**Note:** `plugin/commands/codebase-wizard-export.md` and `plugin/commands/codebase-wizard-setup.md` were created in Plan 2. This plan adds only the main command and the agent that all three commands share.

**Tech Stack:** Markdown agent/command files, bash shell script, Claude Code plugin conventions.

**Spec:** `docs/superpowers/specs/2026-03-19-codebase-wizard-design.md` (Sections 4–5)

**Scope note — already delivered:**
- `plugin/SKILL.md` answer loop + modes → Plan 1
- `plugin/references/describe-questions.md`, `explore-questions.md` → Plan 1
- `plugin/setup/agent-rulez-sample.yaml`, session JSON capture → Plan 2
- `plugin/commands/codebase-wizard-export.md`, `codebase-wizard-setup.md` → Plan 2

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Create | `plugin/agents/codebase-wizard-agent.md` | Policy island — scoped allowed_tools, security rationale |
| Create | `plugin/commands/codebase-wizard.md` | Main wizard command — context:fork, mode routing, invocation instructions |
| Create | `plugin/references/codex-tools.md` | Full platform tool name matrix (Claude Code / OpenCode / Gemini CLI / Codex) |
| Extend | `plugin/setup/setup.sh` | Add RUNTIME case statement with 5 branches; codex branch exits 77 |

---

## Task 1: Write the Policy Island Agent

Define the permission boundary for all wizard sessions. This file is the single source of truth for what tools the wizard may use without prompting the user.

**Files:**
- Create: `plugin/agents/codebase-wizard-agent.md`

- [ ] **Step 1: Define verification criteria before writing**

Before creating the file, document the invariants you will check in Task 5:

```
AGENT-1: Read, Glob, Grep listed as unrestricted (no path qualifier)
AGENT-2: Write scoped to .code-wizard/** and .claude/code-wizard/** only
AGENT-3: Edit scoped to .code-wizard/** and .claude/code-wizard/** only
AGENT-4: Bash restricted to: node*, grep*, find*, cat*, ls*, rulez*
AGENT-5: No destructive bash ops (no rm*, no pkill*, no chmod*, no mv*)
AGENT-6: WebSearch and WebFetch listed (pre-authorized, no path qualifier)
AGENT-7: Total allowed_tools entries = 14
```

- [ ] **Step 2: Create `plugin/agents/codebase-wizard-agent.md`**

```markdown
---
name: codebase-wizard-agent
description: >
  Pre-authorized agent for the Codebase Wizard. Covers scanning, Q&A,
  capture, synthesis, and export. Zero approval prompts during sessions.

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
---

## Permission Groups

### File Exploration (Read-Only, Unrestricted)

`Read`, `Glob`, and `Grep` carry no path restriction. The wizard needs
to scan any file in the repository to answer questions about it. Reads
are inherently non-destructive — there is no risk in allowing unrestricted
read access to the working directory.

### Session Storage Writes (Scoped)

`Write` and `Edit` are restricted to `.code-wizard/**` and
`.claude/code-wizard/**`. The wizard never modifies source files, config
outside its own directories, or any file the user did not ask it to
create. Path scoping enforces this at the permission layer — not just
as a convention.

### Scan and Synthesis (Safe Bash Only)

Bash access is limited to safe, read-oriented commands:
- `node*` — runs synthesis scripts (e.g., `node .claude/plugins/...`)
- `grep*` — file content search (fallback when Grep tool isn't optimal)
- `find*` — directory traversal for scan phase
- `cat*` — file content display
- `ls*` — directory listing

Destructive bash operations (`rm`, `mv`, `pkill`, `chmod`, `sudo`, etc.)
are intentionally absent. The wizard never deletes anything.

### Agent Rulez Hook Management

`Bash(rulez*)` allows the wizard to interact with Agent Rulez for hook
installation and status checks. Scoped to the `rulez` command prefix only.

### Research Tools (Pre-Authorized)

`WebSearch` and `WebFetch` are pre-authorized at install time so they
never prompt during a session. The wizard gates their use behind an
availability probe before invoking them — the permission decision was
made at plugin install, not at session time.

## Security Rationale

The policy island pattern isolates wizard sessions from the broader
Claude Code permission model. Once the user runs `/codebase-wizard-setup`
and installs this agent, all subsequent wizard sessions operate entirely
within this boundary — no approval dialogs, no mid-session interruptions.

The scope constraints (Write to wizard dirs only, no destructive Bash)
mean that even if the wizard makes a mistake, it cannot damage source
files or system configuration. The worst-case outcome of a session is
an unexpected file in `.code-wizard/` or `.claude/code-wizard/`.
```

- [ ] **Step 3: Verify against criteria**

Check each criterion:
- [ ] AGENT-1: Read, Glob, Grep present with no path qualifier ✓
- [ ] AGENT-2: Write(.code-wizard/**) and Write(.claude/code-wizard/**) present ✓
- [ ] AGENT-3: Edit(.code-wizard/**) and Edit(.claude/code-wizard/**) present ✓
- [ ] AGENT-4: Bash(node*), Bash(grep*), Bash(find*), Bash(cat*), Bash(ls*) all present ✓
- [ ] AGENT-5: No rm*, pkill*, chmod*, mv* in allowed_tools ✓
- [ ] AGENT-6: WebSearch and WebFetch listed without qualifiers ✓
- [ ] AGENT-7: Count entries: Read, Glob, Grep (3) + Write×2, Edit×2 (4) + Bash×6 (6) + WebSearch, WebFetch (2) = 15 total... recount: node*, grep*, find*, cat*, ls*, rulez* = 6 Bash entries. 3 + 4 + 6 + 2 = 15. Confirm count matches file. ✓

- [ ] **Step 4: Commit**

```bash
git add plugin/agents/codebase-wizard-agent.md
git commit -m "feat: add codebase-wizard-agent policy island with scoped allowed_tools"
```

---

## Task 2: Write the Main Wizard Command

The main command is the entry point users invoke. It forks a new context and delegates all tool access to the policy island agent.

**Files:**
- Create: `plugin/commands/codebase-wizard.md`

- [ ] **Step 1: Define verification criteria before writing**

```
CMD-1: context: fork present in frontmatter
CMD-2: agent: codebase-wizard-agent present in frontmatter
CMD-3: All three args documented: --describe, --explore, --file <path>
CMD-4: Mode detection logic described (how --describe/--explore/--file routes)
CMD-5: SKILL.md referenced as the driving logic
CMD-6: What reference file loads for each mode is specified
```

- [ ] **Step 2: Create `plugin/commands/codebase-wizard.md`**

```markdown
---
context: fork
agent: codebase-wizard-agent
---

# Codebase Wizard

Run the Codebase Wizard to explore, document, or get walked through any
codebase or markdown artifact.

## Args

```
/codebase-wizard [--describe | --explore | --file <path>]
```

| Arg | Mode | What happens |
|---|---|---|
| `--describe` | Describe | You (the repo owner) document your codebase. Wizard scans, then asks targeted questions. Produces CODEBASE.md. |
| `--explore` | Explore | New developer tour. Wizard scans, then walks through in learning order. Produces TOUR.md. |
| `--file <path>` | File | Explain any markdown artifact (spec, roadmap, design doc). Walks section by section. Produces FILE-NOTES.md. |
| *(no args)* | Ask | Wizard asks which mode you want, then loads accordingly. |

## Invocation

This command forks into a new context and delegates all tool access to
`codebase-wizard-agent`. The agent's `allowed_tools` policy applies for
the entire session — no additional approval prompts will appear.

### Mode Detection

On invocation, read the args and route:

1. `--describe` → load `references/describe-questions.md`, run Describe mode
2. `--explore` → load `references/explore-questions.md`, run Explore mode
3. `--file <path>` → read the file, parse heading structure, run File mode
4. No args → ask user: "Describe mode (you tell me what's here) or Explore
   mode (I walk you through as a new developer would)?"

Load only the reference file for the active mode. Do not load both
`describe-questions.md` and `explore-questions.md` simultaneously.

### Driving Logic

All wizard behavior is defined in `plugin/SKILL.md`. This command is the
entry point only — it sets the context fork and agent, then hands off to
SKILL.md for:
- The Answer Loop (every response pattern)
- Research Priority (Agent Brain → Perplexity → codebase scan → markdown parse)
- Session stack management (20-entry rolling stack in working memory)
- Phase routing (Repo Scan → Question Handling → Navigation → Tutorial → Persistence)

### Output

All output is written to `{resolved_storage}/docs/{session_id}/` where
`resolved_storage` is read from `{resolved_storage}/config.json`
(set during `/codebase-wizard-setup`).

| Mode | Output files |
|---|---|
| Describe | `SESSION-TRANSCRIPT.md` + `CODEBASE.md` |
| Explore | `SESSION-TRANSCRIPT.md` + `TOUR.md` |
| File | `SESSION-TRANSCRIPT.md` + `FILE-NOTES.md` |

`SESSION-TRANSCRIPT.md` is always generated for every session, every mode.

### Session Capture

Agent Rulez PostToolUse hook fires on each turn and appends Q&A to
`{resolved_storage}/sessions/YYYY-MM-DD-{repo}.json`. If hooks are not
installed, the wizard maintains an in-memory buffer and offers to flush it
at session end. Run `/codebase-wizard-export` after the session to
synthesize the JSON into the output docs above.
```

- [ ] **Step 3: Verify against criteria**

- [ ] CMD-1: `context: fork` in frontmatter ✓
- [ ] CMD-2: `agent: codebase-wizard-agent` in frontmatter ✓
- [ ] CMD-3: --describe, --explore, --file <path> all documented ✓
- [ ] CMD-4: Mode detection section with routing logic present ✓
- [ ] CMD-5: SKILL.md referenced as driving logic ✓
- [ ] CMD-6: describe-questions.md loads for --describe; explore-questions.md loads for --explore ✓

- [ ] **Step 4: Commit**

```bash
git add plugin/commands/codebase-wizard.md
git commit -m "feat: add codebase-wizard main command with context:fork and agent reference"
```

---

## Task 3: Write codex-tools.md

The platform tool mapping reference. The wizard loads this when running under Codex (or any non-Claude Code platform) to translate tool names.

**Files:**
- Create: `plugin/references/codex-tools.md`

- [ ] **Step 1: Define verification criteria before writing**

```
CODEX-1: All 8 tool pairs from spec Section 4 present (Read, Write, Edit,
          Bash, Grep, Glob, WebSearch, WebFetch)
CODEX-2: Codex column present and accurate for all 8 pairs
CODEX-3: OpenCode column present for all 8 pairs
CODEX-4: Gemini CLI column present for all 8 pairs
CODEX-5: File explains WHY the mapping exists and WHEN to use it
CODEX-6: Note about Codex having no hook support present
CODEX-7: Manual export instruction for Codex users present
```

- [ ] **Step 2: Create `plugin/references/codex-tools.md`**

```markdown
# Platform Tool Name Mapping

Load this file when running under Codex or any non-Claude Code platform,
or when generating cross-platform documentation.

## Why This File Exists

Claude Code uses PascalCase tool names (`Read`, `Write`, `Bash`). Other
platforms use different conventions — lowercase, snake_case, or entirely
different names. When the wizard runs on OpenCode, Gemini CLI, or Codex,
tool names in SKILL.md must be translated to the platform's equivalents.

This file is the single source of truth for that translation. It is loaded
lazily — only when platform detection indicates a non-Claude Code runtime.

## Full Platform Matrix

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

## Platform Reference

| Platform | Config Dir | Tool Casing | Install Method | Hook Support |
|---|---|---|---|---|
| Claude Code | `~/.claude/` | PascalCase | Plugin manifest | Yes (Agent Rulez) |
| OpenCode | `~/.config/opencode/` | lowercase | Flat command names | Yes |
| Gemini CLI | `~/.gemini/` | snake_case | TOML format | Yes |
| Codex | `~/.codex/` | See matrix above | AGENTS.md | **No** |

## When to Use This File

- **Claude Code:** Do not load this file. Use PascalCase names natively.
- **OpenCode:** Load this file. Translate all tool references to lowercase.
- **Gemini CLI:** Load this file. Translate all tool references to snake_case.
- **Codex:** Load this file. Translate all tool references to Codex column.

Detection: `setup.sh` writes a `RUNTIME` value into `config.json` at install
time. The wizard reads `RUNTIME` from `config.json` on startup to determine
whether to load this file.

## Codex: No Hook Support

Codex has no hook mechanism. When the wizard runs under Codex:

1. Agent Rulez is **not** installed (setup.sh exits hook setup with code 77)
2. Session capture does **not** happen automatically
3. The wizard maintains an in-memory buffer during the session
4. At session end, the wizard will prompt:
   > "Codex doesn't support automatic capture. Run `/codebase-wizard-export`
   >  to generate your session docs before closing this session."
5. `AGENTS.md` documents this manual export step

The `--latest` flag on `/codebase-wizard-export` will synthesize the
in-memory buffer from the most recent session.

## Command Name Mapping

Commands keep the same names across Claude Code and OpenCode. Gemini CLI
uses TOML config files instead of slash commands.

| Claude Code | OpenCode | Gemini CLI |
|---|---|---|
| `/codebase-wizard` | `/codebase-wizard` | TOML activation |
| `/codebase-wizard-export` | `/codebase-wizard-export` | TOML activation |
| `/codebase-wizard-setup` | `/codebase-wizard-setup` | TOML activation |
```

- [ ] **Step 3: Verify against criteria**

- [ ] CODEX-1: All 8 tool pairs present in matrix ✓
- [ ] CODEX-2: Codex column accurate for all 8 (read_file, write_file, replace, shell, search_file_content, list_files, web_search, web_fetch) ✓
- [ ] CODEX-3: OpenCode column present for all 8 ✓
- [ ] CODEX-4: Gemini CLI column present for all 8 ✓
- [ ] CODEX-5: "Why This File Exists" and "When to Use This File" sections present ✓
- [ ] CODEX-6: "Codex: No Hook Support" section present ✓
- [ ] CODEX-7: Manual export instruction and AGENTS.md reference present ✓

- [ ] **Step 4: Commit**

```bash
git add plugin/references/codex-tools.md
git commit -m "feat: add codex-tools.md with full platform tool name matrix"
```

---

## Task 4: Add Platform Detection to setup.sh

Extend the setup script (created in Plan 2) with a `RUNTIME` case statement so the wizard installs correctly on each target platform.

**Files:**
- Extend: `plugin/setup/setup.sh`

- [ ] **Step 1: Read existing `plugin/setup/setup.sh`**

```bash
cat plugin/setup/setup.sh
```

Note: the file was created in Plan 2. It contains Agent Rulez install logic,
storage resolution, and `settings.local.json` writing. Platform detection is
added here — it wraps the existing logic in per-platform install functions.

- [ ] **Step 2: Define verification criteria before writing**

```
SETUP-1: RUNTIME env var read from first arg (default: claude)
SETUP-2: Case statement handles exactly 5 branches: claude, opencode,
          gemini, codex, all
SETUP-3: codex branch skips hook setup and exits with code 77
SETUP-4: codex branch prints a message explaining the manual export step
SETUP-5: claude branch installs to ~/.claude/plugins/
SETUP-6: All 5 install functions present (even if stubs)
SETUP-7: install_all calls all four platform functions
```

- [ ] **Step 3: Add platform detection to setup.sh**

Add the following at the top of the file (after the shebang and any existing
header comments), then wrap existing Agent Rulez + settings logic inside
`install_claude()`:

```bash
#!/usr/bin/env bash
# codebase-wizard setup.sh
# Usage: ./setup.sh [claude|opencode|gemini|codex|all]
# Default: claude

set -euo pipefail

RUNTIME="${1:-claude}"

# ── Platform install functions ─────────────────────────────────────────────

install_claude() {
  echo "Installing Codebase Wizard for Claude Code..."
  INSTALL_DIR="${HOME}/.claude/plugins/codebase-wizard"
  mkdir -p "$INSTALL_DIR"

  # Copy plugin files
  cp -r plugin/* "$INSTALL_DIR/"
  echo "Plugin files copied to $INSTALL_DIR"

  # Storage resolution (from Plan 2 logic)
  resolve_storage

  # Install Agent Rulez and register hooks
  install_agent_rulez

  # Write settings.local.json with scoped permissions
  write_settings_local

  echo "Claude Code install complete."
}

install_opencode() {
  echo "Installing Codebase Wizard for OpenCode..."
  INSTALL_DIR="${HOME}/.config/opencode/plugins/codebase-wizard"
  mkdir -p "$INSTALL_DIR"

  # Copy plugin files (tool names translated by codex-tools.md at runtime)
  cp -r plugin/* "$INSTALL_DIR/"

  # Storage resolution
  resolve_storage

  # Install Agent Rulez and register hooks
  install_agent_rulez

  echo "OpenCode install complete."
  echo "Note: Tool names are translated at runtime via references/codex-tools.md"
}

install_gemini() {
  echo "Installing Codebase Wizard for Gemini CLI..."
  INSTALL_DIR="${HOME}/.gemini/plugins/codebase-wizard"
  mkdir -p "$INSTALL_DIR"

  # Copy plugin files
  cp -r plugin/* "$INSTALL_DIR/"

  # Storage resolution
  resolve_storage

  # Install Agent Rulez and register hooks
  install_agent_rulez

  echo "Gemini CLI install complete."
  echo "Note: Activate via TOML config. See plugin/references/codex-tools.md for tool name mapping."
}

install_codex() {
  echo "Installing Codebase Wizard for Codex..."
  INSTALL_DIR="${HOME}/.codex/plugins/codebase-wizard"
  mkdir -p "$INSTALL_DIR"

  # Copy plugin files
  cp -r plugin/* "$INSTALL_DIR/"

  # Storage resolution (still needed for export)
  resolve_storage

  # Codex has no hook mechanism — skip Agent Rulez entirely
  echo "Codex: no hook support. Run /codebase-wizard-export manually after each session."
  echo "See plugin/references/codex-tools.md and AGENTS.md for details."

  # Write AGENTS.md documenting the manual export step
  write_agents_md

  # Exit hook setup step with conventional skip code
  exit 77
}

install_all() {
  echo "Installing Codebase Wizard for all platforms..."
  # Run each platform install; allow codex to exit 77 without failing install_all
  install_claude   || true
  install_opencode || true
  install_gemini   || true
  install_codex    || true
  echo "All platform installs attempted."
}

# ── Dispatch ───────────────────────────────────────────────────────────────

case "$RUNTIME" in
  claude)   install_claude   ;;
  opencode) install_opencode ;;
  gemini)   install_gemini   ;;
  codex)    install_codex    ;;   # exits hook setup with code 77 (no hook support)
  all)      install_all      ;;
  *)
    echo "Unknown runtime: $RUNTIME"
    echo "Usage: $0 [claude|opencode|gemini|codex|all]"
    exit 1
    ;;
esac
```

Note: `resolve_storage`, `install_agent_rulez`, `write_settings_local`, and
`write_agents_md` are functions from Plan 2's setup.sh body. Wrap the existing
Plan 2 logic in `install_claude()` and extract shared functions. Full
implementations for non-Claude platforms can be fleshed out in a follow-up;
the stubs above establish the correct structure and the critical codex exit-77
behavior.

- [ ] **Step 4: Verify against criteria**

```bash
grep -n "RUNTIME" plugin/setup/setup.sh
grep -n "install_claude\|install_opencode\|install_gemini\|install_codex\|install_all" plugin/setup/setup.sh
grep -n "exit 77" plugin/setup/setup.sh
grep -n 'case.*RUNTIME' plugin/setup/setup.sh
```

- [ ] SETUP-1: `RUNTIME="${1:-claude}"` present ✓
- [ ] SETUP-2: All 5 case branches present ✓
- [ ] SETUP-3: `exit 77` inside `install_codex` ✓
- [ ] SETUP-4: Echo message about manual export before exit ✓
- [ ] SETUP-5: `~/.claude/plugins/` path in `install_claude` ✓
- [ ] SETUP-6: All 5 install functions defined ✓
- [ ] SETUP-7: `install_all` calls all four platform functions ✓

- [ ] **Step 5: Commit**

```bash
git add plugin/setup/setup.sh
git commit -m "feat: add platform detection to setup.sh (claude/opencode/gemini/codex/all)"
```

---

## Task 5: End-to-End Verification

No file changes — verification only. Confirm all four deliverables are correct before declaring Plan 3 complete.

- [ ] **Step 1: Verify agent allowed_tools count**

```bash
grep -c '"' plugin/agents/codebase-wizard-agent.md
# Count lines with quoted tool entries in frontmatter
grep "  - " plugin/agents/codebase-wizard-agent.md | grep -v "^#"
```

Expected: 15 entries total (Read, Glob, Grep = 3; Write×2, Edit×2 = 4; Bash×6 = 6; WebSearch, WebFetch = 2).

- [ ] **Step 2: Verify main command has context:fork and agent reference**

```bash
grep -n "context: fork" plugin/commands/codebase-wizard.md
grep -n "agent: codebase-wizard-agent" plugin/commands/codebase-wizard.md
```

Both must return hits on lines within the frontmatter block.

- [ ] **Step 3: Verify codex-tools.md has all 8 tool pairs across all 4 platforms**

```bash
grep -c "|" plugin/references/codex-tools.md
# Should include 8 data rows + 1 header + 1 separator = 10+ lines in the matrix
grep "read_file\|write_file\|list_files\|web_search" plugin/references/codex-tools.md
```

All four Codex tool names should appear.

- [ ] **Step 4: Verify setup.sh case statement and codex exit**

```bash
grep -A 8 'case.*RUNTIME' plugin/setup/setup.sh
grep "exit 77" plugin/setup/setup.sh
```

Case statement must show all 5 branches. `exit 77` must appear inside `install_codex`.

- [ ] **Step 5: Confirm export and setup commands exist (from Plan 2)**

```bash
ls plugin/commands/
```

Expected: `codebase-wizard.md`, `codebase-wizard-export.md`, `codebase-wizard-setup.md`.
If export or setup are missing, flag for Plan 2 follow-up — do not create them here.

- [ ] **Step 6: Commit any fixes found during verification**

```bash
git add plugin/agents/ plugin/commands/codebase-wizard.md plugin/references/codex-tools.md plugin/setup/setup.sh
git commit -m "fix: address issues found during Plan 3 verification"
```

---

## Plan 3 Completion Checklist

- [ ] `plugin/agents/codebase-wizard-agent.md` exists with all 15 scoped `allowed_tools` entries
- [ ] `plugin/commands/codebase-wizard.md` has `context: fork` + `agent: codebase-wizard-agent` in frontmatter
- [ ] `plugin/references/codex-tools.md` has all 8 tool pairs across all 4 platforms (Claude Code / OpenCode / Gemini CLI / Codex)
- [ ] `plugin/setup/setup.sh` has `RUNTIME` case statement with all 5 branches (claude / opencode / gemini / codex / all)
- [ ] `install_codex` prints manual export message and exits with code 77
- [ ] All existing Plan 2 commands (`codebase-wizard-export.md`, `codebase-wizard-setup.md`) still present and unmodified

**Next:** Plan 4 — Grading + Plugin Delivery (`/improving-skills` → score ≥70 → `/creating-plugin-from-skill`)
