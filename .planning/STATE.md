---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-03-22T14:46:32.689Z"
progress:
  total_phases: 9
  completed_phases: 9
  total_plans: 12
  completed_plans: 12
---

# State: Codebase Wizard

## Current Position

Phase: 09 (pypi-publish) — COMPLETE
Plan: 1 of 1 — COMPLETE

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-21)

**Core value:** A developer can run one command and walk away with a documented codebase — without clicking "Approve" fifteen times or writing documentation by hand.
**Current focus:** Phase 09 — pypi-publish

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

Plan 08-02 tasks — all verified complete (2026-03-22):

- [x] Task 1: Update --for help text to include opencode in install/uninstall (commit b245dbe)
- [x] Task 2: Verify status command shows opencode alongside claude (no code change needed)
- [x] Task 3: Full test suite — 22 passed, 0 failures (22 = 13 OpenCode + 9 Claude)

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

## Blockers

None currently.

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

## Notes

- Plan 01 file: docs/superpowers/plans/2026-03-19-codebase-wizard-plan1-core-skill.md
- Plan 02 file: docs/superpowers/plans/2026-03-19-codebase-wizard-plan2-capture-synthesis.md
- Spec file: docs/superpowers/specs/2026-03-19-codebase-wizard-design.md
- Last executed: 09-01-PLAN.md (2026-03-22) — PyPI publish pipeline complete
- v1.2 milestone COMPLETE: Phases 08 (OpenCode converter) + 09 (PyPI publish) done
- All 9 phases complete; all 12 plans complete
- Push `git tag v1.2.0 && git push origin v1.2.0` to publish ai-codebase-mentor 1.2.0 to PyPI
- Next: v1.3 milestone (Codex subagents) when ready
