# Roadmap: Codebase Wizard

## Overview

Build a Claude Code skill + plugin that transforms codebases into well-documented knowledge bases through a wizard-style Q&A interface, with two modes (Describe/Explore), auto-captured sessions, on-demand synthesis, and pre-authorized agents for zero-approval execution.

## Phases

- [ ] **Phase 1: Core Wizard Skill** - Answer loop, Describe/Explore modes, File mode, question banks
- [ ] **Phase 2: Capture + Synthesis** - Agent Rulez hooks, JSON capture, /export command, synthesis pipeline
- [ ] **Phase 3: Permission Agents + Commands** - Policy island agents, /setup command, multi-platform codex-tools

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
- [ ] 03-01: Agent definitions and policy island setup
- [ ] 03-02: Commands and multi-platform support

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Wizard Skill | 0/1 | In progress | - |
| 2. Capture + Synthesis | 0/2 | Not started | - |
| 3. Permission Agents + Commands | 0/2 | Not started | - |
