---
phase: 09-pypi-publish
plan: 01
subsystem: infra
tags: [pypi, packaging, github-actions, oidc, trusted-publishers, semver]

# Dependency graph
requires:
  - phase: 08-opencode-converter
    provides: "Completed converter implementation that bumped the project to v1.2 milestone"
provides:
  - "pyproject.toml with complete PyPI metadata (authors, readme, classifiers, urls)"
  - "version 1.2.0 in pyproject.toml and __init__.py"
  - "publish-pypi.yml GitHub Actions workflow with Trusted Publisher OIDC"
  - "Package builds cleanly as sdist and wheel"
affects:
  - "PyPI — once tag v1.2.0 is pushed and Trusted Publisher is configured"

# Tech tracking
tech-stack:
  added: [build>=1.0, pypa/gh-action-pypi-publish@release/v1]
  patterns:
    - "Trusted Publisher OIDC — no PYPI_TOKEN secret; publisher configured once on pypi.org"
    - "Semver tag-only publish — workflow fires only on v[0-9]+.[0-9]+.[0-9]+ tags"
    - "Publish workflow is checkout -> build -> publish only (no test duplication)"

key-files:
  created:
    - .github/workflows/publish-pypi.yml
  modified:
    - pyproject.toml
    - ai_codebase_mentor/__init__.py

key-decisions:
  - "Publish uses Trusted Publishers OIDC — no PYPI_TOKEN secret required; cleaner CI setup"
  - "Publish workflow fires on semver tags only — test-installer.yml owns all testing"
  - "No TestPyPI staging — publish goes directly to production PyPI per v1.2 out-of-scope list"

patterns-established:
  - "Publish workflow pattern: semver tag push -> checkout -> build (pip install build && python -m build) -> pypa/gh-action-pypi-publish@release/v1"
  - "GitHub environment 'pypi' must exist and match PyPI Trusted Publisher environment field"

requirements-completed: [PYPI-01, PYPI-02, PYPI-03, PYPI-04, PYPI-05, PYPI-06, PYPI-07]

# Metrics
duration: 2min
completed: 2026-03-22
---

# Phase 9 Plan 1: PyPI Publish Summary

**pyproject.toml enriched with PyPI metadata (authors, classifiers, urls), version bumped to 1.2.0, and publish-pypi.yml workflow added using Trusted Publisher OIDC — no PYPI_TOKEN needed; fires on semver tags only**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-22T14:42:52Z
- **Completed:** 2026-03-22T14:44:43Z
- **Tasks:** 3 of 4 automated (Task 4 is human-action checkpoint)
- **Files modified:** 3

## Accomplishments

- Version bumped to 1.2.0 in both pyproject.toml and ai_codebase_mentor/__init__.py
- pyproject.toml enriched with authors, readme, 9 classifiers, [project.urls], and build>=1.0 dev dep
- publish-pypi.yml workflow created with OIDC Trusted Publisher auth, semver tag trigger, zero test steps
- Package builds cleanly producing ai_codebase_mentor-1.2.0.tar.gz and ai_codebase_mentor-1.2.0-py3-none-any.whl

## Task Commits

Each automated task was committed atomically:

1. **Task 1: Bump version and add pyproject.toml metadata** - `3dc0377` (feat)
2. **Task 2: Create publish-pypi.yml workflow** - `209ba54` (feat)
3. **Task 3: Verify package builds cleanly** - no commit (verification-only task; no files changed)
4. **Task 4: Configure Trusted Publisher on pypi.org** - CHECKPOINT (human-action required)

## Files Created/Modified

- `pyproject.toml` - Version 1.2.0; added authors, readme, classifiers, [project.urls], build dev dep
- `ai_codebase_mentor/__init__.py` - __version__ bumped from 1.0.0 to 1.2.0
- `.github/workflows/publish-pypi.yml` - Trusted Publisher OIDC publish workflow (created)

## Decisions Made

- Trusted Publisher OIDC over PYPI_TOKEN secret: follows pypa best practice, no secret rotation needed
- Semver-only trigger `v[0-9]+.[0-9]+.[0-9]+` to prevent pre-release or branch pushes from publishing
- No TestPyPI stage: per locked decision in 09-CONTEXT.md, publish goes directly to production PyPI
- environment: pypi in workflow matches the GitHub environment name required by Trusted Publisher config

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Build produced `SetuptoolsDeprecationWarning` about `project.license` as TOML table format and `License :: OSI Approved :: MIT License` classifier. These are deprecation warnings (not errors), valid until 2027, and the `license = {text = "MIT"}` format was in the pre-existing pyproject.toml. Changing it was explicitly out of scope per the plan's "Do NOT change" instruction. Noted for future maintenance.

## User Setup Required

**External services require manual configuration before pushing v1.2.0 tag.**

Complete these steps (Task 4 checkpoint):

**On pypi.org:**
1. Log in at https://pypi.org
2. If package does not exist yet, go to Publishing > Add a new pending publisher:
   - PyPI project name: `ai-codebase-mentor`
   - Owner: `SpillwaveSolutions`
   - Repository: `codebase-mentor`
   - Workflow name: `publish-pypi.yml`
   - Environment name: `pypi`
3. If package already exists, go to package > Settings > Publishing > Add publisher with same values

**On GitHub:**
4. Go to https://github.com/SpillwaveSolutions/codebase-mentor/settings/environments
5. Create environment named `pypi`

After both are configured, push tag `v1.2.0` to trigger the publish workflow.

## Next Phase Readiness

- All automated setup is complete — pyproject.toml metadata is correct, workflow is correct, package builds
- Blocked on human action: Trusted Publisher must be configured on pypi.org before the first tag push
- Once checkpoint Task 4 is confirmed, push `git tag v1.2.0 && git push origin v1.2.0` to publish

---
*Phase: 09-pypi-publish*
*Completed: 2026-03-22*
