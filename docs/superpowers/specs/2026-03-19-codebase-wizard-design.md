# Codebase Wizard — Design Spec

**Date:** 2026-03-19
**Status:** Approved
**Project:** codebase-mentor / Codebase Wizard Plugin

---

## Overview

The Codebase Wizard is a universal explainer skill and Claude Code plugin. It accepts any artifact — codebase, markdown spec, design doc, milestone plan — and explains it through a wizard-style Q&A conversation. Every answer is anchored to actual code or document content shown inline. All conversations are auto-captured and exportable as structured documentation.

**Core value:** A developer runs one command and walks away with a documented, navigable understanding of what they're looking at — without clicking "Approve" repeatedly or writing documentation by hand.

**Delivery path:** Skill → graded by `/improving-skills` → converted to plugin by `/creating-plugin-from-skill` → cross-platform install via `setup.sh`.

---

## Section 1: Architecture

### File Layout

```
plugin/
├── SKILL.md                          # Wizard logic + mode routing
│                                     # (question logic lives in references/)
├── agents/
│   └── codebase-wizard-agent.md     # Policy island — all pre-authorized tools
├── commands/
│   ├── codebase-wizard.md           # context: fork, agent: codebase-wizard-agent
│   ├── codebase-wizard-export.md    # Synthesize raw JSON → docs on demand
│   └── codebase-wizard-setup.md    # Install Agent Rulez + write permissions
├── setup/
│   ├── setup.sh                     # Agent Rulez install + settings.local.json writer
│   └── agent-rulez-sample.yaml     # PostToolUse/Stop capture hook config TEMPLATE
└── references/
    ├── chat-feel.md                 # (existing) tone/formatting rules
    ├── scan-patterns.md             # (existing) repo scanning heuristics
    ├── navigation-commands.md       # (existing) session navigation
    ├── tutorial-mode.md             # (existing) tutorial walkthrough
    ├── persistence.md               # (existing) save/load sessions
    ├── describe-questions.md        # NEW: question bank for Describe mode
    │                                # SKILL.md loads this when --describe activates
    ├── explore-questions.md         # NEW: question bank for Explore mode
    │                                # SKILL.md loads this when --explore activates
    └── codex-tools.md               # NEW: tool name equivalents for Codex
```

**SKILL.md vs. reference files boundary:**
- `SKILL.md` contains: mode detection, the answer loop, research tool priority, session stack management, and calls to load reference files on-demand
- `references/describe-questions.md` contains: the ordered question bank, follow-up decision logic, and output schema for Describe mode
- `references/explore-questions.md` contains: the learning-order tour structure and follow-up logic for Explore mode
- Reference files are loaded lazily — only when their mode activates — following the same pattern as the existing skill

### Data Flow

```
User runs /codebase-wizard [--describe | --explore | --file <path>]
  → forks into codebase-wizard-agent (policy island)
  → SKILL.md drives wizard conversation
  → Agent Rulez PostToolUse hook fires on each turn
       → appends Q&A to {resolved_storage}/sessions/YYYY-MM-DD-{repo}.json
       # {resolved_storage} is read from {resolved_storage}/config.json at hook init
  → session ends naturally or user says "done"
  → Agent Rulez Stop hook fires
       → reminds user to /codebase-wizard-export

User runs /codebase-wizard-export [--session <filename> | --latest | --all]
  → reads config.json to find resolved_storage
  → reads specified session(s) from {resolved_storage}/sessions/
  → synthesizes → SESSION-TRANSCRIPT.md + CODEBASE.md or TOUR.md or FILE-NOTES.md
  → writes to {resolved_storage}/docs/{session_id}/
```

### Storage Resolution

On first run (during `/codebase-wizard-setup`), resolved once and stored in `{storage}/config.json`:

```
1. .code-wizard/           exists? → use it
2. .claude/code-wizard/    exists? → use it
3. Neither → ask user once → create chosen directory → write config.json
```

**`config.json` format:**
```json
{
  "version": 1,
  "resolved_storage": ".code-wizard",
  "created": "2026-03-19T14:00:00Z"
}
```

Always check both locations on read. Write only to resolved location.

**Agent Rulez hook path resolution:** The setup script writes the resolved storage path into the deployed `agent-rulez.yaml` (not the sample template). The `agent-rulez-sample.yaml` uses `{resolved_storage}` as a placeholder; `setup.sh` substitutes the actual path when copying it into place.

