# Roadmap: Codebase Wizard

## Overview

Build a Claude Code skill + plugin that transforms codebases into well-documented knowledge bases through a wizard-style Q&A interface, with two modes (Describe/Explore), auto-captured sessions, on-demand synthesis, and pre-authorized agents for zero-approval execution. Delivered as a multi-runtime Python package (`ai-codebase-mentor`) with per-runtime converters that transform the Claude Code plugin format into OpenCode, Codex, and Gemini formats on install.

**Milestone roadmap:** v1.0 (Claude Code) → v1.2 (OpenCode + PyPI) → v1.3 (Codex subagents) → v1.4 (Gemini) → v1.5 (LangChain DeepAgent standalone)

**Design spec:** `docs/superpowers/specs/2026-03-20-codebase-wizard-multi-runtime-design.md`

## Phases

- [x] **Phase 1: Core Wizard Skill** - Answer loop, Describe/Explore modes, File mode, question banks (completed 2026-03-19)
- [x] **Phase 2: Capture + Synthesis** - Agent Rulez hooks, JSON capture, /export command, synthesis pipeline (completed 2026-03-20)
- [x] **Phase 3: Permission Agents + Commands** - Policy island agents, /codebase-wizard command, multi-platform codex-tools (completed 2026-03-20)
- [x] **Phase 4: Plugin Manifest + Marketplace** - plugin.json and marketplace.json finalized (completed 2026-03-20)
- [x] **Phase 5: Claude Code Install/Uninstall** - claude.py converter, global + project install, clean uninstall (completed 2026-03-20)
- [x] **Phase 6: Python Package (Claude-only)** - pyproject.toml, cli.py, bundled plugin, pip install -e . (completed 2026-03-20)
- [x] **Phase 7: GitHub Actions Test Workflow** - test-installer.yml, smoke tests on push, no PyPI publish (completed 2026-03-20)
- [x] **Phase 8: OpenCode Converter** - opencode.py converter, agent/command format conversion, TDD test suite, CLI wiring (completed 2026-03-22)
- [x] **Phase 9: PyPI Publish** - pyproject.toml metadata completeness, publish-pypi.yml workflow, Trusted Publishers OIDC (completed 2026-03-22)

## Phase Details

### Phase 1: Core Wizard Skill
**Goal**: Build the core wizard skill with answer loop, mode detection, question banks, and File mode so the explainer works for codebases, markdown files, and any artifact through a conversational Q&A interface.
**Depends on**: Nothing (first phase)
**Requirements**: Two-mode wizard (Describe/Explore), Answer loop with code-block anchors, File mode, Question banks, Mode detection
**Success Criteria** (what must be TRUE):
  1. Running `--describe` walks repo owner through Q&A and produces CODEBASE.md
  2. Running `--explore` gives a learning-order tour to a new developer
  3. Running `--file <path>` walks through any markdown file section-by-section
  4. Every answer shows a code block with anchor before any explanation
  5. Every answer ends with 2-3 specific follow-up options
**Plans**: 1 plan

Plans:
- [ ] 01-01: Core wizard skill — answer loop, question banks, file mode, updated SKILL.md

### Phase 2: Capture + Synthesis
**Goal**: Auto-capture all Q&A to raw JSON/YAML via Agent Rulez hooks; provide /export command to synthesize raw logs into SESSION-TRANSCRIPT.md and CODEBASE.md.
**Depends on**: Phase 1
**Requirements**: Agent Rulez integration, /setup command, /export command, raw JSON storage, synthesis pipeline
**Success Criteria** (what must be TRUE):
  1. Sessions auto-captured to .claude/code-wizard/ or .code-wizard/ without user action
  2. /export produces SESSION-TRANSCRIPT.md and structured CODEBASE.md from raw logs
  3. /setup installs Agent Rulez and writes settings.local.json permissions
**Plans**: TBD

Plans:
- [ ] 02-01: Agent Rulez integration and capture hooks
- [ ] 02-02: Export command and synthesis pipeline

