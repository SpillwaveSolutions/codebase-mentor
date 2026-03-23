---
type: quick
task: 260323-nrh
title: Update Agent Rulez todo with first-run findings
date: 2026-03-23
files_modified:
  - .planning/todos/pending/2026-03-23-fix-agent-rulez-config-and-add-session-capture-hook.md
commits:
  - f4cfaba
duration_estimate: "<5 min"
---

# Quick Task 260323-nrh: Update Agent Rulez todo with first-run findings

**One-liner:** Replaced vague problem statements in agent-rulez todo with four confirmed root causes and three actionable fixes discovered during live codebase-wizard testing on book_generator.

## What Was Done

Rewrote `.planning/todos/pending/2026-03-23-fix-agent-rulez-config-and-add-session-capture-hook.md`
from scratch. The original file described symptoms and listed things to investigate. The new file
contains confirmed root causes and exact implementation steps.

### Before

The todo described two vague problems:
- "Agent Rulez file looks malformed — needs inspection"
- "Missing session capture hook — design and implement"

Both items required research before any code could be written. The files listed in frontmatter
pointed to a non-existent `plugins/` path rather than `plugin/`.

### After

The todo now has three sections:

**Confirmed Findings** — four facts from live testing:
1. `agent-rulez-sample.yaml` uses `hooks:` (wrong); correct key is `rules:`; non-existent actions `append`/`notify` replaced by valid `block`/`inject`/`run`
2. `rulez hook add` subcommand does not exist; correct command is `rulez install`
3. Agent Rulez is a policy enforcement engine, not a session recorder; cannot write JSON turn data
4. Session capture belongs in the wizard skill's Answer Loop via Write tool calls, not in any hook

**Corrected Solution** — three discrete, implementable changes with exact YAML/JSON schemas and
code snippets. No research required to execute.

**Files to Change** — updated frontmatter and body to reference actual `plugin/` paths.

## Commits

| Hash | Description |
|------|-------------|
| f4cfaba | fix(260323-nrh): rewrite agent rulez todo with confirmed first-run findings |

## Deviations from Plan

None. Plan executed exactly as written.

## Self-Check: PASSED

- [x] Todo file exists at `.planning/todos/pending/2026-03-23-fix-agent-rulez-config-and-add-session-capture-hook.md`
- [x] Section "Confirmed Findings" present with 4 numbered findings
- [x] Section "Corrected Solution" present with 3 subsections
- [x] Section "Files to Change" present with 3 files
- [x] Frontmatter `files` list updated to `plugin/` paths
- [x] Commit f4cfaba exists