---

## Section 2: The Explainer

### Universal Artifact Support

The wizard accepts any artifact as its subject:

| Artifact | What the explainer does | Output doc |
|---|---|---|
| Codebase / source file | Scans, traces call chains, shows code blocks with LOC | `CODEBASE.md` |
| Markdown spec / PRD | Parses sections, explains each, asks follow-ups | `FILE-NOTES.md` |
| Milestone / roadmap doc | Walks through phases, explains deliverables | `FILE-NOTES.md` |
| Design doc | Explains decisions, surfaces trade-offs | `FILE-NOTES.md` |
| New developer tour | Guides in learning order, interactive navigation | `TOUR.md` |

The artifact type is detected automatically. If passed a `.md` file, the wizard parses its structure. If pointed at a directory, it scans for entry points.

### The Answer Loop (Every Response)

Every single answer follows this pattern without exception:

```
1. Find the relevant artifact (code, section, passage)
2. Show it as a code block with full anchor:
      // src/auth/middleware.ts → AuthMiddleware → validate() → L14-31
3. Explain in plain English (1 short paragraph, no undefined jargon)
4. Show connections (code mode only):
      → calls:     src/services/token.ts → TokenService → verify()
      → called by: src/routes/api.ts → router.use() → L8
5. Predict next (2-3 follow-up options)
```

The user never guesses where something lives. The code block is always the anchor. Explanation always follows the code.

### Two Modes + File Mode

**Describe mode** (`--describe`) — repo owner documents their codebase:
- Loads `references/describe-questions.md`
- Scans repo first (reuses `scan-patterns.md` logic)
- Asks questions for context Claude cannot infer: ownership, intent, constraints, domain terms, missing pieces
- One question at a time — not a form dump
- Output: `CODEBASE.md` with sections (Overview, Entry Points, Auth, Data Layer, Key Concepts, Constraints)

**Explore mode** (`--explore`) — new developer getting a tour:
- Loads `references/explore-questions.md`
- Same scan, then guides through in learning order (not file order):
  1. What the app does
  2. Where it starts
  3. How auth works
  4. How data flows
  5. Where to make a first change
- User can ask follow-ups, take detours, or say "next"
- Navigation commands from `navigation-commands.md` work throughout
- Output: `TOUR.md` — re-readable learning document

**File mode** (`--file <path>`) — explain any markdown artifact:
- Works with any `.md` file (spec, roadmap, design, milestone plan)
- Parses heading structure into sections
- Walks through each section: shows the section content, explains it, asks follow-up questions
- User says "next" to advance or asks questions to dig deeper
- Output: `FILE-NOTES.md` — section-by-section explanation with follow-up Q&A captured

### Research Adaptability

The wizard uses available tools, checked in order:

```
1. Agent Brain (if installed + indexed) → semantic search over codebase
2. Perplexity (if available)           → external context, library docs
3. Codebase scan                       → grep, glob, file reads
4. Markdown parse                      → heading structure, section extraction
```

**Availability check:** Before using Agent Brain or Perplexity, the wizard attempts a lightweight probe (e.g., `which agent-brain` or a minimal API call). If the probe fails, it falls back to the next tier silently. It only surfaces the unavailability to the user when the question genuinely requires external context that the fallback cannot provide:
> "I can answer this better with Agent Brain — want me to set it up? Or I can scan the codebase directly."

---

## Section 3: Capture + Synthesis

### Agent Rulez Hook Config

`setup/agent-rulez-sample.yaml` is a **template**. `setup.sh` substitutes `{resolved_storage}` with the actual path when deploying:

```yaml
# Deployed to: {resolved_storage}/agent-rulez.yaml
# Generated by: /codebase-wizard-setup
hooks:
  - event: PostToolUse
    action: append
    target: ".code-wizard/sessions/{date}-{repo}.json"
    # {date} and {repo} are Agent Rulez native interpolation variables:
    # {date} → YYYY-MM-DD at hook invocation time
    # {repo} → basename of the current working directory
    format: json
    on_error: warn
    # on_error: warn means capture failures notify the user but do not abort the session

  - event: Stop
    action: notify
    message: "Session ended. Run /codebase-wizard-export to generate docs."
```

