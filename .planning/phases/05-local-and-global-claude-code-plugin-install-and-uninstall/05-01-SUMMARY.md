---
plan: 05-01
phase: 05-local-and-global-claude-code-plugin-install-and-uninstall
status: complete
completed: 2026-03-20
---

# Summary: Phase 05-01 — Package Skeleton and RuntimeInstaller Base Class

## What Was Done

Created the `ai_codebase_mentor` Python package skeleton:

- `ai_codebase_mentor/__init__.py` — sets `__version__ = "1.0.0"`, single-line docstring
- `ai_codebase_mentor/converters/__init__.py` — empty module docstring only; no imports
- `ai_codebase_mentor/converters/base.py` — `RuntimeInstaller` ABC and `_read_version()` helper

## RuntimeInstaller ABC

Three abstract methods matching the design spec signature exactly:

| Method | Signature |
|--------|-----------|
| `install` | `(self, source: Path, target: str = "global") -> None` |
| `uninstall` | `(self, target: str = "global") -> None` |
| `status` | `(self) -> dict` |

## `_read_version()` Helper

Module-level function (not a method). Reads `plugin_dir / ".claude-plugin" / "plugin.json"`, returns `data["version"]` or `None` if anything fails. Shared by all converters for the `status()` implementation.

## Verification

```
python3 -c "import ai_codebase_mentor; print(ai_codebase_mentor.__version__)"  → 1.0.0
python3 -c "from ai_codebase_mentor.converters.base import RuntimeInstaller, _read_version; import inspect; print(inspect.isabstract(RuntimeInstaller))"  → True
```

## Design Decisions

- `converters/__init__.py` is intentionally empty — no auto-imports of converter classes. The CLI (Phase 6) does explicit imports to avoid errors when only some converters are present (v1.0 has only claude.py).
- `_read_version()` returns `None` on any exception — never raises. Converters that need it for `status()` get safe behavior for free.
- Path.home() calls are deferred to method bodies in all subclasses (not class-level constants) so monkeypatch works in tests.
