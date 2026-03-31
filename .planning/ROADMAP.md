# Roadmap: Codebase Wizard

## Milestones

- ✅ **v1.0 MVP** - Phases 1-13 (shipped 2026-03-29)
- 🚧 **v1.3 Gemini CLI Converter** - Phases 14-16 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-13) — SHIPPED 2026-03-29</summary>

### Phase 1: Core Wizard Skill
**Goal**: Users can run the codebase wizard in Describe and Explore modes
**Plans**: 1 plan

Plans:
- [x] 01-01: Answer loop, mode detection, question banks, file mode

### Phase 2: Capture + Synthesis
**Goal**: Sessions are captured and exported as structured documents
**Plans**: 1 plan

Plans:
- [x] 02-01: Agent Rulez hooks, JSON capture, /export command

### Phase 3: Permission Agents + Commands
**Goal**: Users can run wizard with zero approval prompts via policy islands
**Plans**: 1 plan

Plans:
- [x] 03-01: Policy islands, context:fork, /codebase-wizard command

### Phase 4: Plugin Manifest + Marketplace
**Goal**: Plugin is installable and discoverable via plugin.json and marketplace.json
**Plans**: 1 plan

Plans:
- [x] 04-01: plugin.json, marketplace.json, cross-file consistency

### Phase 5: Claude Code Installer
**Goal**: Users can install and uninstall the plugin globally or per-project
**Plans**: 1 plan

Plans:
- [x] 05-01: Global + project install/uninstall for Claude Code

### Phase 6: Python Package
**Goal**: Users can install the package from PyPI and run the CLI
**Plans**: 1 plan

Plans:
- [x] 06-01: pyproject.toml, CLI entry point, bundled plugin

### Phase 7: CI/CD
**Goal**: Every push is automatically tested in GitHub Actions
**Plans**: 1 plan

Plans:
- [x] 07-01: test-installer.yml workflow

### Phase 8: OpenCode Converter
**Goal**: Users can install the plugin for OpenCode via `--for opencode`
**Plans**: 2 plans

Plans:
- [x] 08-01: opencode.py TDD — 13-case test suite, GREEN
- [x] 08-02: CLI wiring — --for opencode, --for all, status

### Phase 9: PyPI Publish
**Goal**: Package is published to PyPI as v1.2.0 via OIDC
**Plans**: 1 plan

Plans:
- [x] 09-01: publish-pypi.yml, Trusted Publishers OIDC, v1.2.0

### Phase 10: Agent Rulez Config Fix + Session Capture
**Goal**: Agent Rulez hooks fire correctly and sessions are captured to disk
**Plans**: 1 plan

Plans:
- [x] 10-01: rules: schema fix, capture-session.sh, Write-tool fallback

### Phase 11: Wizard UX Improvements
**Goal**: Wizard always presents numbered options and offers Visual Flow diagrams
**Plans**: 1 plan

Plans:
- [x] 11-01: Numbered next-options, free-text fallback, Visual Flow

### Phase 12: E2E Installer Tests
**Goal**: CliRunner tests verify install/uninstall works end-to-end in temp dirs
**Plans**: 2 plans

Plans:
- [x] 12-01: context:fork subtask mapping, OpenCode E2E fixtures
- [x] 12-02: test_e2e_installer.py — 9 CliRunner tests, all pass

### Phase 13: Live Wizard CLI Integration Tests
**Goal**: Live claude and opencode headless invocations confirm wizard output
**Plans**: 1 plan

Plans:
- [x] 13-01: Fixture project, test_wizard_live.py, 5 slow tests

</details>

---

### 🚧 v1.3 Gemini CLI Converter (In Progress)

**Milestone Goal:** Add `gemini.py` converter so `ai-codebase-mentor install --for gemini` generates Gemini-native files, following the same monorepo + converter pattern as Claude and OpenCode.

## Phase Details

