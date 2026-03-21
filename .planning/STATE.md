---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: opencode-pypi
status: roadmap-ready
last_updated: "2026-03-21T00:00:00.000Z"
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 3
  completed_plans: 0
---

# State: Codebase Wizard

## Current Position

Phase: Phase 8 (not started — roadmap defined, ready for planning)
Plan: —
Status: Roadmap ready — Phase 8 and Phase 9 defined
Last activity: 2026-03-21 — Milestone v1.2 roadmap created

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-21)

**Core value:** A developer can run one command and walk away with a documented codebase — without clicking "Approve" fifteen times or writing documentation by hand.
**Current focus:** Milestone v1.2 — OpenCode converter + PyPI publish

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
- Last executed: 07-01-PLAN.md (2026-03-20) — v1.0 complete
- v1.2 phase directories: .planning/phases/08-opencode-converter/, .planning/phases/09-pypi-publish/
- Next: plan-phase 8 (08-01 OpenCode converter TDD)
