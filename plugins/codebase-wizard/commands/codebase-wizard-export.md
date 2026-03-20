---
context: fork
agent: codebase-wizard-agent
---

# /codebase-wizard-export

Synthesizes raw session JSON into structured docs. Forks into
`codebase-wizard-agent` (session agent — write access scoped to wizard dirs).

Args: `--latest` (default) | `--session <filename>` | `--all`

All export behavior is governed by the `exporting-conversation` skill.
This command is the entry point only.
