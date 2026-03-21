# Technology Stack — v1.2 OpenCode + PyPI

**Project:** ai-codebase-mentor
**Milestone:** v1.2 — OpenCode converter + PyPI publish
**Researched:** 2026-03-21
**Scope:** Stack additions/changes ONLY — does not re-cover validated v1.0 foundations

---

## Existing Stack (Do Not Change)

| Component | Current Value | Status |
|-----------|--------------|--------|
| Build backend | `setuptools>=68` + `wheel` | Keep as-is |
| Runtime dep | `click>=8.0` | Keep as-is |
| Python floor | `>=3.9` | Keep as-is |
| Dev dep | `pytest>=7.0` | Keep as-is |
| Converter base | `abc.ABC` + stdlib `pathlib`, `json`, `shutil` | Keep as-is |
| CLI | Click group with lazy `_get_converters()` | Extend, do not refactor |
| CI | `actions/checkout@v4`, `actions/setup-python@v5` | Already in test workflow |

---

## OpenCode Converter — Stack Additions

### Python Dependencies: None Required

The `opencode.py` converter uses only stdlib. The conversion job is:

1. Read `agents/*.md` frontmatter (YAML-delimited `---` blocks) — parse with `str.split('---')` or stdlib `re`, not PyYAML (avoids a new dep)
2. Lowercase tool names from `allowed_tools` list using the mapping in `codex-tools.md`
3. Write output files as plain text/JSON to `~/.config/opencode/`

**Why no PyYAML dep:** The frontmatter in agent files is simple key/value + list syntax. A 10-line parser using `re` and `str.split` handles it without importing PyYAML. Introducing PyYAML just to parse 3-field frontmatter would add a transitive dep to every `pip install ai-codebase-mentor` for no benefit. Use stdlib only.

**Why no `tomllib`/`tomli`:** OpenCode's native config format is JSON or YAML, not TOML (TOML is Codex's format — v1.3). The opencode.py converter writes JSON. `json` is stdlib.

### OpenCode Plugin Format

**Confidence: MEDIUM** — Derived from project's own `codex-tools.md` and the design spec open question. No official OpenCode documentation was accessible during research. The spec explicitly flags this as unresolved: "OpenCode plugin format — same schema as `.claude-plugin/plugin.json`?"

What is known from project sources (HIGH confidence from `codex-tools.md`):

| Property | Value |
|----------|-------|
| Config directory | `~/.config/opencode/` |
| Tool naming | lowercase (`read`, `write`, `bash`, `glob`, `grep`, `websearch`, `webfetch`) |
| Hook support | Yes |
| Install scope | Global only (no per-project path documented in design spec) |

**Recommended approach for opencode.py:** Write JSON output (matching `plugin.json` structure with `runtime: "opencode"` and lowercased tool names) to `~/.config/opencode/plugins/codebase-wizard/`. If OpenCode uses a different manifest schema, the converter needs a one-time update — but the file I/O and tool-name translation logic is the same either way.

**Phase research flag:** The `opencode.py` converter MUST verify the actual OpenCode plugin directory and manifest schema before implementation. Check `opencode --help`, `opencode plugins list`, or `~/.config/opencode/` layout on a machine with OpenCode installed. This is the highest-risk unknown in v1.2.

### Tool Name Translation

The mapping is already documented and validated in `ai_codebase_mentor/plugin/skills/explaining-codebase/references/codex-tools.md`:

```python
TOOL_NAME_MAP = {
    "Read": "read",
    "Write": "write",
    "Edit": "edit",
    "Bash": "bash",
    "Grep": "grep",
    "Glob": "glob",
    "WebSearch": "websearch",
    "WebFetch": "webfetch",
}
```

Tool names with path scopes (e.g., `Write(.code-wizard/**)`) need the scope preserved after lowercasing: `write(.code-wizard/**)`.

---

## PyPI Publish — Stack Additions

### Build Tooling: `build` package

**Recommended:** `pip install build` (the `build` package, not setuptools directly)

**Why `build` not `uv`:** The existing `pyproject.toml` uses setuptools as the build backend, which `build` invokes correctly via PEP 517. `uv publish` is a valid alternative but is newer and less universally adopted in GitHub Actions documentation. `build` + `pypa/gh-action-pypi-publish` is the canonical PyPA-blessed workflow as of early 2026.

