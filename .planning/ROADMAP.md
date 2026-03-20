# Roadmap: Codebase Wizard

## Overview

Build a Claude Code skill + plugin that transforms codebases into well-documented knowledge bases through a wizard-style Q&A interface, with two modes (Describe/Explore), auto-captured sessions, on-demand synthesis, and pre-authorized agents for zero-approval execution. Delivered as a multi-runtime Python package (`ai-codebase-mentor`) with per-runtime converters that transform the Claude Code plugin format into OpenCode, Codex, and Gemini formats on install.

**Milestone roadmap:** v1.0 (Claude Code) → v1.2 (OpenCode + PyPI) → v1.3 (Codex subagents) → v1.4 (Gemini) → v1.5 (LangChain DeepAgent standalone)

**Design spec:** `docs/superpowers/specs/2026-03-20-codebase-wizard-multi-runtime-design.md`

## Phases

- [x] **Phase 1: Core Wizard Skill** - Answer loop, Describe/Explore modes, File mode, question banks (completed 2026-03-19)
- [x] **Phase 2: Capture + Synthesis** - Agent Rulez hooks, JSON capture, /export command, synthesis pipeline (completed 2026-03-20)
- [x] **Phase 3: Permission Agents + Commands** - Policy island agents, /codebase-wizard command, multi-platform codex-tools (completed 2026-03-20)

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
