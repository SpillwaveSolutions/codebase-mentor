# Architecture Patterns: v1.2 OpenCode + PyPI Integration

**Domain:** Multi-runtime AI plugin installer (Python package)
**Milestone:** v1.2 — OpenCode converter + PyPI publish
**Researched:** 2026-03-21
**Overall confidence:** HIGH (all findings sourced from actual project files)

---

## Executive Summary

The existing architecture is a clean, extensible monorepo with a single integration seam: `_get_converters()` in `cli.py`. Every new runtime requires only one new file (`opencode.py`) and one dict entry update. The Claude installer (`claude.py`) is a reference implementation that v1.2 mirrors for OpenCode.

The bundled plugin in `ai_codebase_mentor/plugin/` is a static copy of `plugins/codebase-wizard/`. It does not auto-sync; sync is a manual step (copy on release). The `pyproject.toml` package-data glob handles inclusion.

The two GitHub Actions workflows have completely orthogonal triggers: `test-installer.yml` runs on every push; `publish-pypi.yml` runs only on semver tag pushes. They share no steps — the publish workflow does a build+upload, not a copy of test workflow steps.

---

## Component Map: v1.0 Baseline

```
plugins/codebase-wizard/           ← canonical plugin source (Claude Code format)
  .claude-plugin/
    plugin.json                    ← runtime: "claude-code", version: "1.0.0"
    marketplace.json
  agents/
    codebase-wizard-agent.md       ← allowed_tools: PascalCase (Read, Write, Bash...)
    codebase-wizard-setup-agent.md
  commands/
    codebase-wizard.md             ← context: fork, agent: codebase-wizard-agent
    codebase-wizard-export.md
    codebase-wizard-setup.md
  skills/
    explaining-codebase/
      SKILL.md
      references/
        chat-feel.md, scan-patterns.md, navigation-commands.md
        tutorial-mode.md, persistence.md
        describe-questions.md, explore-questions.md
        codex-tools.md             ← tool name matrix across all 4 platforms
    configuring-codebase-wizard/
      SKILL.md
      scripts/setup.sh, agent-rulez-sample.yaml
    exporting-conversation/
      SKILL.md

ai_codebase_mentor/
  plugin/                          ← static copy of plugins/codebase-wizard/
    .claude-plugin/plugin.json, marketplace.json
    agents/*.md
    commands/*.md
    skills/**/*
  converters/
    __init__.py
    base.py                        ← RuntimeInstaller ABC: install/uninstall/status + plugin_source
    claude.py                      ← ClaudeInstaller: shutil.copytree to ~/.claude/plugins/
  cli.py                           ← _get_converters() registry + click group
  __init__.py                      ← __version__ = "1.0.0"

pyproject.toml                     ← version = "1.0.0", entry point, package-data glob
.github/workflows/
  test-installer.yml               ← push + pull_request trigger, matrix OS, no secrets
```

---

## Integration Point 1: opencode.py Converter

### Where it fits

`opencode.py` is a new file at `ai_codebase_mentor/converters/opencode.py`. It subclasses `RuntimeInstaller` from `base.py`, exactly mirroring the structure of `claude.py`.

### What it reads

`opencode.py` receives `self.plugin_source` (inherited from `RuntimeInstaller.plugin_source`, resolves to `ai_codebase_mentor/plugin/`). From that directory, it reads:

| Source path (relative to plugin_source) | Purpose |
|------------------------------------------|---------|
| `agents/codebase-wizard-agent.md` | Extract `allowed_tools:` list from YAML frontmatter |
| `agents/codebase-wizard-setup-agent.md` | Extract `allowed_tools:` list from YAML frontmatter |
| `commands/codebase-wizard.md` | Extract `context:`, `agent:`, command body |
| `commands/codebase-wizard-export.md` | Extract `context:`, `agent:`, command body |
| `commands/codebase-wizard-setup.md` | Extract `context:`, `agent:`, command body |
| `.claude-plugin/plugin.json` | Read `version` field (via `_read_version()` from base.py) |

The `skills/` tree is NOT directly processed by `opencode.py`. OpenCode reads skills as markdown instruction files — they can be copied verbatim or concatenated into a single instructions file, depending on what OpenCode's plugin format requires. The `agents/*.md` and `commands/*.md` files require conversion; the skills tree requires copying.

### Critical transformation: tool name lowercasing

The canonical plugin uses PascalCase tool names (Claude Code convention). OpenCode uses lowercase. The mapping is documented in `ai_codebase_mentor/plugin/skills/explaining-codebase/references/codex-tools.md`:

| Claude Code (canonical) | OpenCode |
|------------------------|----------|
| `Read` | `read` |
| `Write` | `write` |
| `Edit` | `edit` |
| `Bash` | `bash` |
| `Grep` | `grep` |
| `Glob` | `glob` |
| `WebSearch` | `websearch` |
| `WebFetch` | `webfetch` |

