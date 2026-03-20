---
plan: 06-01
phase: 06-python-installer-for-all-runtimes-published-to-pypi-as-ai-codebase-mentor
status: complete
completed: 2026-03-20
---

# Summary: Phase 06-01 — Package Scaffold

## What Was Done

Created the ai-codebase-mentor Python package scaffold:

| File | Content |
|------|---------|
| `pyproject.toml` | `[build-system]` uses `setuptools.build_meta` (not legacy backend — not available on Python 3.13) |
| `MANIFEST.in` | `recursive-include ai_codebase_mentor/plugin *` |
| `ai_codebase_mentor/__init__.py` | `__version__ = "1.0.0"` |
| `ai_codebase_mentor/converters/__init__.py` | Docstring only |
| `ai_codebase_mentor/converters/base.py` | `RuntimeInstaller` ABC + `plugin_source` property + `_read_version()` helper |
| `ai_codebase_mentor/plugin/` | Full copy of `plugins/codebase-wizard/` via `cp -r` |
| `ai_codebase_mentor/cli.py` | Stub: empty click group for `pip install -e .` to work before full CLI |

## Build System Note

The plan specified `setuptools.backends.legacy:build` — not available on the local Python 3.13 / setuptools environment. Changed to `setuptools.build_meta` (the standard backend), which works correctly.

## Bundled Plugin

`ai_codebase_mentor/plugin/` mirrors `plugins/codebase-wizard/` exactly:
- `.claude-plugin/plugin.json` and `marketplace.json`
- `skills/` (3 subdirectories)
- `agents/` (2 agent files)
- `commands/` (3 command files)

## Verification

```
python -c "import ai_codebase_mentor; print(ai_codebase_mentor.__version__)"  → 1.0.0
python -c "from ai_codebase_mentor.converters.base import RuntimeInstaller; print('base OK')"  → base OK
python -c "Path('ai_codebase_mentor/plugin/.claude-plugin/plugin.json').exists()"  → True
python -c "import tomllib; d=...; assert d['project']['scripts']['ai-codebase-mentor']=='ai_codebase_mentor.cli:main'"  → entry point OK
ai-codebase-mentor --help  → Usage: ai-codebase-mentor [OPTIONS] COMMAND [ARGS]... (stub, no subcommands)
```

## plugin_source Property

Added to `RuntimeInstaller` base class:
```python
@property
def plugin_source(self) -> Path:
    return Path(__file__).parent.parent / "plugin"
```
Resolves to `ai_codebase_mentor/plugin/` from `converters/base.py`. All subclasses inherit this default.