**Why not twine:** `twine upload` is the legacy path. The `pypa/gh-action-pypi-publish` action handles the upload step directly — twine is not needed when using this action. Adding twine would be redundant.

**Build command:**
```bash
python -m build   # produces dist/*.tar.gz and dist/*.whl
```

This is a one-line addition to the publish workflow. No changes to `pyproject.toml` are needed — the existing setuptools config already supports it.

**Dev dependency to add:**
```toml
[project.optional-dependencies]
dev = ["pytest>=7.0", "build>=1.0"]
```

`build>=1.0` is the stable release line. Pin to `>=1.0` (released 2023) — not a specific patch to avoid over-constraining.

### GitHub Actions Workflow: `pypa/gh-action-pypi-publish`

**Confidence: HIGH** — This is the official PyPA-maintained action, stable since 2020, no known breaking changes.

**Action:** `pypa/gh-action-pypi-publish@release/v1`

Use the floating `release/v1` tag (PyPA's recommendation) rather than pinning a specific SHA — the action maintainers guarantee backward compatibility within v1.

**Authentication: Trusted Publisher (OIDC) — no API token**

PyPI Trusted Publisher lets GitHub Actions authenticate via OIDC without storing a PyPI API token in GitHub Secrets. Setup steps:
1. On PyPI: go to project → Publishing → Add a publisher → GitHub Actions (repository + workflow filename)
2. In the workflow: set `permissions: id-token: write`
3. The action handles the rest — no `PYPI_TOKEN` secret needed

**Trigger:** Semver tag push only (not every push):
```yaml
on:
  push:
    tags:
      - "v[0-9]+.[0-9]+.[0-9]+"
```

This matches `v1.2.0` but not `v1.2.0-beta.1`. If pre-release tags are needed later, extend the pattern.

### Full Publish Workflow Structure

**Confidence: HIGH** — Derived from the PyPA publish guide pattern and the existing `test-installer.yml` conventions already in this repo.

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v[0-9]+.[0-9]+.[0-9]+"

jobs:
  publish:
    name: Build and publish to PyPI
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write   # required for Trusted Publisher OIDC

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install build
        run: pip install build
      - name: Build distributions
        run: python -m build
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

**Why `environment: pypi`:** GitHub Environments let you require manual approval before publishing. Best practice for PyPI releases — prevents accidental publishes from CI noise. Create a `pypi` environment in the repo settings.

**Why ubuntu-latest only (not matrix):** Publish runs once. The test workflow already validates on ubuntu + macos. Publishing from multiple OS would produce duplicate distributions.

### pyproject.toml Changes for PyPI

Two additions needed — both are metadata, not structural changes:

```toml
[project]
# Add these fields:
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
urls = {Homepage = "https://github.com/SpillwaveSolutions/codebase-mentor"}
```

The `[project.urls]` table (or inline `urls`) enables the "Homepage" link on the PyPI project page. PyPI will reject packages without at least one URL — add it now to avoid a publish failure.

**Version field:** `version = "1.2.0"` — bump from `1.0.0`. PyPI does not allow re-uploading the same version. Set to `1.2.0` before the first publish or the tag `v1.2.0` publish will fail.

---

## What NOT to Add

| Package | Reason to exclude |
|---------|------------------|
| `PyYAML` | Frontmatter parsing is simple enough for stdlib `re` + `str.split` |
| `tomli` / `tomllib` | TOML is Codex's format (v1.3), not OpenCode's |
| `twine` | Redundant when using `pypa/gh-action-pypi-publish` |
| `uv` | Valid but not the canonical path for this project's setuptools backend |
| `packaging` | Version parsing not needed in v1.2; add only if `status` command needs semver comparison |
| `requests` / `httpx` | No HTTP calls in the converter; opencode.py is filesystem-only |
| `flit` | Project already uses setuptools; switching build backends in v1.2 adds risk for no benefit |

---

## Full Stack After v1.2

### pyproject.toml (annotated diff)

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]          # unchanged
build-backend = "setuptools.build_meta"         # unchanged

