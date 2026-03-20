---
name: codebase-wizard-setup-agent
description: >
  Pre-authorized agent for Codebase Wizard setup. Covers storage creation,
  Agent Rulez install, hook registration, and settings.local.json write.
  Broader permissions than the session agent — only used during /codebase-wizard-setup.

allowed_tools:
  # File exploration (read-only, unrestricted)
  - "Read"
  - "Glob"
  - "Grep"

  # Wizard storage writes (same as session agent)
  - "Write(.code-wizard/**)"
  - "Write(.claude/code-wizard/**)"
  - "Edit(.code-wizard/**)"
  - "Edit(.claude/code-wizard/**)"

  # Settings writes (setup-specific — session agent does NOT have these)
  # Required to write scoped permissions during onboarding.
  # This is the sole reason a separate setup agent exists.
  - "Write(.claude/settings.local.json)"
  - "Edit(.claude/settings.local.json)"

  # AGENTS.md for Codex platform support
  - "Write(AGENTS.md)"
  - "Edit(AGENTS.md)"

  # Setup shell operations
  # Broader than the session agent — setup needs mkdir, cp, chmod, bash scripts.
  - "Bash(rulez*)"
  - "Bash(node*)"
  - "Bash(bash*)"
  - "Bash(mkdir*)"
  - "Bash(cp*)"
  - "Bash(chmod*)"
  - "Bash(ls*)"
  - "Bash(cat*)"
---

# Codebase Wizard Setup Agent — Policy Island

Pre-authorizes every tool needed for one-time wizard setup: storage creation,
Agent Rulez install, hook registration, and settings.local.json write.

This agent is wider than the session agent (`codebase-wizard-agent`) by design.
It is only activated via `/codebase-wizard-setup` — not during normal sessions.

---

## Why a Separate Setup Agent

The session agent (`codebase-wizard-agent`) cannot write to
`.claude/settings.local.json` — that path is intentionally outside its
permission boundary to prevent the wizard from modifying its own permissions
during a session.

Setup is different: it runs once during onboarding and explicitly needs to
write `settings.local.json` to grant the session agent its scoped permissions.
A dedicated setup agent lets us use `context: fork` for setup too, while still
keeping the permission boundary explicit and auditable.

---

## Permission Groups

### Group 1: File Exploration (Read-Only, Unrestricted)

**Tools:** `Read`, `Glob`, `Grep`

Needed to inspect current settings, check existing storage, read config files.

---

### Group 2: Wizard Storage Writes

**Tools:** `Write/Edit(.code-wizard/**)`, `Write/Edit(.claude/code-wizard/**)`

Creates storage directories, writes `config.json`, deploys `agent-rulez.yaml`.

---

### Group 3: Settings Write (Setup-Specific)

**Tools:** `Write(.claude/settings.local.json)`, `Edit(.claude/settings.local.json)`

Writes scoped write permissions for the session agent. This is the critical
extra permission that separates the setup agent from the session agent.

---

### Group 4: Codex Platform Support

**Tools:** `Write(AGENTS.md)`, `Edit(AGENTS.md)`

Creates `AGENTS.md` with manual export instructions when `./setup.sh codex`
runs (Codex uses instruction files instead of hooks).

---

### Group 5: Setup Shell Operations

**Tools:** `Bash(rulez*)`, `Bash(node*)`, `Bash(bash*)`, `Bash(mkdir*)`,
`Bash(cp*)`, `Bash(chmod*)`, `Bash(ls*)`, `Bash(cat*)`

Runs `setup.sh`, creates directories, deploys files. Broader than the session
agent's bash permissions because setup requires file system operations that
sessions never need.

---

## Security Summary

| Risk | Mitigation |
|------|------------|
| Writing arbitrary files | Write/Edit scoped to wizard dirs + settings.local.json + AGENTS.md only |
| Modifying source files | Not in allowed_tools — any attempt blocked |
| Running during sessions | Only activated by /codebase-wizard-setup command |
| Escalating own permissions | Can only write settings.local.json, not settings.json |