### Phase 3: Permission Agents + Commands
**Goal**: Ship pre-authorized agent definitions (policy islands) that eliminate the approval loop, plus /codebase-wizard-export and /setup commands, and codex-tools.md for multi-platform support.
**Depends on**: Phase 2
**Requirements**: Policy island agents, /setup command, /export command, codex-tools.md
**Success Criteria** (what must be TRUE):
  1. Running /setup once eliminates all "May I?" prompts for subsequent wizard sessions
  2. Agents cover: file read/write, bash scan scripts, git read ops
  3. Multi-platform support via codex-tools.md
**Plans**: TBD

Plans:
- [x] 03-01: Policy island agent, /codebase-wizard command, codex-tools matrix, platform detection in setup.sh

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Wizard Skill | 1/1 | Complete | 2026-03-19 |
| 2. Capture + Synthesis | 1/1 | Complete | 2026-03-20 |
| 3. Permission Agents + Commands | 1/1 | Complete | 2026-03-20 |
| 4. Plugin Manifest + Marketplace | 1/1 | Complete | 2026-03-20 |
| 5. Claude Code Install/Uninstall | 2/2 | Complete | 2026-03-20 |
| 6. Python Package (Claude-only) | 2/2 | Complete | 2026-03-20 |
| 7. GitHub Actions Test Workflow | 1/1 | Complete | 2026-03-20 |
| 8. OpenCode Converter | 2/2 | Complete   | 2026-03-22 |
| 9. PyPI Publish | 1/1 | Complete   | 2026-03-22 |

### Phase 4: Claude Code plugin manifest and marketplace listing

**Goal:** Finalize the Claude Code plugin manifest (`plugin.json`) and create `marketplace.json` so the plugin has correct metadata for packaging, installation, and marketplace discovery. This is the metadata gate — no installer code, just valid manifest structure that Phase 5 (installer) and Phase 6 (Python package) consume verbatim.
**Requirements**: MANIFEST-01 (plugin.json complete), MANIFEST-02 (marketplace.json created), MANIFEST-03 (metadata finalized and consistent)
**Depends on:** Phase 3
**Plans:** 1 plan

Plans:
- [x] 04-01-PLAN.md — Finalize plugin.json and create marketplace.json

### Phase 5: Local and global Claude Code plugin install and uninstall

**Goal:** Implement the Claude Code runtime installer as a Python module (`ai_codebase_mentor/converters/claude.py`). Supports global install (`~/.claude/plugins/codebase-wizard/`) and per-project install (`./plugins/codebase-wizard/`). Supports clean uninstall. Implements the RuntimeInstaller base class interface from the design spec.
**Requirements**: CLAUDE-INSTALL-01 (global install), CLAUDE-INSTALL-02 (project install), CLAUDE-INSTALL-03 (clean uninstall), CLAUDE-INSTALL-04 (status reporting)
**Depends on:** Phase 4
**Plans:** 2 plans

Plans:
- [x] 05-01-PLAN.md — Package skeleton and RuntimeInstaller base class (wave 1)
- [x] 05-02-PLAN.md — ClaudeInstaller implementation with TDD test suite (wave 2)

### Phase 6: Python package for Claude Code installer (Claude-only, not on PyPI)

**Goal:** Create the ai-codebase-mentor Python package structure: pyproject.toml, ai_codebase_mentor/ package with cli.py entry point, base.py RuntimeInstaller class, bundled plugin copy, and MANIFEST.in. Wire the Claude converter (Phase 5) to the CLI. Package is installable locally via pip install -e . but NOT published to PyPI in this phase.
**Requirements**: PKG-01 (pyproject.toml with entry point), PKG-02 (RuntimeInstaller base class), PKG-03 (bundled plugin copy), PKG-04 (cli.py with four subcommands), PKG-05 (pip install -e . works)
**Depends on:** Phase 5
**Plans:** 2 plans

Plans:
- [x] 06-01-PLAN.md — Package scaffold: pyproject.toml, MANIFEST.in, __init__.py, converters/base.py, bundled plugin (wave 1)
- [x] 06-02-PLAN.md — CLI wiring: cli.py with install/uninstall/status/version, wired to ClaudeInstaller (wave 2)

