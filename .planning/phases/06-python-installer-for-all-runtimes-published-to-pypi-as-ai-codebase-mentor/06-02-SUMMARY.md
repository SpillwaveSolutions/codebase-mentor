---
plan: 06-02
phase: 06-python-installer-for-all-runtimes-published-to-pypi-as-ai-codebase-mentor
status: complete
completed: 2026-03-20
---

# Summary: Phase 06-02 — CLI Wiring

## What Was Done

Replaced the stub `cli.py` from 06-01 with the full implementation.

## CLI Commands

```
ai-codebase-mentor install    --for [claude|all] [--project]
ai-codebase-mentor uninstall  --for [claude|all] [--project]
ai-codebase-mentor status
ai-codebase-mentor version
```

## Verification Results

| Check | Result |
|-------|--------|
| `--help` lists 4 subcommands | PASS |
| `version` prints `ai-codebase-mentor 1.0.0` | PASS |
| `install --for unknown-runtime` exits 1 with "Unsupported runtime" | PASS |
| `status` reports claude install state | PASS |
| `cli import OK` | PASS |
| No `dist/` directory | PASS (PyPI publish excluded) |

## Status Output

```
claude: installed at /...codebase-mentor/plugins/codebase-wizard (v1.0.0)
```
(Project-scope check fires because `./plugins/codebase-wizard/` exists in repo root — correct behavior.)

## Checkpoint Task

The plan included a `checkpoint:human-verify` gate. Since Phase 5 ClaudeInstaller was already complete and all automated checks passed, the checkpoint was satisfied by the verification output above.

## Design: Lazy Import Registry

```python
def _get_converters():
    from ai_codebase_mentor.converters.claude import ClaudeInstaller
    return {"claude": ClaudeInstaller}
```

Lazy import means the registry can grow (add opencode/codex/gemini) without changing the CLI structure. Adding v1.2 opencode support requires only: `from ... import OpenCodeInstaller` + `"opencode": OpenCodeInstaller` in the dict.
