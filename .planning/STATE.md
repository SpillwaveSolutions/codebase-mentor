---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-03-25T21:21:47.217Z"
progress:
  total_phases: 12
  completed_phases: 12
  total_plans: 16
  completed_plans: 16
---

# State: Codebase Wizard

## Current Position

Phase: 12 (e2e-integration-tests-for-opencode-and-claude-installer-temp-dir-tests-with-sample-plugin-files-verify-install-works-end-to-end-analyze-and-fix-current-install-failures) — COMPLETE
Plan: 2 of 2 (DONE)

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-21)

**Core value:** A developer can run one command and walk away with a documented codebase — without clicking "Approve" fifteen times or writing documentation by hand.
**Current focus:** Phase 12 — e2e-integration-tests-for-opencode-and-claude-installer-temp-dir-tests-with-sample-plugin-files-verify-install-works-end-to-end-analyze-and-fix-current-install-failures

## Completed Work (v1.0)

Plan 01-01 tasks — all verified complete (2026-03-19):

- [x] Task 1: Add Answer Loop + Research Priority + Mode Detection to SKILL.md (commit 155369d)
- [x] Task 2: Create plugin/references/describe-questions.md (commit 1cc3087)
- [x] Task 3: Create plugin/references/explore-questions.md (commit ec8affb)
- [x] Task 4: Add File Mode (Phase 2b) to SKILL.md (commit 46989dd)
- [x] Task 5: Update SKILL.md frontmatter (commit 46989dd)
- [x] Task 6: Verification — all 8 invariants PASS

Plan 02-01 tasks — all verified complete (2026-03-19):

- [x] Task 1: Create plugin/setup/agent-rulez-sample.yaml (commit 73ff741)
- [x] Task 2: Create plugin/setup/setup.sh (commit 33020ae)
- [x] Task 3: Create plugin/commands/codebase-wizard-export.md (commit 2e5f050)
- [x] Task 4: Create plugin/commands/codebase-wizard-setup.md (commit 2944372)

Plan 04-01 tasks — all verified complete (2026-03-20):

- [x] Task 1: Finalize plugins/codebase-wizard/.claude-plugin/plugin.json (12 fields, 3 commands, 2 agents, 3 skills)
- [x] Task 2: Create plugins/codebase-wizard/.claude-plugin/marketplace.json (15 fields, entry points to plugin.json)
- [x] Verification: plugin.json PASS, marketplace.json PASS, cross-file consistency PASS

Plan 03-01 tasks — all verified complete (2026-03-20):

- [x] Task 1: Create plugin/agents/codebase-wizard-agent.md (commit 92117f1)
- [x] Task 2: Create plugin/commands/codebase-wizard.md (commit fce4784)
- [x] Task 3: Create plugin/references/codex-tools.md (commit 86076b5)
- [x] Task 4: Extend plugin/setup/setup.sh with platform detection (commit 8d7382e)
- [x] Task 5: End-to-End Verification — all 7 invariants PASS

Plan 08-01 tasks — all verified complete (2026-03-22):

- [x] Task 1 (RED): Write 13 failing tests in tests/test_opencode_installer.py (commit a6bbfad)
- [x] Task 2 (GREEN): Implement OpenCodeInstaller in opencode.py — all 13 tests pass (commit 77fcf15)
- [x] Task 3: Wire CLI _get_converters() to include opencode (commit 4f8fcd1)
- [x] Verification: 13 OpenCode tests PASS, 9 Claude tests PASS (zero regressions)

Plan 11-01 tasks — all verified complete (2026-03-23):

- [x] Task 1: Update explaining-codebase SKILL.md — numbered options, free-text fallback, Visual Flow (commit f6f39ba)
- [x] Task 2: Update exporting-conversation SKILL.md — numbered next_options in SESSION-TRANSCRIPT (commit 998475e)
- [x] Verification: 0 bare bullet Next blocks, 3 escape hatch lines, 5 Visual Flow references, numbered export template, all 4 files in sync

