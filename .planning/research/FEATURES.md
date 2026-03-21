# Feature Landscape: v1.2 OpenCode + PyPI

**Domain:** Multi-runtime AI plugin installer (Python package)
**Milestone:** v1.2 — OpenCode converter + PyPI publish-on-tag
**Researched:** 2026-03-21
**Overall confidence:** MEDIUM (OpenCode format LOW due to no web access; PyPI HIGH from well-established practice)

---

## Research Constraints

Web search and WebFetch were unavailable during this research session (permissions denied, Brave API key not set). OpenCode format findings are derived from training data (cutoff August 2025) plus inference from the project's own spec. PyPI Trusted Publishers findings are HIGH confidence from well-established, stable practice.

**Implication:** The OpenCode format section MUST be validated against current OpenCode docs before implementation begins. The PyPI section can be implemented from this document directly.

---

## Table Stakes

Features that must work correctly for v1.2 to ship.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `opencode.py` converter: `install()` | Core v1.2 goal — OpenCode users expect `install --for opencode` to work | Medium | Depends on confirmed OpenCode install path and format |
| `opencode.py` converter: `uninstall()` | Idempotent cleanup required by RuntimeInstaller contract | Low | Must be no-op if not installed |
| `opencode.py` converter: `status()` | Required by base class; `ai-codebase-mentor status` must show opencode entry | Low | Returns `{"installed": bool, "location": str, "version": str}` |
| CLI registers `opencode` runtime | `_get_converters()` in `cli.py` must add `"opencode": OpenCodeInstaller` | Low | One-line addition to existing lazy-import dict |
| PyPI `publish-pypi.yml` workflow | `pip install ai-codebase-mentor` is the v1.2 release gate | Low-Medium | Trusted Publishers setup requires one-time PyPI config |
| Tag-triggered publish only | Publish must not fire on every push | Low | Tag pattern `v[0-9]+.[0-9]+.[0-9]+` in workflow trigger |
| `pyproject.toml` publish metadata | Authors, classifiers, URLs required for a valid PyPI listing | Low | Existing `pyproject.toml` needs `[project.urls]`, authors, classifiers |

## Differentiators

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| OpenCode tool name conversion | OpenCode uses lowercase snake_case tool names vs Claude Code's PascalCase (`Read` → `read`, `Glob` → `glob`) | Low | Simple string mapping; high value for correctness |
| `--project` flag support for OpenCode | Per-project install mirrors Claude installer; useful for monorepo setups | Low | OpenCode may support both global and local config dirs |

## Anti-Features

Features to explicitly NOT build in v1.2.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full YAML/JSON validation of agent files during conversion | Over-engineering; source files are already valid (they work in Claude Code) | Trust source files; only transform what must change for OpenCode |
| Auto-discovering OpenCode install path from running process | Fragile; platform-specific; unnecessary | Use the known conventional path `~/.config/opencode/` |
| Skills directory conversion | OpenCode format for skills is undocumented at this milestone | Convert only agents and commands; skills remain in SKILL.md format |
| Gemini or Codex work in v1.2 | Scope creep — those are v1.3 and v1.4 | Keep `_get_converters()` extension point clean for future additions |

---

## Feature 1: OpenCode Converter (`opencode.py`)

### What OpenCode Is (context)

OpenCode is an open-source AI coding tool built by the SST team. It runs in the terminal (TUI), supports multiple AI providers, and has a plugin/agent system. At training cutoff (August 2025), OpenCode was in active development and its plugin schema was evolving.

**CRITICAL OPEN QUESTION: OpenCode install path and format schema are unconfirmed. Research below represents training-data inference and must be validated against current OpenCode docs before coding begins.**

### OpenCode Plugin Format (LOW confidence — training data only)

OpenCode's plugin/rules format at training cutoff used markdown files placed in a known directory rather than a JSON manifest. The analogy to Claude Code:

| Claude Code | OpenCode (inferred) | Confidence |
|-------------|---------------------|------------|
| `~/.claude/plugins/codebase-wizard/` | `~/.config/opencode/` or `~/.opencode/` | LOW |
| `.claude-plugin/plugin.json` | No equivalent manifest (or `opencode.json`) | LOW |
| `agents/*.md` (YAML frontmatter: `name`, `allowed_tools`) | Agent/rules files in markdown format | MEDIUM |
| `commands/*.md` (YAML frontmatter: `context`, `agent`) | Similar markdown command files | MEDIUM |
| Tool name: `Read` (PascalCase) | Tool name: `read` (likely snake_case) | LOW-MEDIUM |

