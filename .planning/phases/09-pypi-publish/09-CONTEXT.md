# Phase 9: PyPI Publish — Context

**Gathered:** 2026-03-22
**Status:** Ready for planning
**Source:** Conversation, REQUIREMENTS.md, design spec, existing pyproject.toml

---

<domain>
## Phase Boundary

Phase 9 delivers two things:

1. **`pyproject.toml` metadata completeness** — add the fields PyPI requires for
   a valid listing: `authors`, `readme`, `classifiers`, `[project.urls]`. Bump
   version to `1.2.0` (now that opencode converter ships).

2. **`.github/workflows/publish-pypi.yml`** — GitHub Actions workflow that builds
   sdist + wheel and publishes to PyPI via Trusted Publishers (OIDC) on semver
   tag push only. No test steps (tests live in test-installer.yml).

This phase does NOT implement any new converter logic or CLI changes.

</domain>

<decisions>
## Implementation Decisions

### Version bump — Locked

`pyproject.toml` `version` field: `"1.0.0"` → `"1.2.0"`
`ai_codebase_mentor/__init__.py` `__version__`: `"1.0.0"` → `"1.2.0"`
Both must match exactly.

### pyproject.toml additions — Locked

Add these fields to the `[project]` table (current file is missing all of them):

```toml
authors = [
  {name = "Spillwave Solutions", email = "hello@spillwave.io"},
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
    "Topic :: Software Development :: Libraries :: Python Modules",
]

[project.urls]
Homepage = "https://github.com/SpillwaveSolutions/codebase-mentor"
Repository = "https://github.com/SpillwaveSolutions/codebase-mentor"
```

Also add `build` as a dev dependency (needed for publish workflow):
```toml
dev = ["pytest>=7.0", "build>=1.0"]
```

### publish-pypi.yml — Locked

File: `.github/workflows/publish-pypi.yml`

Trigger: `push: tags: ['v[0-9]+.[0-9]+.[0-9]+']` (semver tags only, no pre-release)
NOT triggered on: push to branches, pull_request, schedule.

Permissions block (required for Trusted Publishers OIDC):
```yaml
permissions:
  id-token: write
  contents: read
```

Environment: `pypi` (must match the GitHub environment configured in PyPI Trusted Publisher setup)

Steps (in order):
1. `actions/checkout@v4`
2. `actions/setup-python@v5` with `python-version: "3.11"`
3. `pip install build`
4. `python -m build` (produces `dist/` with sdist + wheel)
5. `pypa/gh-action-pypi-publish@release/v1` (no `password:` — OIDC handles auth)

No test steps. No version extraction. No Docker. No matrix.

### Tag convention — Locked

Workflow fires on `v1.2.0`, `v1.3.0`, etc.
Tag format: `v{MAJOR}.{MINOR}.{PATCH}` — must match the version in `pyproject.toml`.
Pre-release tags (`v1.2.0-alpha`, `v1.2.0rc1`) do NOT trigger the workflow.

### PyPI Trusted Publisher setup (one-time human action) — Locked

This is NOT automated — it requires a human to configure on pypi.org BEFORE
the first tag fires:
1. Create package on PyPI (or claim the name `ai-codebase-mentor`)
2. Go to the package's Publishing page → Add a Trusted Publisher
3. Set: owner=SpillwaveSolutions, repo=codebase-mentor, workflow=publish-pypi.yml, environment=pypi

This is documented in the plan as a prerequisite checkpoint — executor must
include it as a human-action task so it doesn't get skipped.

### What does NOT go in this phase — Locked

- No TestPyPI staging step
- No changelog automation
- No release notes generation
- No version bumping automation (manual bump before tagging)
- No test steps in publish workflow (handled by test-installer.yml)

### Claude's Discretion

- Exact wording of the `description` field in `pyproject.toml` (keep existing or improve slightly)
- Whether `keywords` list gets expanded for PyPI discoverability
- Exact Python version range in `requires-python` (keep `>=3.9` or narrow)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Files to modify
- `pyproject.toml` — add authors, readme, classifiers, [project.urls], bump version
- `ai_codebase_mentor/__init__.py` — bump __version__ to match

### File to create
- `.github/workflows/publish-pypi.yml` — Trusted Publisher OIDC publish workflow

### Reference (do not modify)
- `.github/workflows/test-installer.yml` — existing workflow (understand trigger pattern; publish workflow must NOT duplicate its test steps)
- `.planning/REQUIREMENTS.md` — PYPI-01 through PYPI-07

</canonical_refs>

<specifics>
## publish-pypi.yml Full Structure

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'

permissions:
  id-token: write
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

No `password:`, no `repository-url:` (defaults to production PyPI), no `skip-existing:`.

## Current pyproject.toml gaps (confirmed by reading file)

Missing fields: `authors`, `readme`, `classifiers`, `[project.urls]`
Version: `1.0.0` → needs to be `1.2.0`
Dev deps: missing `build>=1.0`

</specifics>

<deferred>
## Deferred Ideas

- TestPyPI staging workflow — not needed; Trusted Publishers works on first real publish
- Automated version bumping (bumpversion, commitizen) — future tooling decision
- Release notes in GitHub Releases — future nice-to-have
- PyPI download badge in README — post-publish addition

</deferred>

---

*Phase: 09-pypi-publish*
*Context gathered: 2026-03-22 from conversation + requirements + pyproject.toml inspection*