Scoped tool entries like `Write(.code-wizard/**)` become `write(.code-wizard/**)` — only the tool name prefix is lowercased; path arguments are preserved as-is.

### What it writes

OpenCode's config directory is `~/.config/opencode/` (confirmed in `codex-tools.md` "Config Dir" column).

Install destinations:

| target | path |
|--------|------|
| `"global"` | `~/.config/opencode/plugins/codebase-wizard/` |
| `"project"` | `./.opencode/plugins/codebase-wizard/` (standard per-project convention) |

**Confidence note:** The exact output file structure OpenCode expects for plugins (JSON manifest, markdown commands, agent files) is an open question flagged in the design spec: "OpenCode plugin format — same schema as `.claude-plugin/plugin.json`?" Web access was unavailable to verify. The safest conservative implementation is to copy the plugin tree and rewrite tool names in agent files. The roadmap phase for `opencode.py` should include an investigation step to verify the actual OpenCode plugin schema before writing conversion code.

### What it does NOT do

- Does not modify `plugins/codebase-wizard/` (canonical source is read-only)
- Does not modify any file under `ai_codebase_mentor/plugin/` (bundled copy is read-only)
- Does not touch `claude.py` or any existing converter

---

## Integration Point 2: cli.py — `_get_converters()` update

### Current state (v1.0)

```python
def _get_converters():
    from ai_codebase_mentor.converters.claude import ClaudeInstaller
    return {"claude": ClaudeInstaller}
```

### Required change (v1.2)

```python
def _get_converters():
    from ai_codebase_mentor.converters.claude import ClaudeInstaller
    from ai_codebase_mentor.converters.opencode import OpenCodeInstaller
    return {
        "claude": ClaudeInstaller,
        "opencode": OpenCodeInstaller,
    }
```

This is the **only** change required to `cli.py`. The existing `install`, `uninstall`, `status`, and `version` commands all dispatch via the registry — they work for `opencode` without modification. The `--for opencode` flag routes correctly because `runtime == "all"` expands to `list(converters.keys())`.

The `--help` text on the `--for` option currently says `Target runtime: claude, all`. Update to `Target runtime: claude, opencode, all` for user clarity, but this is cosmetic.

### What does NOT change in cli.py

- The `@click.group()` and all four `@main.command()` decorators
- The `install`, `uninstall`, `status`, `version` command implementations
- Error handling and exit codes

---

## Integration Point 3: Plugin Bundle Sync Strategy

### Current mechanism

`pyproject.toml` includes `ai_codebase_mentor/plugin/` in the package via:

```toml
[tool.setuptools.package-data]
"ai_codebase_mentor" = ["plugin/**/*", "plugin/**/.claude-plugin/*"]
```

`ai_codebase_mentor/plugin/` is a **static copy** of `plugins/codebase-wizard/`. There is no automated sync mechanism.

### Sync strategy for v1.2

The sync is a manual release step: before tagging, copy `plugins/codebase-wizard/` to `ai_codebase_mentor/plugin/`. This is the existing pattern established in v1.0 and does not change for v1.2.

**Recommended approach for the publish-pypi.yml workflow:** Do NOT add a sync step to the workflow. The workflow should build from whatever is committed. The release author is responsible for running the sync before tagging. This keeps CI deterministic and avoids the workflow having write access to the repo.

**Where to document this:** Add a "Before tagging a release" section to the project README or a `RELEASING.md` file with the manual sync command:

```bash
rsync -a --delete plugins/codebase-wizard/ ai_codebase_mentor/plugin/
```

### What changes in pyproject.toml for v1.2

The `version` field must be bumped from `"1.0.0"` to `"1.2.0"` before PyPI publish. No other `pyproject.toml` fields need updating for the OpenCode converter — no new dependencies are required (stdlib `pathlib`, `shutil`, `json`, `re` are sufficient).

The `description` field currently reads "Install the Codebase Wizard plugin for Claude Code (and other runtimes in future releases)." Update to reflect OpenCode support: "Install the Codebase Wizard plugin for Claude Code and OpenCode."

Keywords should add `"opencode"`.

---

## Integration Point 4: publish-pypi.yml Workflow

### Trigger separation

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `test-installer.yml` | `push` + `pull_request` (all branches) | Smoke test install/uninstall/status on every change |
| `publish-pypi.yml` | `push` with `tags: ['v*.*.*']` filter | Build sdist + wheel, publish to PyPI on semver tag |

These triggers are mutually exclusive in normal use: tagging a release fires `publish-pypi.yml`, not `test-installer.yml` (tags are not branches). However, both can fire if a tag push also contains branch commits — this is harmless and expected.