### Phase 7: GitHub Actions installer test workflow (no PyPI publish)

**Goal:** Create the GitHub Actions workflow that installs `ai-codebase-mentor` from source and runs install/uninstall/status smoke tests against it on every push, gating Milestone 1 (v1.0). PyPI publish is explicitly excluded.
**Requirements**: GH-ACTIONS-01 (workflow triggers on push), GH-ACTIONS-02 (matrix: ubuntu-latest + macos-latest, Python 3.11), GH-ACTIONS-03 (steps: install, verify files, status, uninstall, verify removed, status; no secrets)
**Depends on:** Phase 6
**Plans:** 1 plan

Plans:
- [x] 07-01-PLAN.md — GitHub Actions test-installer workflow (install/uninstall/status, no PyPI publish)

### Phase 8: OpenCode Converter

**Goal:** Implement `ai_codebase_mentor/converters/opencode.py` — the install-time converter that reads the bundled Claude plugin source and generates OpenCode-native files at `~/.config/opencode/codebase-wizard/` (global) or `./.opencode/codebase-wizard/` (project). Wire the converter into the CLI alongside the existing Claude installer.
**Depends on:** Phase 7
**Requirements**: OPENCODE-01, OPENCODE-02, OPENCODE-03, OPENCODE-04, OPENCODE-05, OPENCODE-06, OPENCODE-07, OPENCODE-08, OPENCODE-09, OPENCODE-10, OPENCODE-11, OPENCODE-12, OPENCODE-13
**Success Criteria** (what must be TRUE):
  1. `ai-codebase-mentor install --for opencode` writes converted agent, command, and skill files to `~/.config/opencode/codebase-wizard/` with no manual steps
  2. Agent files in the output directory use `tools:` (lowercase object) instead of `allowed_tools:` (PascalCase array), with `AskUserQuestion` mapped to `question` and the other four special mappings applied
  3. Agent frontmatter has `name:` field removed and named colors converted to hex values
  4. Output directory contains a `command/` directory (singular) rather than `commands/`, with all three command files present and `~/.claude` paths rewritten to `~/.config/opencode`
  5. `opencode.json` is written (or merged) in the install directory pre-authorizing file access so no per-file permission prompts appear during wizard sessions
  6. `ai-codebase-mentor uninstall --for opencode` removes the install directory cleanly; a second uninstall is a no-op
  7. `ai-codebase-mentor status` reports OpenCode install state alongside Claude install state
  8. `ai-codebase-mentor install --for all` includes OpenCode in the runtime iteration
  9. All 13 test cases in `tests/test_opencode_installer.py` pass
**Plans**: 2 plans

Plans:
- [x] 08-01-PLAN.md — OpenCode converter implementation with TDD (opencode.py + tests/test_opencode_installer.py)
- [x] 08-02-PLAN.md — Wire OpenCode converter into CLI — `--for opencode`, `--for all`, status reporting

### Phase 9: PyPI Publish

**Goal:** Finalize `pyproject.toml` metadata so the PyPI listing is complete, bump version to `1.2.0`, and create `.github/workflows/publish-pypi.yml` — a GitHub Actions workflow that publishes to PyPI on semver tag push using Trusted Publishers (OIDC), with no `PYPI_TOKEN` secret required.
**Depends on:** Phase 8
**Requirements**: PYPI-01, PYPI-02, PYPI-03, PYPI-04, PYPI-05, PYPI-06, PYPI-07
**Success Criteria** (what must be TRUE):
  1. Pushing a `v1.2.0` tag triggers `publish-pypi.yml` and no other workflow
  2. The workflow authenticates to PyPI via OIDC (no `PYPI_TOKEN` secret in the repo)
  3. The workflow builds an sdist and wheel via `python -m build` and uploads both via `pypa/gh-action-pypi-publish`
  4. `pyproject.toml` contains `authors`, `readme`, `classifiers`, and `[project.urls]` (Homepage + Repository); `version` is `1.2.0`
  5. Version in `pyproject.toml` matches `__version__` in `ai_codebase_mentor/__init__.py`
  6. After publish, `pip install ai-codebase-mentor` installs from PyPI and `ai-codebase-mentor --version` outputs `1.2.0`
  7. `publish-pypi.yml` contains no test steps — testing remains the responsibility of `test-installer.yml`
