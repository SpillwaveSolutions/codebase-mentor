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
├── SKILL.md                          # Wizard logic, mode routing, question banks
├── agents/
│   └── codebase-wizard-agent.md     # Policy island — all pre-authorized tools
├── commands/
│   ├── codebase-wizard.md           # context: fork, agent: codebase-wizard-agent
│   ├── codebase-wizard-export.md    # Synthesize raw JSON → docs on demand
│   └── codebase-wizard-setup.md    # Install Agent Rulez + write permissions
├── setup/
│   ├── setup.sh                     # Agent Rulez install + settings.local.json writer
│   └── agent-rulez-sample.yaml     # PostToolUse/Stop capture hook config
└── references/
    ├── chat-feel.md                 # (existing) tone/formatting rules
    ├── scan-patterns.md             # (existing) repo scanning heuristics
    ├── navigation-commands.md       # (existing) session navigation
    ├── tutorial-mode.md             # (existing) tutorial walkthrough
    ├── persistence.md               # (existing) save/load sessions
    ├── describe-questions.md        # NEW: question bank for Describe mode
    ├── explore-questions.md         # NEW: question bank for Explore mode
    └── codex-tools.md               # NEW: tool name equivalents for Codex
```

### Data Flow

```
User runs /codebase-wizard [--describe | --explore | --file <path>]
  → forks into codebase-wizard-agent (policy island)
  → SKILL.md drives wizard conversation
  → Agent Rulez PostToolUse hook fires on each turn
       → appends Q&A to {storage}/sessions/YYYY-MM-DD-{repo}.json
  → session ends naturally or user says "done"
  → Agent Rulez Stop hook fires
       → reminds user to /codebase-wizard-export

User runs /codebase-wizard-export
  → reads raw JSON from {storage}/sessions/
  → synthesizes → transcript.md + CODEBASE.md (or TOUR.md)
  → writes to {storage}/docs/
```

### Storage Resolution

On first run, resolved once and stored in `{storage}/config.json`:

```
1. .code-wizard/           exists? → use it
2. .claude/code-wizard/    exists? → use it
3. Neither → ask user once → write choice to resolved location
```

Always check both locations on read. Write only to resolved location.

---

## Section 2: The Explainer

### Universal Artifact Support

The wizard accepts any artifact as its subject:

| Artifact | What the explainer does |
|---|---|
| Codebase / source file | Scans, traces call chains, shows code blocks with LOC |
| Markdown spec / PRD | Parses sections, explains each, asks follow-ups |
| Milestone / roadmap doc | Walks through phases, explains deliverables |
| Design doc | Explains decisions, surfaces trade-offs |

The artifact type is detected automatically. If passed a `.md` file, the wizard parses its structure. If pointed at a directory, it scans for entry points.

### The Answer Loop (Every Response)

Every single answer follows this pattern without exception:

```
1. Find the relevant artifact (code, section, passage)
2. Show it as a code block with full anchor:
      // src/auth/middleware.ts → AuthMiddleware → validate() → L14-31
3. Explain in plain English (1 short paragraph, no undefined jargon)
4. Show connections:
      → calls:     src/services/token.ts → TokenService → verify()
      → called by: src/routes/api.ts → router.use() → L8
5. Predict next (2-3 follow-up options)
```

The user never guesses where something lives. The code block is always the anchor. Explanation always follows the code.

### Two Modes

**Describe mode** (`--describe`) — repo owner documents their codebase:
- Scans repo first (reuses `scan-patterns.md` logic)
- Asks questions for context Claude cannot infer: ownership, intent, constraints, domain terms, missing pieces
- One question at a time — not a form dump
- Output: `CODEBASE.md` with sections (Overview, Entry Points, Auth, Data Layer, Key Concepts, Constraints)

**Explore mode** (`--explore`) — new developer getting a tour:
- Same scan, then guides through in learning order (not file order):
  1. What the app does
  2. Where it starts
  3. How auth works
  4. How data flows
  5. Where to make a first change
- User can ask follow-ups, take detours, or say "next"
- Navigation commands from `navigation-commands.md` work throughout
- Output: `TOUR.md` — re-readable learning document

**File mode** (`--file <path>`) — explain a specific artifact:
- Works with any `.md` file (spec, roadmap, design, milestone plan)
- Parses structure, walks through section by section
- Wizard asks follow-up questions about each section
- User says "next" to advance or asks questions to dig deeper

### Research Adaptability

The wizard uses available tools, checked in order:

```
1. Agent Brain (if installed + indexed) → semantic search over codebase
2. Perplexity (if available)           → external context, library docs
3. Codebase scan                       → grep, glob, file reads
4. Markdown parse                      → heading structure, section extraction
```

If a needed tool is unavailable, the wizard asks rather than silently degrading:
> "I can answer this better with Agent Brain — want me to set it up? Or I can scan the codebase directly."

---

## Section 3: Capture + Synthesis

### Agent Rulez Hook Config (`setup/agent-rulez-sample.yaml`)

```yaml
hooks:
  - event: PostToolUse
    action: append
    target: ".code-wizard/sessions/{date}-{repo}.json"
    format: json

  - event: Stop
    action: notify
    message: "Session ended. Run /codebase-wizard-export to generate docs."