**Note on `{date}` and `{repo}`:** These are Agent Rulez native template variables, confirmed in the Agent Rulez documentation. `{date}` is the ISO date at invocation time; `{repo}` is the current directory basename. If Agent Rulez does not support these natively, `setup.sh` pre-computes them and writes a static path into the deployed YAML.

**Hook error handling:** If the PostToolUse hook fails (disk full, permission error, storage not yet initialized), Agent Rulez is configured with `on_error: warn`. The session continues uninterrupted; a warning is shown in the console. Sessions are not lost — the wizard maintains an in-memory buffer and offers to flush it at the end if hooks failed.

### Raw Session Format

**`{resolved_storage}/sessions/YYYY-MM-DD-{repo}.json`:**

```json
{
  "version": 1,
  "session_id": "2026-03-19-codebase-mentor",
  "repo": "codebase-mentor",
  "artifact": "plugin/SKILL.md",
  "mode": "explore",
  "created": "2026-03-19T14:00:00Z",
  "turns": [
    {
      "ts": "2026-03-19T14:22:01Z",
      "question": "How does the session stack work?",
      "anchor": "plugin/SKILL.md → Phase 3 → Session Stack Format → L164",
      "code_shown": "session: {\n  repo: ...\n  history: [...]\n  current: 2\n}",
      "explanation": "The stack is a JSON object maintained in working memory...",
      "connections": {
        "calls": [],
        "called_by": ["Phase 2 answer handler"]
      },
      "next_options": [
        "How does rewind work?",
        "What happens when the stack hits 20 entries?",
        "Show me the bookmark format"
      ]
    }
  ]
}
```

The `version` field allows the export command to detect and handle sessions written by older plugin versions.

### Synthesis (`/codebase-wizard-export`)

**Args:** `--session <filename>` | `--latest` (default) | `--all`

- `--latest`: synthesizes the most recent session file in `{resolved_storage}/sessions/`
- `--session <filename>`: synthesizes a specific session file
- `--all`: synthesizes all sessions — each gets its own output directory; no merging across sessions

Output always goes to `{resolved_storage}/docs/{session_id}/`. Each session produces its own subdirectory, preventing overwrites between sessions.

**Three output documents (always generated from every session):**

**`SESSION-TRANSCRIPT.md`** (always — every mode):
- Full Q&A in order with code blocks and anchors
- Preserves the exact conversational flow

**`CODEBASE.md`** (Describe mode sessions):
```markdown
# Codebase: {repo}
## Overview
## Entry Points
## Auth
## Data Layer
## Key Concepts (from Q&A)
## Traced Call Chains
## Constraints
## Open Questions
```

**`TOUR.md`** (Explore mode sessions):
- Conversational flow formatted as a re-readable learning guide

**`FILE-NOTES.md`** (File mode sessions):
- Section-by-section breakdown of the explained artifact with captured Q&A

---

## Section 4: Multi-Platform Support

### Platform Matrix

| Platform | Config Dir | Tool Casing | Install | Hook Support |
|---|---|---|---|---|
| Claude Code | `~/.claude/` | PascalCase | Plugin manifest | Yes (Agent Rulez) |
| OpenCode | `~/.config/opencode/` | lowercase | Flat command names | Yes |
| Gemini CLI | `~/.gemini/` | snake_case | TOML format | Yes |
| Codex | `~/.codex/` | See codex-tools.md | AGENTS.md | No |

**Codex and hooks:** Codex has no hook mechanism. When installed for Codex, `setup.sh` skips Agent Rulez configuration entirely (exits the hook setup step with code 77, the conventional "skip" exit for unsupported scenarios). Codex users must run `/codebase-wizard-export` manually at the end of each session. `AGENTS.md` documents this manual step.

### Tool Name Mapping

| Claude Code | OpenCode | Gemini CLI |
|---|---|---|
| `Read` | `read` | `read_file` |
| `Write` | `write` | `write_file` |
| `Edit` | `edit` | `replace` |
| `Bash` | `bash` | `run_shell_command` |
| `Grep` | `grep` | `search_file_content` |
| `Glob` | `glob` | `glob` |
| `WebSearch` | `websearch` | `google_web_search` |
| `WebFetch` | `webfetch` | `web_fetch` |

Codex equivalents documented in `references/codex-tools.md`.