Plan 08-02 tasks — all verified complete (2026-03-22):

- [x] Task 1: Update --for help text to include opencode in install/uninstall (commit b245dbe)
- [x] Task 2: Verify status command shows opencode alongside claude (no code change needed)
- [x] Task 3: Full test suite — 22 passed, 0 failures (22 = 13 OpenCode + 9 Claude)

Plan 12-01 tasks — all verified complete (2026-03-25):

- [x] Task 1 (RED): Add 4 failing tests for context:fork subtask mapping (commit f704eb4)
- [x] Task 2 (GREEN): Implement _has_context_fork() and _write_opencode_subtasks() (commit adcf47c)
- [x] Verification: 18 OpenCode tests PASS, 14 Claude tests PASS, full suite 32 passed, 0 failed

Plan 12-02 tasks — all verified complete (2026-03-25):

- [x] Task 1: Create tests/test_e2e_installer.py with 9 CliRunner E2E tests (commit b7c5f4a)
- [x] Task 2: Move context:fork pending todo to done/, full suite green (commit 76ca0f6)
- [x] Verification: All 41 tests PASS (14 opencode + 14 claude + 9 e2e + 4 subtask), 0 failed

## Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-19 | Extend existing SKILL.md rather than replace | Preserve existing 5-phase foundation |
| 2026-03-19 | Lazy-load reference files per mode | Avoid context bloat |
| 2026-03-19 | Answer loop required on every response | Consistent UX across all modes |
| 2026-03-21 | OpenCode converter uses Approach A (reads bundled Claude source, generates on install) | No runtime-specific artifacts in repo; single source of truth in Claude format |
| 2026-03-21 | PyPI publish uses Trusted Publishers (OIDC) — no PYPI_TOKEN secret | Cleaner CI setup; publisher configured once on pypi.org |
| 2026-03-21 | Publish workflow runs only on semver tag push — no test duplication | test-installer.yml owns testing; publish workflow is checkout→build→publish only |

- [Phase 02]: codebase-wizard-setup.md runs in main context (no context:fork) to write settings.local.json and install Agent Rulez
- [Phase 02]: SESSION-TRANSCRIPT.md always generated for every mode — universal output regardless of describe/explore/file
- [Phase 02]: on_error: warn on PostToolUse hook — capture failures never abort wizard sessions
- [Phase 03]: context:fork on /codebase-wizard required for policy island agent to take effect
- [Phase 03]: exit 77 in install_codex is conventional "skip" signal, not an error; caught by install_all
- [Phase 03]: install_codex writes AGENTS.md with permanent manual export instructions for Codex users
- [Phase 04]: plugin.json is the install manifest (read programmatically by Phase 5 installer); marketplace.json is the discovery record (read by marketplace UI and Phase 6 CLI)
- [Phase 04]: `runtime: "claude-code"` in plugin.json is consumed by Phase 6 Python CLI as the converter selector key
- [Phase 04]: `entry: ".claude-plugin/plugin.json"` in marketplace.json is the canonical pointer from discovery record to install manifest
- [Phase 08]: Path-scoped tools (e.g., `Write(.code-wizard/**)`) stripped of scope annotation in agent conversion; path scope handled via opencode.json permissions (OPENCODE-06)
- [Phase 08]: JSONC not supported for opencode.json — use standard JSON; warn if parse fails (per v1.2 out-of-scope list)
- [Phase 09]: No TestPyPI staging — publish goes directly to PyPI (per v1.2 out-of-scope list)
- [Phase 08-opencode-converter]: YAML frontmatter parsed line-by-line with block scalar state tracking — no YAML library needed
- [Phase 08-opencode-converter]: 08-01 Task 3 pre-completed _get_converters() wiring; 08-02 updated --for help text only
- [Phase 09-pypi-publish]: PyPI publish uses Trusted Publishers OIDC — no PYPI_TOKEN secret needed; publisher configured once on pypi.org
- [Phase 09-pypi-publish]: Publish workflow fires on semver tag push only — test-installer.yml owns all testing; publish-pypi.yml has zero test steps
- [Phase 11-wizard-ux-improvements]: Numbering applied at render time in SESSION-TRANSCRIPT template; next_options JSON array schema unchanged
- [Phase 11-wizard-ux-improvements]: Visual Flow triggered by pipeline/orchestration/data flow/multi-step explanations; box-drawing chars (│ ▼ ├── └──) used for diagram format
- [Phase 10-fix-agent-rulez-config-and-add-session-capture]: Agent Rulez uses rules: top-level key (not hooks:); rulez install is the correct activation command; capture-session.sh uses exported env vars for python3 to avoid shell interpolation hazards; Write-tool fallback in SKILL.md Step 6 for Agent Rulez-absent environments
- [Phase 12]: _has_context_fork uses regex against raw frontmatter — no YAML library needed; _write_opencode_subtasks merges after permissions so both share the same opencode.json file
- [Phase 12]: cli_env fixture pattern: monkeypatch.chdir() + monkeypatch.setattr(Path.home) works with CliRunner in-process invocations for full CLI isolation