**What must be verified before coding:**
1. The global install path for OpenCode plugins/rules
2. Whether a manifest file (JSON or TOML) is required
3. Exact frontmatter schema for agent files (field names, allowed values)
4. Whether `allowed_tools` uses different names than Claude Code
5. Whether `context: fork` / `agent:` on commands is supported

### Two Conversion Scenarios

The converter complexity depends entirely on which scenario is true:

**Scenario A: OpenCode uses same format as Claude Code** (LOW confidence)
- Converter is trivial: copy plugin tree, update any tool name casing
- Risk: tool name casing (`Read` vs `read`) may still differ
- `opencode.py` is nearly identical to `claude.py` with a different install path

**Scenario B: OpenCode uses a different format** (MEDIUM confidence this is true)
- Converter must parse agent frontmatter, remap tool names, possibly generate a manifest
- `opencode.py` reads `agents/*.md` and `commands/*.md`, rewrites YAML frontmatter
- Higher complexity but still tractable (structured source, structured target)

**Recommendation:** Design `opencode.py` for Scenario B. If OpenCode turns out to use the same format, the converter collapses to a copy — no harm done. If it differs, we need the parsing logic. Build the harder case.

### Converter Design (Scenario B)

```python
# opencode.py — conceptual structure
class OpenCodeInstaller(RuntimeInstaller):
    TOOL_NAME_MAP = {
        "Read": "read",
        "Glob": "glob",
        "Grep": "grep",
        "Write": "write",
        "Edit": "edit",
        "Bash": "bash",
        "WebSearch": "web_search",
        "WebFetch": "web_fetch",
    }

    def install(self, source: Path, target: str = "global") -> None:
        dest = self._resolve_dest(target)
        dest.mkdir(parents=True, exist_ok=True)
        self._convert_agents(source / "agents", dest / "agents")
        self._convert_commands(source / "commands", dest / "commands")
        # skills: copy as-is (format compatible or left for v1.3+)
        self._copy_skills(source / "skills", dest / "skills")

    def _convert_agents(self, src: Path, dest: Path) -> None:
        # Parse YAML frontmatter from each *.md
        # Remap tool names in allowed_tools list
        # Write transformed frontmatter + body to dest

    def _resolve_dest(self, target: str) -> Path:
        # Global: ~/.config/opencode/plugins/codebase-wizard/
        # Project: ./.opencode/plugins/codebase-wizard/
        # MUST BE VERIFIED against current OpenCode docs
```

### Install Path (LOW confidence — must verify)

Likely candidates based on OpenCode conventions observed at training cutoff:

| Scope | Path | Notes |
|-------|------|-------|
| Global | `~/.config/opencode/` | XDG-compliant; SST tends toward this |
| Project | `.opencode/` | Project-local override |

**Validation instruction:** Before writing `_resolve_dest()`, check OpenCode docs or source for the canonical plugin/rules install path.

### Dependencies on Existing Infrastructure

`opencode.py` slots directly into the existing `RuntimeInstaller` ABC:

| Dependency | Status | Notes |
|------------|--------|-------|
| `RuntimeInstaller` ABC in `base.py` | Already shipped (v1.0) | No changes needed |
| `_read_version()` helper in `base.py` | Available but may not apply | OpenCode may not have a plugin.json; version read may need a different strategy |
| `_get_converters()` in `cli.py` | Needs one-line addition | `"opencode": OpenCodeInstaller` added to the dict |
| `--project` flag logic in CLI | Already works | OpenCode installer just needs to use `target` param |
| YAML frontmatter parsing | NOT in existing codebase | Need `python-frontmatter` or `PyYAML`; add to `pyproject.toml` dependencies |

**New dependency:** YAML frontmatter parsing. The existing code has no YAML parser. Options:
- `python-frontmatter` (dedicated library, clean API, ~5KB) — recommended
- `PyYAML` (lower-level, already common) — workable but more boilerplate
- Manual string parsing — fragile, avoid

