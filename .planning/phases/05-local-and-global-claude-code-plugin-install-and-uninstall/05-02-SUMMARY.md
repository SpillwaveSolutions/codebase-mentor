---
plan: 05-02
phase: 05-local-and-global-claude-code-plugin-install-and-uninstall
status: complete
completed: 2026-03-20
---

# Summary: Phase 05-02 — ClaudeInstaller TDD

## What Was Done

Implemented `ClaudeInstaller` in `ai_codebase_mentor/converters/claude.py` using TDD (RED → GREEN).

## Test Results

```
9 passed in 0.16s
```

All 9 tests verified:

| Test | Behavior |
|------|---------|
| `test_global_install_copies_plugin_json` | plugin.json present at `~/.claude/plugins/codebase-wizard/.claude-plugin/plugin.json` |
| `test_project_install_copies_plugin_json` | plugin.json present at `./plugins/codebase-wizard/.claude-plugin/plugin.json` |
| `test_global_install_is_idempotent` | second `install()` call does not raise |
| `test_global_uninstall_removes_directory` | `~/.claude/plugins/codebase-wizard/` gone after uninstall |
| `test_project_uninstall_removes_directory` | `./plugins/codebase-wizard/` gone after uninstall |
| `test_uninstall_when_not_installed_is_noop` | `uninstall()` with nothing installed returns cleanly |
| `test_status_after_global_install` | `installed=True`, correct `location`, `version="1.0.0"` |
| `test_status_before_install` | `{"installed": False, "location": None, "version": None}` |
| `test_install_raises_runtime_error_on_bad_source` | `RuntimeError` with "not found" in message |

## Implementation

`ClaudeInstaller._resolve_dest(target)` — private helper returns the right `Path` based on target string. Called inside `install()`, `uninstall()`, and `status()` so `Path.home()` and `Path.cwd()` are evaluated at call time (not class load), enabling monkeypatch isolation.

`shutil.copytree` for install (fresh copy after rmtree if destination exists), `shutil.rmtree` for uninstall. Both wrapped in `OSError → RuntimeError` conversion.

## Test Infrastructure

- `source_plugin_dir` fixture: `shutil.copytree(REAL_PLUGIN_SOURCE, tmp_path/"plugin-source"/"codebase-wizard")`
- `installer` fixture: redirects `Path.home()` → `tmp_path/"home"`, `Path.cwd()` → `tmp_path/"cwd"` via `monkeypatch`
- Every test fully isolated — no shared state

## Downstream Consumers

Phase 6 `cli.py` imports `ClaudeInstaller` directly and calls `install()`, `uninstall()`, `status()`.