```

### Raw Session Format

**`.code-wizard/sessions/YYYY-MM-DD-{repo}.json`:**

```json
{
  "session_id": "2026-03-19-codebase-mentor",
  "repo": "codebase-mentor",
  "artifact": "plugin/SKILL.md",
  "mode": "explore",
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

### Synthesis (`/codebase-wizard-export`)

Reads all session JSON files → generates two documents in `.code-wizard/docs/`:

**`CODEBASE.md`** (structured reference — from Describe mode):
```markdown
# Codebase: {repo}
## Overview
## Entry Points
## Auth
## Data Layer
## Key Concepts (from Q&A)
## Traced Call Chains
## Open Questions
```

**`TOUR.md`** (readable walkthrough — from Explore mode):
- Preserves conversational flow with all code block anchors
- Reads as a guided tour a new developer can re-read

**`SESSION-TRANSCRIPT.md`** (raw Q&A — always generated):
- Full question + answer + code blocks in order
- Preserves every turn

---

## Section 4: Multi-Platform Support

### Platform Matrix

| Platform | Config Dir | Tool Casing | Install | Hook Support |
|---|---|---|---|---|
| Claude Code | `~/.claude/` | PascalCase | Plugin manifest | Yes (Agent Rulez) |
| OpenCode | `~/.config/opencode/` | lowercase | Flat command names | Yes |
| Gemini CLI | `~/.gemini/` | snake_case | TOML format | Yes |
| Codex | `~/.codex/` | See codex-tools.md | AGENTS.md | No (exit 77) |

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
  codex)    install_codex    ;;   # write AGENTS.md, skip hooks
  all)      install_all      ;;
esac
```

### Per-Platform Config Files

- **`CLAUDE.md`** — skill invocation, agent reference
- **`GEMINI.md`** — `activate_skill` mapping + tool equivalents
- **`AGENTS.md`** — Codex instruction file (hook scenarios exit 77)

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
  # File exploration (read-only)
  - "Read"
  - "Glob"
  - "Grep"

  # Session storage writes (scoped to wizard dirs only)
  - "Write(.code-wizard/**)"
  - "Write(.claude/code-wizard/**)"
  - "Edit(.code-wizard/**)"
  - "Edit(.claude/code-wizard/**)"

  # Scan and synthesis scripts
  - "Bash(node*)"
  - "Bash(grep*)"
  - "Bash(find*)"
  - "Bash(cat*)"
  - "Bash(ls*)"

  # Agent Rulez hook management
  - "Bash(rulez*)"

  # Research tools (capability-gated — wizard checks availability first)
  - "WebSearch"
  - "WebFetch"
---
```

**Security choices:**
- `Write` scoped to `.code-wizard/**` only — cannot write elsewhere
- No destructive bash (`rm`, `pkill`, etc.) — wizard never deletes
- Research tools included but wizard checks availability before using

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
Read raw session JSON from storage location.
Synthesize to: transcript.md + CODEBASE.md or TOUR.md.
Write to {storage}/docs/.
```

**`commands/codebase-wizard-setup.md`:**
```yaml
---
# No fork — setup runs once, writes config
---
Run setup/setup.sh:
1. Install Agent Rulez
2. Write settings.local.json permissions
3. Copy agent-rulez-sample.yaml to storage location
4. Ask user: .code-wizard/ or .claude/code-wizard/?
5. Write storage choice to config.json
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
- IDE integrations (Claude Code CLI only)
- Automatic git commits of generated docs

---

## Open Questions

| Question | Impact |
|---|---|
| Should `--file` mode support non-markdown files (e.g. JSON schemas, OpenAPI specs)? | Scope of Section 2 |
| Should export offer a `--format pdf` option via the `pdf` skill? | Nice-to-have for v2 |
| Agent Rulez YAML format — confirm exact hook event names with repo | Section 3 implementation |