Add to `pyproject.toml`: `"python-frontmatter>=1.0"` (or `PyYAML>=6.0` as fallback).

---

## Feature 2: PyPI Publish-on-Tag (`publish-pypi.yml`)

### Approach: Trusted Publishers (HIGH confidence — established best practice)

PyPI Trusted Publishers uses OpenID Connect (OIDC) to authenticate GitHub Actions workflows directly against PyPI — no API token, no long-lived secret stored in GitHub.

**This is the current recommended approach as of 2023 and is firmly standard practice by 2026.** The API token approach is deprecated for new projects.

### One-Time Setup (PyPI side)

Before the workflow fires the first time, perform these steps on PyPI:

1. Log into pypi.org → navigate to the `ai-codebase-mentor` project page (create it first with a manual upload if needed, OR use "pending publisher" feature to pre-configure before first release)
2. Go to: Publishing → Add a new publisher
3. Select: GitHub Actions
4. Fill in:
   - GitHub repository owner: `SpillwaveSolutions`
   - Repository name: `codebase-mentor`
   - Workflow filename: `publish-pypi.yml`
   - Environment name: `pypi` (optional but recommended)

**Pending Publisher (recommended for first publish):** PyPI supports configuring the Trusted Publisher before the package exists on PyPI. This avoids a chicken-and-egg problem where you can't configure publishing without the package, but can't create the package without publishing.

### Workflow YAML Structure (HIGH confidence)

```yaml
# .github/workflows/publish-pypi.yml
name: Publish to PyPI

on:
  push:
    tags:
      - "v[0-9]+.[0-9]+.[0-9]+"   # fires on semver tags: v1.2.0, v1.2.1, etc.
                                    # does NOT fire on: v1.2.0-rc1, v1.2.0.post1

jobs:
  publish:
    name: Build and publish to PyPI
    runs-on: ubuntu-latest
    environment: pypi               # matches environment name configured in PyPI

    permissions:
      id-token: write               # required for OIDC Trusted Publisher auth
      contents: read

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install build tools
        run: pip install build

      - name: Build sdist and wheel
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # No `with: password:` needed — OIDC handles auth
```

**Key design decisions in this workflow:**

| Decision | Rationale |
|----------|-----------|
| Tag pattern `v[0-9]+.[0-9]+.[0-9]+` | Matches semver tags only; excludes pre-release suffixes (`-rc1`) and push events on branches |
| `environment: pypi` | Adds a GitHub environment gate (optional approval); must match PyPI Trusted Publisher config |
| `id-token: write` | Required permission for OIDC token generation; without it, Trusted Publisher auth fails silently |
| `python -m build` (not `setup.py sdist bdist_wheel`) | Modern build frontend; works with `pyproject.toml` + setuptools backend already configured |
| `pypa/gh-action-pypi-publish@release/v1` | Official PyPA action; `@release/v1` tracks the latest stable release automatically |

### `pyproject.toml` Additions for PyPI Listing (MEDIUM confidence — standard fields)

The existing `pyproject.toml` is minimal. A clean PyPI listing requires:

```toml
[project]
# Add these fields to existing [project] section:
authors = [
  {name = "Spillwave Solutions", email = "hello@spillwave.io"}
]
readme = "README.md"
classifiers = [
  "Development Status :: 4 - Beta",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: MIT License",
  "Programming Language :: Python :: 3",
  "Programming Language :: Python :: 3.9",
  "Programming Language :: Python :: 3.10",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Topic :: Software Development :: Documentation",
  "Topic :: Utilities",
]

[project.urls]
Homepage = "https://github.com/SpillwaveSolutions/codebase-mentor"
Repository = "https://github.com/SpillwaveSolutions/codebase-mentor"
"Bug Tracker" = "https://github.com/SpillwaveSolutions/codebase-mentor/issues"
```

Also add `build` to dev dependencies so local builds work:
```toml
[project.optional-dependencies]
dev = ["pytest>=7.0", "build>=1.0"]
```

### Relationship to Existing `test-installer.yml`

The publish workflow is separate from and does not replace `test-installer.yml`. The recommended pattern:

1. `test-installer.yml` fires on every push and PR (already exists, already passes)
2. `publish-pypi.yml` fires only on semver tags — and only if tests have already passed