[project]
name = "ai-codebase-mentor"
version = "1.2.0"                               # CHANGE: was 1.0.0
description = "..."                             # unchanged
requires-python = ">=3.9"                       # unchanged
license = {text = "MIT"}                        # unchanged
keywords = [...]                                # unchanged
dependencies = ["click>=8.0"]                   # unchanged — no new runtime deps
classifiers = [...]                             # ADD: enables PyPI metadata
urls = {Homepage = "..."}                       # ADD: required by PyPI

[project.optional-dependencies]
dev = ["pytest>=7.0", "build>=1.0"]            # ADD: build for local dist builds

[project.scripts]                               # unchanged
[tool.setuptools.packages.find]                 # unchanged
[tool.setuptools.package-data]                  # unchanged
```

### New files

| File | Purpose |
|------|---------|
| `ai_codebase_mentor/converters/opencode.py` | OpenCode `RuntimeInstaller` subclass |
| `.github/workflows/publish-pypi.yml` | Tag-triggered publish workflow |

### Changed files

| File | Change |
|------|--------|
| `pyproject.toml` | version bump to 1.2.0, add classifiers + url |
| `ai_codebase_mentor/cli.py` | Add `"opencode": OpenCodeInstaller` to `_get_converters()` |
| `ai_codebase_mentor/__init__.py` | Bump `__version__` to `"1.2.0"` |

---

## Confidence Assessment

| Area | Confidence | Source | Notes |
|------|------------|--------|-------|
| OpenCode tool names (lowercase) | HIGH | `codex-tools.md` in this repo | Documented and cross-referenced in design spec |
| OpenCode config dir (`~/.config/opencode/`) | HIGH | `codex-tools.md` in this repo | Explicitly listed |
| OpenCode plugin manifest schema | LOW | Design spec open question | "Same schema as plugin.json?" is explicitly unresolved — must verify on a machine with OpenCode installed before implementing |
| `build` package for sdist/wheel | HIGH | PyPA standard, training data | Stable since 2018, no known breaking changes |
| `pypa/gh-action-pypi-publish@release/v1` | HIGH | Official PyPA action, widely deployed | Use `release/v1` floating tag per maintainer guidance |
| Trusted Publisher (OIDC) auth | HIGH | PyPI official feature, training data | Current best practice, replaces API tokens |
| Semver tag trigger pattern | HIGH | GitHub Actions docs pattern | Standard `v[0-9]+.[0-9]+.[0-9]+` glob |
| No new runtime deps needed | HIGH | Codebase analysis | Converter is filesystem + stdlib only |

---

## Open Questions (Must Resolve Before Implementation)

1. **OpenCode plugin manifest schema** — Is it the same JSON structure as `plugin.json` (with `runtime: "opencode"`)? Or does OpenCode use a different format entirely (e.g., a directory of markdown files, a TOML config, or no manifest at all)?
   - Resolve by: installing OpenCode locally and inspecting `~/.config/opencode/` after adding a plugin, or reading the OpenCode GitHub repo (https://github.com/sst/opencode)

2. **OpenCode install path** — Is `~/.config/opencode/plugins/codebase-wizard/` correct? OpenCode may use a subdirectory like `~/.config/opencode/agents/` or read from a different XDG path.
   - Resolve by: same approach as above

3. **PyPI project registration** — Has `ai-codebase-mentor` been registered on PyPI yet? If not, the first publish must be done manually or the Trusted Publisher must be configured before the workflow can run.
   - Resolve by: checking https://pypi.org/project/ai-codebase-mentor/

---

## Sources

- `ai_codebase_mentor/plugin/skills/explaining-codebase/references/codex-tools.md` — tool name matrix and OpenCode config dir (HIGH confidence, project source)
- `docs/superpowers/specs/2026-03-20-codebase-wizard-multi-runtime-design.md` — converter responsibilities and open questions (HIGH confidence, project spec)
- `pyproject.toml` — existing build config baseline (HIGH confidence, project source)
- `ai_codebase_mentor/converters/claude.py` — converter pattern to replicate for opencode.py (HIGH confidence, project source)
- `.github/workflows/test-installer.yml` — existing actions versions and patterns (HIGH confidence, project source)
- PyPA publish guide pattern (MEDIUM confidence, training data — verify against https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/ before implementing)