## Blockers

None currently.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260322-uqt | Commit existing evals infrastructure — trigger tuning test cases, eval runner, and HTML review UI for codebase-wizard skill | 2026-03-23 | 7ad631e | [260322-uqt-commit-existing-evals-infrastructure-tri](./quick/260322-uqt-commit-existing-evals-infrastructure-tri/) |
| 260323-v121 | v1.2.1 — OpenCode singular directories fix: agents/→agent/, skills/→skill/ in opencode.py; updated 6 test assertions in test_opencode_installer.py; all 14 OpenCode tests pass | 2026-03-23 | — | — |
| 260323-v122 | v1.2.2 — Claude plugin registry fix: installer was only copying files, never writing registry entries; added _register_plugin(), _register_marketplace(), _register_installed_plugin(), _enable_plugin(), _unregister_plugin() helpers and PLUGIN_REGISTRY_KEY/MARKETPLACE_ID constants to claude.py; 4 new tests; all 13 Claude tests pass | 2026-03-23 | — | — |
| 260323-v123 | v1.2.3 — Two hotfixes: (1) Wrong marketplace ID corrected: PLUGIN_REGISTRY_KEY=codebase-wizard@codebase-mentor, MARKETPLACE_ID=codebase-mentor, _register_marketplace() writes source: git with GitHub URL; (2) Plugin component frontmatter fixed: all 3 commands got description field, both agents got model+color fields, skill names converted to kebab-case, plugin-level marketplace.json invalid python-package block and redundant commands array removed. Tagged v1.2.3, pushed, GitHub release created. Commits: 923b2e7 (registry fix), ee22f73 (plugin frontmatter). All 27 tests pass. | 2026-03-23 | ee22f73 | — |
| 260323-mew | Document v1.2.1/1.2.2/1.2.3 hotfix releases in STATE.md | 2026-03-23 | 2406a05 | [260323-mew-document-v1-2-1-1-2-2-1-2-3-hotfix-relea](./quick/260323-mew-document-v1-2-1-1-2-2-1-2-3-hotfix-relea/) |
| 260323-nrh | Rewrite agent-rulez todo with confirmed first-run findings: wrong schema (hooks: vs rules:), nonexistent rulez hook subcommand, Agent Rulez cannot do session capture, session capture belongs in wizard skill Answer Loop via Write tool | 2026-03-23 | f4cfaba | [260323-nrh-update-agent-rulez-todo-with-first-run-f](./quick/260323-nrh-update-agent-rulez-todo-with-first-run-f/) |
| 260323-arz | Correction: Agent Rulez CAN capture JSON via run: action (passes PostToolUse event as stdin JSON); updated agent-rulez todo to reflect correct approach: run: script + Write tool fallback; added visual-flow-diagram todo; reinforced UX rule: wizard always ends with numbered options + free-text, never open question | 2026-03-23 | — | — |

