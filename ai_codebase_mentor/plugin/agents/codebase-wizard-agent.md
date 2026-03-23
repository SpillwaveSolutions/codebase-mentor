---
name: codebase-wizard-agent
description: >
  Pre-authorized agent for the Codebase Wizard. Covers scanning, Q&A,
  capture, synthesis, and export. Zero approval prompts during sessions.
model: inherit
color: blue

allowed_tools:
  # File exploration (read-only, unrestricted paths)
  # These are intentionally unrestricted — the wizard must be able to read
  # any file in the repo it is explaining. Restricting Read would break
  # the core explain-from-code contract.
  - "Read"
  - "Glob"
  - "Grep"

  # Session storage writes (scoped to wizard dirs only)
  # Write and Edit are restricted to wizard-managed directories.
  # The agent cannot modify source files, configs, or any path outside
  # these two directories. This is the hard security boundary.
  - "Write(.code-wizard/**)"
  - "Write(.claude/code-wizard/**)"
  - "Edit(.code-wizard/**)"
  - "Edit(.claude/code-wizard/**)"

  # Scan and synthesis helpers (no destructive operations)
  # Only safe, read-oriented shell commands are permitted.
  # rm, pkill, chmod, and other destructive commands are not in this list
  # and will be blocked. The wizard never deletes anything.
  - "Bash(node*)"
  - "Bash(grep*)"
  - "Bash(find*)"
  - "Bash(cat*)"
  - "Bash(ls*)"

  # Agent Rulez hook management
  # Required for the wizard to register and query its PostToolUse hooks.
  - "Bash(rulez*)"

  # Research tools (pre-authorized; wizard probes availability before use)
  # Including these in allowed_tools means they never prompt during sessions.
  # The permission decision was made at plugin install time.
  # The wizard still gates their use behind a runtime availability probe
  # (e.g., `which agent-brain`) — pre-authorization is not unconditional use.
  - "WebSearch"
  - "WebFetch"
---

# Codebase Wizard Agent — Policy Island

This agent definition pre-authorizes every tool the Codebase Wizard needs
for a full session: scanning, Q&A, capture, synthesis, and export.
Zero approval prompts fire during normal wizard use.

---

## Permission Groups

### Group 1: File Exploration (Read-Only, Unrestricted)

**Tools:** `Read`, `Glob`, `Grep`

**Rationale:** The wizard must be able to read any file in the repository it
is explaining. Restricting these to a specific path would break the core
contract — show code, then explain it. Read-only tools carry no write risk,
so they are pre-authorized without a path scope.

**What this covers:**
- Phase 1 repo scan: discovering entry points, folder roles, configs, docs
- Phase 2 question handling: finding the exact file + line for any answer
- Phase 4 tutorial mode: reading README and docs files
- Phase 5 persistence: reading saved session files to resume

---

### Group 2: Session Storage Writes (Scoped)

**Tools:** `Write(.code-wizard/**)`, `Write(.claude/code-wizard/**)`,
`Edit(.code-wizard/**)`, `Edit(.claude/code-wizard/**)`

**Rationale:** The wizard writes session transcripts, generated docs
(CODEBASE.md, TOUR.md, FILE-NOTES.md), and config to storage directories.
Write and Edit are scoped to these two paths only. The agent cannot write to
source files, `.claude/settings.local.json`, or any path outside the wizard
directories — any attempt is blocked by the permission boundary.

**What this covers:**
- Writing SESSION-TRANSCRIPT.md, CODEBASE.md, TOUR.md, FILE-NOTES.md
- Writing config.json on first setup
- Updating session JSON files during capture

---

### Group 3: Scan and Synthesis Helpers (No Destructive Ops)

**Tools:** `Bash(node*)`, `Bash(grep*)`, `Bash(find*)`, `Bash(cat*)`,
`Bash(ls*)`

**Rationale:** The wizard uses safe, read-oriented shell commands to scan
the codebase and synthesize documents. Only these prefixes are permitted.
Destructive shell commands (`rm`, `pkill`, `chmod`, `mv`, `cp` to arbitrary
paths) are not listed here and are blocked.

**What this covers:**
- `ls` / `find`: directory structure inspection during repo scan
- `grep`: pattern search when Grep tool is insufficient
- `cat`: reading file contents for synthesis
- `node`: running synthesis scripts if needed

---

### Group 4: Agent Rulez Hook Management

**Tool:** `Bash(rulez*)`

**Rationale:** The wizard registers and queries its PostToolUse capture hooks
via the Agent Rulez CLI. Scoped to `rulez*` to permit only Agent Rulez
commands, not arbitrary bash.

**What this covers:**
- `rulez install` during setup
- `rulez hook add` to register the capture hook
- `rulez hook list` to verify hook status

---

### Group 5: Research Tools (Pre-Authorized)

**Tools:** `WebSearch`, `WebFetch`

**Rationale:** Including these in `allowed_tools` means they never prompt
during sessions. The wizard probes their availability at runtime before use
(e.g., checking API key presence). Pre-authorization in this agent is the
install-time permission decision; session-time use is still gated by the
research priority waterfall (Agent Brain → Perplexity → codebase scan).

**What this covers:**
- Looking up library documentation for external context
- Fetching official API docs when a question requires it
- Research Priority tier 2: Perplexity / web search fallback

---

## Security Summary

| Risk | Mitigation |
|------|------------|
| Writing to source files | Write/Edit scoped to `.code-wizard/**` and `.claude/code-wizard/**` only |
| Destructive shell commands | Bash restricted to `node*`, `grep*`, `find*`, `cat*`, `ls*`, `rulez*` |
| Unbounded web access | WebSearch/WebFetch are available but gated behind runtime availability probe |
| Reading sensitive files | Read is intentionally unrestricted; wizard reads what it explains |

The agent cannot write outside `.code-wizard/**` or `.claude/code-wizard/**`.
Any attempt to modify source files is blocked at the permission boundary —
not by convention, but by the allowed_tools list.