### Phase 14: Gemini Converter Implementation
**Goal**: The Gemini converter correctly converts all Claude plugin files to Gemini-native format
**Depends on**: Phase 13 (v1.0 complete)
**Requirements**: GEMINI-01, GEMINI-02, GEMINI-03, GEMINI-04, GEMINI-05, GEMINI-06, GEMINI-07, GEMINI-08, GEMINI-09, GEMINI-10, GEMINI-11, GEMINI-12, GEMINI-13, GEMINI-14, GEMINI-15
**Success Criteria** (what must be TRUE):
  1. `ai-codebase-mentor install --for gemini` writes converted files to `~/.gemini/codebase-wizard/` with correct structure (agents/, commands/, skill/)
  2. Agent files have `tools:` array with Gemini snake_case names, `color:` stripped, and `Task`/`mcp__*` tools excluded
  3. Command files are written as valid TOML with `.toml` extension
  4. `${VAR}` patterns, `<sub>` tags, and `~/.claude` paths are all rewritten for Gemini compatibility
  5. `ai-codebase-mentor status` reports Gemini install state; `--for all` includes Gemini; uninstall removes the directory cleanly
**Plans**: 2 plans

Plans:
- [ ] 14-01-PLAN.md — TDD: GeminiInstaller converter + test suite (RED->GREEN all conversion rules)
- [ ] 14-02-PLAN.md — CLI wiring: register GeminiInstaller in _get_converters()

### Phase 15: Gemini E2E Integration Tests
**Goal**: CliRunner and live Gemini CLI tests confirm end-to-end install correctness
**Depends on**: Phase 14
**Requirements**: E2E-01, E2E-02, E2E-03, E2E-04, E2E-05, E2E-06, E2E-07, E2E-08
**Success Criteria** (what must be TRUE):
  1. CliRunner install/uninstall/status tests pass for `--for gemini` (global and project) in temp dirs
  2. Generated TOML command files parse as valid TOML with no syntax errors
  3. Generated agent files contain only valid Gemini snake_case tool names
  4. `--for all` CliRunner test confirms Gemini files appear alongside Claude and OpenCode output
  5. Live `gemini` headless test (marked `@pytest.mark.slow`) runs against the fixture project and produces wizard output; failure artifact bundle created on failure
**Plans**: TBD

Plans:
- [ ] 15-01: CliRunner E2E tests (E2E-01 through E2E-06, E2E-08) — all executed and results reported
- [ ] 15-02: Live Gemini CLI integration test (E2E-07) — slow test with failure artifact bundle

### Phase 16: CLI Wiring + Version Bump
**Goal**: `--for gemini` is fully wired into the CLI and the package ships as v1.3.0 on PyPI
**Depends on**: Phase 15
**Requirements**: GEMINI-13, GEMINI-14
**Success Criteria** (what must be TRUE):
  1. `ai-codebase-mentor install --for gemini` and `--for all` work end-to-end from a fresh `pip install ai-codebase-mentor==1.3.0`
  2. `ai-codebase-mentor status` output includes a Gemini line with correct install path and state
  3. PyPI release v1.3.0 is published and installable
**Plans**: TBD

Plans:
- [ ] 16-01: Wire `--for gemini` CLI help text, `--for all` iteration, status; bump version to 1.3.0; publish to PyPI

---

## Progress

**Execution Order:** 14 → 15 → 16

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Wizard Skill | v1.0 | 1/1 | Complete | 2026-03-19 |
| 2. Capture + Synthesis | v1.0 | 1/1 | Complete | 2026-03-19 |
| 3. Permission Agents | v1.0 | 1/1 | Complete | 2026-03-20 |
| 4. Plugin Manifest | v1.0 | 1/1 | Complete | 2026-03-20 |
| 5. Claude Installer | v1.0 | 1/1 | Complete | 2026-03-20 |
| 6. Python Package | v1.0 | 1/1 | Complete | 2026-03-21 |
| 7. CI/CD | v1.0 | 1/1 | Complete | 2026-03-21 |
| 8. OpenCode Converter | v1.0 | 2/2 | Complete | 2026-03-22 |
| 9. PyPI Publish | v1.0 | 1/1 | Complete | 2026-03-21 |
| 10. Agent Rulez Fix | v1.0 | 1/1 | Complete | 2026-03-23 |
| 11. Wizard UX | v1.0 | 1/1 | Complete | 2026-03-23 |
| 12. E2E Installer Tests | v1.0 | 2/2 | Complete | 2026-03-25 |
| 13. Live CLI Tests | v1.0 | 1/1 | Complete | 2026-03-26 |
| 14. Gemini Converter | 1/2 | In Progress|  | - |
| 15. Gemini E2E Tests | v1.3 | 0/2 | Not started | - |
| 16. CLI Wiring + v1.3.0 | v1.3 | 0/1 | Not started | - |