### Command Name Conversion

| Claude Code | OpenCode | Gemini |
|---|---|---|
| `/codebase-wizard` | `/codebase-wizard` | TOML file |
| `/codebase-wizard-export` | `/codebase-wizard-export` | TOML file |
| `/codebase-wizard-setup` | `/codebase-wizard-setup` | TOML file |

### Setup Script Platform Detection (`setup/setup.sh`)

```bash
case "$RUNTIME" in
  claude)   install_claude   ;;   # copy plugin to ~/.claude/plugins/
  opencode) install_opencode ;;   # flatten names, lowercase tools
  gemini)   install_gemini   ;;   # convert to TOML, snake_case tools
  codex)    install_codex    ;;   # write AGENTS.md, skip hooks (exit 77)
  all)      install_all      ;;
esac
```

### Per-Platform Config Files

- **`CLAUDE.md`** — skill invocation instructions, agent reference
- **`GEMINI.md`** — `activate_skill` mapping + tool equivalents auto-loaded at session start
- **`AGENTS.md`** — Codex instruction file; documents manual export step (no hooks)

### Plugin Delivery Path

```
1. Build skill (SKILL.md + references + agents + commands)
2. /improving-skills → grade → iterate until acceptable score
3. /creating-plugin-from-skill → publish for Claude Code
4. setup.sh --runtime opencode|gemini|codex → cross-platform
```

---

## Section 5: Permission Agents + Commands

### Policy Island (`agents/codebase-wizard-agent.md`)

```yaml
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
```

**Security choices:**
- `Write` scoped to `.code-wizard/**` only — cannot modify source files or config outside wizard dirs
- No destructive bash (`rm`, `pkill`, etc.) — wizard never deletes anything
- `WebSearch` / `WebFetch` in `allowed_tools` means they never prompt; the wizard gates their use behind an availability probe, not a permission prompt. This is intentional: the permission decision was made at plugin install time, not session time.

### Commands

**`commands/codebase-wizard.md`:**
```yaml
---
context: fork
agent: codebase-wizard-agent
---
Run the Codebase Wizard.
Args: --describe | --explore | --file <path>
Invoke SKILL.md wizard logic with the appropriate mode.
```

**`commands/codebase-wizard-export.md`:**
```yaml
---
context: fork
agent: codebase-wizard-agent
---
Args: --latest (default) | --session <filename> | --all
Read config.json to find resolved_storage.
Read session JSON from {resolved_storage}/sessions/.
Synthesize: SESSION-TRANSCRIPT.md + CODEBASE.md or TOUR.md or FILE-NOTES.md.
Write to {resolved_storage}/docs/{session_id}/.
```

**`commands/codebase-wizard-setup.md`:**
```yaml
---
# No context: fork — setup runs in the main context intentionally.
# Reason: setup needs to write settings.local.json and install Agent Rulez,
# which requires permissions outside the scoped wizard agent.
# This command runs ONCE during onboarding; it is not used in regular sessions.
---
Run setup/setup.sh:
1. Ask user: .code-wizard/ or .claude/code-wizard/?
2. Create chosen directory, write config.json with resolved_storage
3. Install Agent Rulez (rulez install)
4. Copy agent-rulez-sample.yaml → {resolved_storage}/agent-rulez.yaml
   substituting {resolved_storage} with actual path
5. Register hook: rulez hook add --config {resolved_storage}/agent-rulez.yaml
6. Write settings.local.json with scoped permissions
```

### `settings.local.json` Written by Setup

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

---

## Non-Goals

- Real-time collaboration / multi-user sessions
- Cloud sync of captured sessions (local-only)
- IDE integrations (Claude Code CLI only for v1)
- Automatic git commits of generated docs
- Merging sessions from different dates into a single output document

---

## Open Questions

| Question | Impact |
|---|---|
| Does Agent Rulez support `{date}` and `{repo}` as native interpolation variables? | Determines whether setup.sh must pre-compute static paths |
| Should `--file` mode support non-markdown files (JSON schemas, OpenAPI specs)? | Scope of Section 2 — defer to v2 unless trivial |
| Should export offer `--format pdf` via the `pdf` skill? | Nice-to-have for v2 |
| What is the acceptable `/improving-skills` score threshold before publishing? | Plugin delivery path gate |