## Accumulated Context

### Roadmap Evolution

- Phase 4 added: Claude Code plugin manifest and marketplace listing
- Phase 5 added: Local and global Claude Code plugin install and uninstall
- Phase 6 added: Python package for Claude Code installer (Claude-only, not on PyPI) — scope narrowed from "all runtimes + PyPI" per multi-runtime design
- Phase 7 added: GitHub Actions installer test workflow (no PyPI publish) — PyPI publish deferred to v1.2
- Multi-runtime design approved 2026-03-20: Approach A (monorepo + converters), milestones v1.0→v1.5
- Spec: docs/superpowers/specs/2026-03-20-codebase-wizard-multi-runtime-design.md
- **Phase 8 added (2026-03-21):** OpenCode converter — opencode.py, agent/command format conversion, TDD 13-case test suite, CLI wiring for `--for opencode` / `--for all` / status
- **Phase 9 added (2026-03-21):** PyPI publish — pyproject.toml metadata completeness, publish-pypi.yml with Trusted Publishers OIDC, version bump to 1.2.0
- v1.2 roadmap finalized: 2 phases, 3 plans (08-01, 08-02, 09-01)
- **Phase 10 added (2026-03-23):** Fix Agent Rulez config and add session capture — correct rules: schema, fix setup.sh (rulez install), add capture-session.sh run: script + Write-tool fallback
- **Phase 11 added (2026-03-23):** Wizard UX improvements — numbered next-options (1/2/3), free-text fallback, Visual Flow diagram option in explore mode
- **Phase 12 added (2026-03-25):** E2E integration tests for OpenCode and Claude installer — temp dir tests with sample plugin files, verify install works end-to-end, analyze and fix current install failures

## Notes

- Plan 01 file: docs/superpowers/plans/2026-03-19-codebase-wizard-plan1-core-skill.md
- Plan 02 file: docs/superpowers/plans/2026-03-19-codebase-wizard-plan2-capture-synthesis.md
- Spec file: docs/superpowers/specs/2026-03-19-codebase-wizard-design.md
- Last activity: 2026-03-25 - Phase 12 Plan 02 complete: 9 CliRunner E2E tests added in tests/test_e2e_installer.py; context:fork todo moved to done/; 41 tests pass
- Prior phase 12 plan 01: context:fork mapped to subtask:true in opencode.json via _has_context_fork() + _write_opencode_subtasks()
- Prior activity: 2026-03-23 - Phase 10 complete: Agent Rulez config fixed (rules: schema), capture-session.sh created, setup.sh fixed (rulez install), SKILL.md Answer Loop Step 6 added with Write-tool fallback
- Last executed: 10-01-PLAN.md (2026-03-23) — Agent Rulez config and session capture complete
- Phase 11 also complete (2026-03-23): wizard Answer Loop now uses numbered options (1-5) + free-text escape hatch + Visual Flow option in all three Next blocks; SESSION-TRANSCRIPT export preserves numbered format
- v1.2 milestone COMPLETE: Phases 08 (OpenCode converter) + 09 (PyPI publish) done
- All 11 phases complete; all 14 plans complete (Phase 10 Plan 01 done 2026-03-23)
- v1.2.3 tagged and published to GitHub; plugin installed at ~/.claude/plugins/codebase-wizard/ with correct codebase-wizard@codebase-mentor registry entries; Claude Code restart required to load plugin
- All 41 tests pass (18 OpenCode + 14 Claude + 9 E2E) — Phase 12 complete
- Phase 12 COMPLETE: All 12 phases done, all 16 plans done
- Next: v1.3 milestone (Codex subagents) — begin with /gsd:plan-phase
