---
plan: 07-01
phase: 07-github-actions-workflows-for-installer-tests-and-pypi-release-on-tag
status: complete
completed: 2026-03-20
---

# Summary: Phase 07-01 — GitHub Actions Test Installer Workflow

## What Was Created

`.github/workflows/test-installer.yml` — CI workflow for install/uninstall/status smoke tests.

## Workflow Details

| Property | Value |
|----------|-------|
| Triggers | `push` (all branches), `pull_request` |
| Matrix OS | ubuntu-latest, macos-latest |
| Python version | 3.11 |
| fail-fast | false (both platforms show results even when one fails) |

## Step Sequence (10 steps)

1. Check out repository (`actions/checkout@v4`)
2. Set up Python (`actions/setup-python@v5` with pip cache)
3. Install package from source (`pip install -e .`)
4. Verify CLI entry point is available (`ai-codebase-mentor --version`)
5. Install codebase-wizard for Claude (`ai-codebase-mentor install --for claude`)
6. Verify plugin files exist (`test -d "$HOME/.claude/plugins/codebase-wizard"`)
7. Check status installed (`ai-codebase-mentor status`)
8. Uninstall codebase-wizard for Claude (`ai-codebase-mentor uninstall --for claude`)
9. Verify plugin files removed (`test ! -d "$HOME/.claude/plugins/codebase-wizard"`)
10. Check status uninstalled (`ai-codebase-mentor status`)

## Excluded (PyPI Deferred)

`.github/workflows/publish-pypi.yml` was NOT created. PyPI publish is deferred to Milestone 2 (v1.2). The `workflows/` directory contains only `test-installer.yml`.

## Notes

- `ai-codebase-mentor --version` step: requires `@click.version_option()` on the click group — added to `cli.py` alongside the `version` subcommand.
- PyYAML parses the `on:` trigger key as Python `True` (YAML boolean alias). The file is structurally valid — GitHub Actions reads it correctly from disk without PyYAML interference.
- Phase 6 (pyproject.toml + ai_codebase_mentor/) must be complete for CI to pass — this workflow depends on `pip install -e .` succeeding. Phase 6 is now complete (2026-03-20).

## Milestone 1 Completion Status

All 7 phases planned and executed:
- Phase 4: Plugin manifest (plugin.json + marketplace.json) ✓
- Phase 5: ClaudeInstaller (base class + TDD, 9/9 tests pass) ✓
- Phase 6: Python package (pyproject.toml, bundled plugin, cli.py) ✓
- Phase 7: GitHub Actions test workflow ✓

Milestone 1 (v1.0) release gate is structurally complete. CI will verify on push.