**Plans**: 1 plan

Plans:
- [x] 09-01: pyproject.toml metadata + publish-pypi.yml workflow (version bump to 1.2.0, OIDC publish)

### Phase 10: Fix Agent Rulez config and add session capture

**Goal:** Rewrite agent-rulez-sample.yaml with correct rules: schema (block rules + run: capture-session rule), fix setup.sh (replace rulez hook add with rulez install, deploy capture-session.sh), create capture-session.sh that reads PostToolUse JSON from stdin and appends to .code-wizard/sessions/{session_id}.json, add Write-tool fallback session capture instruction to SKILL.md Answer Loop.
**Requirements**: RULEZ-01 (correct YAML schema with rules: key), RULEZ-02 (setup.sh uses rulez install and deploys capture script), RULEZ-03 (capture-session.sh reads PostToolUse stdin JSON), RULEZ-04 (SKILL.md Write-tool fallback for session capture)
**Depends on:** Phase 9
**Plans:** 1/1 plans complete

Plans:
- [ ] 10-01-PLAN.md — Fix agent-rulez-sample.yaml, setup.sh, create capture-session.sh, add SKILL.md Write fallback

### Phase 11: Wizard UX improvements: numbered next-options, free-text fallback, and visual flow diagram option in explore mode

**Goal:** Update the wizard Answer Loop to use numbered follow-up options (1-5) instead of bare bullets, add a free-text escape hatch after every option block, and add a Visual Flow diagram option type for pipeline/orchestration explanations in explore mode. Sync changes to SESSION-TRANSCRIPT export template and bundled plugin copy.
**Requirements**: UX-01 (numbered options + free-text fallback in all Next blocks), UX-02 (Visual Flow option type with ASCII diagram format for pipeline contexts)
**Depends on:** Phase 10
**Plans:** 1/1 plans complete

Plans:
- [ ] 11-01-PLAN.md — Numbered next-options, free-text fallback, Visual Flow option in SKILL.md + export template sync

### Phase 12: E2E integration tests for OpenCode and Claude installer: temp dir tests with sample plugin files, verify install works end-to-end, analyze and fix current install failures

**Goal:** Fix the context:fork silent drop bug (map to subtask:true in opencode.json) and add E2E integration tests that exercise the full CLI install/uninstall/status workflow via CliRunner against temp directories, verifying correct file output for both OpenCode and Claude runtimes.
**Requirements**: E2E-01, E2E-02, E2E-03, E2E-04, E2E-05, E2E-06, E2E-07, E2E-08, E2E-09, E2E-10
**Depends on:** Phase 11
**Plans:** 2/2 plans complete

Plans:
- [ ] 12-01-PLAN.md — TDD: context:fork to subtask:true fix in opencode.py (RED tests then GREEN implementation)
- [ ] 12-02-PLAN.md — E2E CliRunner integration tests + todo cleanup

### Phase 13: live wizard CLI integration tests — claude -p and opencode headless invocation with sample fixture project, verify .code-wizard/docs output and hook files

**Goal:** Create live E2E integration tests that invoke `claude -p` and `opencode run` in headless mode against a sample fixture project, verifying that the codebase-wizard skill produces SESSION-TRANSCRIPT.md output with expected structural content. Tests are marked @pytest.mark.slow and skip gracefully when auth is not available.
**Requirements**: TBD (self-describing test phase — no formal requirement IDs)
**Depends on:** Phase 12
**Plans:** 1/1 plans complete

Plans:
- [ ] 13-01-PLAN.md — Fixture project, slow marker config, and live test_wizard_live.py with claude/opencode tests
