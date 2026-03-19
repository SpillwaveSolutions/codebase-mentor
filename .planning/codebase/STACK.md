# Technology Stack

**Analysis Date:** 2026-03-19

## Project Type

**codebase-mentor** is a Claude agent skill — a conversational, tutor-style agent for exploring and understanding codebases. The system is implemented as structured markdown specifications, not a traditional compiled/runtime application. There is no build system, package manager, or runtime environment.

## Languages

**Primary:**
- Markdown - All executable specifications and behavioral rules
- Plain text - Configuration and reference documentation

**Usage:**
- `plugin/SKILL.md` - Main skill specification with trigger conditions and phase logic
- `plugin/references/*.md` - Five reference modules loaded on-demand by each phase
- Skill fronts the Claude API platform directly; no transpilation or build step required

## Execution Model

**Platform:** Claude API (agent platform)

**Invocation:**
- Triggered through natural language queries
- No build process, no compilation
- Loaded directly as conversational context when activated

**Behavioral Rules:**
Defined entirely in markdown with embedded decision trees and flowcharts:
- `SKILL.md` governs trigger detection and 5-phase flow
- `references/chat-feel.md` provides tone/formatting standards (always loaded)
- Phase-specific references loaded on-demand to manage context budget

## Configuration

**Environment:**
- No environment variables required
- No secrets management
- No API keys (skill runs within Claude's native environment)

**Skill Metadata:**
```markdown
---
name: codebase-mentor
description: Conversational tutor-style agent for exploring and understanding codebases...
---
```
Metadata in `plugin/SKILL.md` controls agent platform activation.

**No external configuration files.**

## Storage & State

**Session State (in-memory):**
```json
{
  "repo": "repository-name",
  "history": [
    { "topic": "topic-name", "file": "file/path", "line": 123 }
  ],
  "current": 0,
  "tutorial_step": null,
  "bookmarks": []
}
```

**Persistence:**
- Sessions saved as `.md` files (`[topic]-[YYYY-MM-DD].md`)
- Companion `.json` files for programmatic resume
- Location: `/docs/agent/` (within target repo, if writable)

**Maximum session history:** 20 entries (oldest dropped when exceeded)

## Runtime Constraints

**Context Budget:**
- Reference files loaded selectively to avoid context bloat
- Phase 1: `scan-patterns.md` loaded
- Phase 2: (no extra load)
- Phase 3: `navigation-commands.md` loaded
- Phase 4: `tutorial-mode.md` loaded
- Phase 5: `persistence.md` loaded
- `chat-feel.md` always loaded

**Performance Notes:**
- No network calls
- No database operations
- Entirely text-based processing
- Latency determined by Claude API response time

## Dependencies

**Zero external dependencies.** The skill runs within Claude's native platform without requiring:
- Package managers (npm, pip, cargo, etc.)
- External libraries or SDKs
- System runtimes (Node, Python, Java, etc.)
- Database connections
- File system access beyond reading the target repository

## Platform Requirements

**Development:**
- Text editor (markdown)
- Git repository access
- Claude API platform account

**Deployment:**
- Registered with Claude agent platform
- Accessible via agent skill marketplace
- No build artifacts or compiled binaries

**Consumers:**
- Claude instances with agent skill support
- User-provided repository (scanned in-memory during conversation)

---

*Stack analysis: 2026-03-19*