### publish-pypi.yml structure

The workflow requires PyPI Trusted Publishing (OIDC) — no API token stored as a secret. This is the current PyPI recommended approach (requires configuring a Trusted Publisher in the PyPI project settings pointing at the GitHub Actions workflow file).

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi                     # GitHub environment gates the publish
    permissions:
      id-token: write                     # required for OIDC Trusted Publishing
      contents: read

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install build tools
        run: pip install build
      - name: Build sdist and wheel
        run: python -m build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # No 'with: password:' needed — Trusted Publishing handles auth
```

Confidence: MEDIUM. The `pypa/gh-action-pypi-publish` action and OIDC Trusted Publishing pattern is well established. The exact action version tag (`release/v1` vs a pinned SHA) should be verified against the current PyPI action docs before executing.

### What does NOT go in publish-pypi.yml

- No install/uninstall smoke test steps (that is test-installer.yml's job)
- No `PYPI_API_TOKEN` secret (Trusted Publishing replaces it)
- No manual `twine upload` (the action handles it)

---

## New vs Modified Files: Explicit List

### New files (v1.2)

| File | Type | What it does |
|------|------|-------------|
| `ai_codebase_mentor/converters/opencode.py` | New | `OpenCodeInstaller` subclass: reads agents/commands from plugin/, lowercases tool names, installs to `~/.config/opencode/plugins/codebase-wizard/` |
| `.github/workflows/publish-pypi.yml` | New | Builds and publishes to PyPI on semver tag push |
| `tests/test_opencode_installer.py` | New | TDD test suite for `OpenCodeInstaller` (mirrors `tests/test_claude_installer.py`) |

### Modified files (v1.2)

| File | Change | Scope |
|------|--------|-------|
| `ai_codebase_mentor/cli.py` | Add `OpenCodeInstaller` to `_get_converters()` dict | 2-line addition to `_get_converters()` function |
| `pyproject.toml` | Bump `version` from `"1.0.0"` to `"1.2.0"`, update `description`, add `"opencode"` keyword | 3-field update |
| `ai_codebase_mentor/__init__.py` | Bump `__version__` to match pyproject.toml | 1-line change |
| `ai_codebase_mentor/plugin/` | Sync from `plugins/codebase-wizard/` before tagging | Manual step, not automated |

### Unchanged files (v1.2)

All of the following are untouched by v1.2:

- `ai_codebase_mentor/converters/base.py` — `RuntimeInstaller` ABC, `_read_version()` utility
- `ai_codebase_mentor/converters/claude.py` — `ClaudeInstaller` implementation
- `.github/workflows/test-installer.yml` — existing test workflow
- `plugins/codebase-wizard/` — canonical plugin source
- All `plugin/*.md` skill, command, agent files

---

## Suggested Build Order for v1.2

The two milestone phases have a dependency: `opencode.py` must work before `publish-pypi.yml` is useful (nothing to publish without a working second converter).

### Phase 1: OpenCode Converter

Deliverables (in execution order):

1. `tests/test_opencode_installer.py` — write failing tests first (TDD, mirrors `test_claude_installer.py`)
2. `ai_codebase_mentor/converters/opencode.py` — implement `OpenCodeInstaller` until tests pass
3. `ai_codebase_mentor/cli.py` — add `"opencode": OpenCodeInstaller` to `_get_converters()`
4. Verify `ai-codebase-mentor install --for opencode` end-to-end (manual smoke test)
5. Extend `test-installer.yml` to add opencode install/uninstall/status steps (optional but recommended)

**Dependency to resolve before coding:** Confirm the exact OpenCode plugin directory structure. The design spec flags this as an open question. If OpenCode reads agents from `~/.config/opencode/agents/*.md` and commands from `~/.config/opencode/commands/*.md` directly (similar to Claude Code reading from `~/.claude/plugins/`), the converter is a copy-with-rewrite. If OpenCode uses a JSON manifest referencing other files, the converter must generate that manifest too.

### Phase 2: PyPI Publish

Deliverables (in execution order):

1. `pyproject.toml` — bump version to `1.2.0`, update description
2. `ai_codebase_mentor/__init__.py` — bump `__version__`
3. Sync `ai_codebase_mentor/plugin/` from `plugins/codebase-wizard/`
4. `.github/workflows/publish-pypi.yml` — create publish workflow
5. Configure PyPI Trusted Publisher (one-time web UI step in PyPI project settings)
6. Tag `v1.2.0` — triggers publish workflow

Phase 2 cannot proceed until Phase 1 is complete because the PyPI package being published must include the working OpenCode converter.

---

## Architecture Invariants to Preserve

These constraints from the existing codebase must not be violated by v1.2 changes:

1. **`base.py` is not modified.** `RuntimeInstaller` is stable. New converters subclass it; they do not extend it.

2. **`claude.py` is not modified.** The existing Claude installer must continue to work identically. No shared code is extracted from `claude.py` into `base.py` in this milestone.

3. **`_get_converters()` remains the only registry.** No new registry mechanism. No auto-discovery. Adding `opencode.py` requires only one dict entry change.

4. **`plugin_source` resolves the same path for all converters.** `OpenCodeInstaller` uses the inherited `plugin_source` property — it does not bundle its own plugin copy or point to a different directory. All converters share `ai_codebase_mentor/plugin/` as the single source.

5. **`uninstall()` is always a no-op when not installed.** OpenCode uninstall follows the same contract: check if destination exists, return silently if not, remove if present.

6. **`install()` is idempotent.** If `~/.config/opencode/plugins/codebase-wizard/` already exists, remove it and re-copy (same pattern as `claude.py`).

7. **No new runtime dependencies.** The `opencode.py` converter uses only Python stdlib. The `dependencies = ["click>=8.0"]` in `pyproject.toml` does not change.

---

## Confidence Assessment

| Area | Confidence | Source | Notes |
|------|------------|--------|-------|
| opencode.py fit in architecture | HIGH | `base.py`, `claude.py`, `cli.py` read directly | Pattern is explicit in existing code |
| Tool name mapping (PascalCase → lowercase) | HIGH | `codex-tools.md` in plugin/skills/explaining-codebase/references/ | Definitive matrix in project files |
| OpenCode config dir (~/.config/opencode/) | HIGH | `codex-tools.md` "Config Dir" column | Listed explicitly in project |
| Plugin bundle sync strategy | HIGH | `pyproject.toml` package-data, `base.py` plugin_source | Static copy pattern is clear |
| `_get_converters()` update scope | HIGH | `cli.py` read directly | 2-line change, pattern is clear |
| pyproject.toml version bump fields | HIGH | `pyproject.toml` read directly | Fields identified by inspection |
| publish-pypi.yml trigger (semver tag) | HIGH | Design spec Section 3 Milestone 2, Phase 7 PLAN explicitly deferred it | Explicitly stated in two places |
| OpenCode plugin output file schema | LOW | Web access unavailable; design spec flags as open question | Must verify before coding opencode.py; described as open question in spec |
| PyPI Trusted Publishing action version | MEDIUM | Known pattern; specific action tag unverified (no web access) | Use `pypa/gh-action-pypi-publish@release/v1`, verify current tag before use |

---

## Open Questions

1. **OpenCode plugin schema:** What exact directory structure and files does OpenCode expect when reading a plugin from `~/.config/opencode/plugins/`? Does it use a JSON manifest? Does it read `agents/*.md` and `commands/*.md` directly (same as Claude Code), or does it use a different file layout? This is the primary blocker for `opencode.py` implementation and was flagged as an open question in the design spec (`docs/superpowers/specs/2026-03-20-codebase-wizard-multi-runtime-design.md`, Open Questions table).

   **Resolution path:** Check OpenCode official docs at `https://opencode.ai/docs` or the OpenCode GitHub repo (`https://github.com/sst/opencode`) before starting `opencode.py` coding.

2. **PyPI Trusted Publisher setup:** The one-time PyPI web UI configuration (adding a Trusted Publisher pointing at the GitHub Actions workflow) must be done before the publish workflow can succeed. This is not automated and must be done by the package owner.

3. **`test-installer.yml` scope expansion:** Should `test-installer.yml` be extended to also test `--for opencode` after Phase 1 ships? Recommended yes, to match the v1.0 pattern of testing every supported runtime on push. This would be a modification to `test-installer.yml` in Phase 1, not Phase 2.

---

## Sources

All findings sourced from project files (HIGH confidence):

- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/ai_codebase_mentor/converters/base.py` — RuntimeInstaller ABC
- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/ai_codebase_mentor/converters/claude.py` — ClaudeInstaller reference implementation
- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/ai_codebase_mentor/cli.py` — `_get_converters()` registry pattern
- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/pyproject.toml` — package config, version, package-data glob
- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/.github/workflows/test-installer.yml` — existing workflow structure and triggers
- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/ai_codebase_mentor/plugin/skills/explaining-codebase/references/codex-tools.md` — tool name matrix and config dir per platform
- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/docs/superpowers/specs/2026-03-20-codebase-wizard-multi-runtime-design.md` — Converter responsibilities table, open questions
- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/.planning/PROJECT.md` — milestone goals and constraints
- `/Users/richardhightower/clients/spillwave/src/codebase-mentor/.planning/phases/07-github-actions-workflows-for-installer-tests-and-pypi-release-on-tag/07-01-PLAN.md` — PyPI deferral decision