Consider adding a dependency: the publish job can require the test workflow to pass first. However, the simplest v1.2 implementation is two independent workflows; adding workflow dependency (via `workflow_run` trigger) adds complexity and can be deferred.

---

## Feature Dependencies

```
opencode.py converter
  → requires: RuntimeInstaller ABC (base.py) [already shipped]
  → requires: YAML frontmatter parser (new dependency)
  → requires: confirmed OpenCode install path [MUST VERIFY]
  → requires: confirmed OpenCode agent/command schema [MUST VERIFY]
  → unlocks: cli.py opencode entry in _get_converters()
  → unlocks: test-installer.yml opencode test job

publish-pypi.yml
  → requires: pyproject.toml metadata additions (classifiers, authors, URLs)
  → requires: PyPI account with Trusted Publisher configured (one-time human step)
  → requires: GitHub environment "pypi" created in repo settings (one-time human step)
  → independent of: opencode.py converter
```

---

## MVP Recommendation

Prioritize in this order:

1. **Verify OpenCode format first** — do NOT write `opencode.py` until the install path and agent schema are confirmed. Coding against wrong assumptions creates a rewrite.
2. **PyPI metadata + workflow** — can be developed in parallel with OpenCode research. No external unknowns. Purely additive to `pyproject.toml` and a new workflow file.
3. **`opencode.py` converter** — implement once format is confirmed. Start with Scenario B (format conversion) even if Scenario A (copy-only) turns out to be true.
4. **Add opencode to `cli.py` `_get_converters()`** — one-line change, done last after converter is tested.

**Defer:**
- `--project` flag for OpenCode: Include if OpenCode clearly supports a per-project install path; defer if the install convention is global-only.
- Extending `test-installer.yml` with OpenCode tests: Requires OpenCode to be installable on GitHub Actions runner. May need to add OpenCode install step in CI.

---

## Phase-Specific Notes for Roadmap

| Phase | Task | Complexity | Blocker |
|-------|------|------------|---------|
| v1.2 Phase 01 | OpenCode format research + `opencode.py` | Medium | Must verify format before coding |
| v1.2 Phase 01 | Add YAML parser dependency to `pyproject.toml` | Low | None |
| v1.2 Phase 02 | `pyproject.toml` metadata additions | Low | None |
| v1.2 Phase 02 | `publish-pypi.yml` workflow | Low | Trusted Publisher one-time setup (human step) |
| v1.2 Phase 02 | GitHub environment "pypi" creation | Low | Human step in GitHub repo settings |

---

## Sources

| Finding | Source | Confidence |
|---------|--------|------------|
| OpenCode install path (`~/.config/opencode/`) | Training data (August 2025 cutoff) — NOT verified | LOW |
| OpenCode plugin schema (Scenario A vs B) | Training data inference; listed as open question in project spec | LOW |
| OpenCode tool names (snake_case) | Training data inference from SST/OpenCode conventions | LOW |
| PyPI Trusted Publishers approach | Established practice since 2023; PyPA official documentation | HIGH |
| `pypa/gh-action-pypi-publish@release/v1` action | PyPA official action, in production use since 2022 | HIGH |
| `id-token: write` permission required | OIDC standard requirement, documented in GitHub Actions OIDC docs | HIGH |
| `python -m build` build frontend | PEP 517/518 standard since 2021, universally recommended | HIGH |
| `pyproject.toml` classifier and URL fields | PyPI packaging specification (stable) | HIGH |

---

## Gaps to Address Before Coding

1. **OpenCode install path** — run `opencode --help` or check OpenCode docs/source for `~/.config/opencode/` vs `~/.opencode/` vs other path
2. **OpenCode manifest requirement** — does OpenCode need a `plugin.json` or `opencode.json` in the plugin root, or is directory structure alone sufficient?
3. **OpenCode agent frontmatter schema** — exact field names: is it `allowed_tools:` (same as Claude Code) or different? Is `context: fork` supported?
4. **OpenCode version at v1.2 target** — what OpenCode version is this converter targeting? Format may differ between early and recent OpenCode versions.
5. **PyPI account ownership** — confirm `ai-codebase-mentor` package name is available on PyPI (or already claimed) before configuring Trusted Publisher
