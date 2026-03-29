# Codebase Wizard

## Current State: v1.0 Shipped (2026-03-29)

**Shipped:** 13 phases, 17 plans, 4079 LOC Python, 122 commits over 10 days
**Published:** `pip install ai-codebase-mentor` (v1.2.0 on PyPI)
**Next milestone:** Not yet planned — run `/gsd:new-milestone` to start

## What This Is

A multi-runtime AI plugin and Python package that transforms codebases into well-documented knowledge bases through a wizard-style Q&A interface. The plugin runs in Claude Code and OpenCode. The `ai-codebase-mentor` Python package installs the correct format for each runtime via per-runtime converters.

## Core Value

A developer can run one command and walk away with a documented codebase — without clicking "Approve" fifteen times or writing documentation by hand.

## Requirements

### Validated (v1.0)

- ✓ Core wizard skill: answer loop, Describe/Explore modes, File mode, question banks — v1.0 Phase 1
- ✓ Capture + synthesis: Agent Rulez hooks, JSON capture, /export command — v1.0 Phase 2
- ✓ Permission agents + commands: policy islands, zero-approval execution — v1.0 Phase 3
- ✓ Plugin manifest + marketplace: plugin.json, marketplace.json — v1.0 Phase 4
- ✓ Claude Code installer: global + project install/uninstall — v1.0 Phase 5
- ✓ Python package: pyproject.toml, CLI entry point, bundled plugin — v1.0 Phase 6
- ✓ CI/CD: test-installer.yml on every push — v1.0 Phase 7
- ✓ OpenCode converter: agent/command format conversion, TDD — v1.0 Phase 8
- ✓ PyPI publish: Trusted Publishers OIDC, v1.2.0 — v1.0 Phase 9
- ✓ Agent Rulez config: correct rules schema, capture-session.sh — v1.0 Phase 10
- ✓ Wizard UX: numbered options, free-text fallback, Visual Flow — v1.0 Phase 11
- ✓ E2E tests: CliRunner installer tests, failure artifact bundle — v1.0 Phase 12
- ✓ Live CLI tests: claude -p and opencode headless with fixture project — v1.0 Phase 13

### Active

- [ ] OpenCode skill activation: wizard not invoked via `opencode run` (see todo)
- [ ] Codex converter — deferred to future milestone
- [ ] Gemini converter — deferred to future milestone

### Out of Scope

- Real-time collaboration / multi-user sessions — single-developer tool
- Cloud sync of captured sessions — local-only storage
- IDE integrations (VS Code extension, etc.) — CLI only
- Automatic git commits of generated docs — user decides what to commit

## Context

Shipped v1.0 with 4079 LOC across 19 Python files and 16 plugin markdown files.
Tech stack: Python 3.11+, Click CLI, pytest, GitHub Actions CI/CD.
Agent Rulez (https://github.com/SpillwaveSolutions/agent_rulez) provides hook infrastructure.
Policy islands pattern governs permission management.

Known integration gap: OpenCode `run` command doesn't activate the codebase-wizard skill — it answers prompts directly. Hooks fire correctly but the wizard session writing logic is bypassed. Tracked as pending todo.

## Working Agreements

### Test Work Policy

A task that adds or modifies tests but does not run them is **incomplete**, not partially complete.

- Writing the test file is step 1. Running it is step 2. Both are mandatory.
- For e2e/integration/slow/live tests, step 2 means executing in the intended environment.
- If a test cannot be run, the close state must be "blocked" with the exact missing prerequisite and the command to run once unblocked.
- Skipped tests are unverified, not done.

### Postconditions for Test Tasks

Before marking any test task complete:
- [ ] Test file created or updated
- [ ] Relevant test command executed
- [ ] Result observed (pass/fail/blocked — never "skipped")
- [ ] Failures captured with logs/artifacts
- [ ] Close-out includes: exact command, result, key output line

### Run Commands

- Fast suite: `pytest`
- Integration/e2e: `scripts/run_integration_tests.sh`
- OpenCode e2e with failure artifacts: `scripts/run_opencode_e2e_with_artifacts.sh`

## Constraints

- **Platform**: Claude Code (v1.0 ✓), OpenCode (v1.0 partial — install works, skill activation pending)
- **Storage**: Local filesystem only (`.code-wizard/`)
- **Hook infrastructure**: Agent Rulez, installable without elevated permissions
- **Agent Rulez**: Hooks declared in YAML, not hardcoded in settings.json

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Approach A (monorepo + converters) | Claude format is canonical; converters generate per-runtime on install | ✓ Good — shipped v1.0 |
| Separate plugin.json and marketplace.json | Install manifest stays clean; marketplace adds discovery | ✓ Good |
| Policy islands pattern for agents | Eliminates approval fatigue; permissions declared once | ✓ Good |
| Agent Rulez for hooks (not hardcoded) | Declarative YAML config is portable and auditable | ✓ Good |
| Lazy import in `_get_converters()` | Adding new runtimes requires only adding to dict | ✓ Good |
| Two modes (Describe/Explore) | Different goals for repo owners vs newcomers | ✓ Good — both modes work |
| Numbered follow-up options (1-5) | Better UX than bare bullets, free-text fallback | ✓ Good — Phase 11 |
| Write-tool fallback for session capture | Works regardless of Agent Rulez hook state | ✓ Good — Phase 10 |

---
*Last updated: 2026-03-29 after v1.0 milestone*
