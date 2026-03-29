# Retrospective

## Milestone: v1.0 — Codebase Wizard MVP

**Shipped:** 2026-03-29
**Phases:** 13 | **Plans:** 17 | **Timeline:** 10 days (2026-03-19 → 2026-03-29)

### What Was Built

- Core wizard skill with Describe/Explore/File modes and question banks
- Auto-capture pipeline via Agent Rulez hooks + Write-tool fallback
- Pre-authorized agents (policy islands) for zero-approval execution
- Multi-runtime Python package (`ai-codebase-mentor`) with Claude + OpenCode converters
- CLI with install/uninstall/status for both runtimes
- PyPI publish via GitHub Actions with Trusted Publishers OIDC
- 71 fast tests + 3 slow integration tests + failure artifact bundle system
- CI/CD: test-installer.yml (every push) + test-integration.yml (manual/nightly)

### What Worked

- **Monorepo + converters pattern:** One canonical format (Claude), generated on install. No duplication.
- **TDD approach:** Every converter was test-driven. Caught regressions early.
- **Phase-by-phase delivery:** Each phase shipped independently with atomic commits.
- **Policy islands pattern:** Zero-approval execution works well for the wizard use case.

### What Was Inefficient

- **Tests written but never run:** Phases 12-13 wrote extensive e2e tests with `@pytest.mark.slow` that were never executed. Six bugs were discovered only when a human demanded the tests be run. This wasted an entire session on debugging issues that should have been caught immediately.
- **OpenCode integration assumed, not verified:** The OpenCode converter was tested via unit tests and CliRunner, but the actual `opencode run` invocation was never tested until late. The skill activation gap was only discovered in the last session.
- **Probe function bugs accepted as blockers:** The opencode probe returned false (30s timeout in test context) but opencode was installed the whole time. The agent accepted the skip without checking `which opencode`.

### Patterns Established

- **Definition of Done for tests:** Writing a test is not complete until it runs and results are reviewed. Added to CLAUDE.md, PROJECT.md, and memory.
- **Failure artifact bundles:** E2e tests emit comprehensive diagnostic packages on failure (FAILURE_REPORT.md, config snapshots, subprocess outputs, directory tree, tarball).
- **Run scripts:** `scripts/run_integration_tests.sh` and `scripts/run_opencode_e2e_with_artifacts.sh` standardize test execution.
- **Verify before claiming blocked:** Always run `which <tool>` before accepting a pytest skip as evidence of a missing tool.

### Key Lessons

1. **Run the test.** Always. If you wrote it, run it. If it has special markers, use those markers. If it needs external tools, check if they're available. Never mark test work complete without execution evidence.
2. **Unit tests are necessary but not sufficient.** The OpenCode converter passed all 18 unit tests but failed in real integration. The gap was only visible with a real `opencode run` invocation.
3. **Session-scoped pytest fixtures can mask availability.** A probe that fails once (timeout) caches the result for the entire pytest session. Don't trust probe results — verify independently.

### Cost Observations

- Model mix: mostly Sonnet for execution, Opus for planning
- Sessions: ~15 across the milestone
- Notable: The 6 bugs found by running tests could have been caught in a single session if the tests had been run when written

---

## Cross-Milestone Trends

| Metric | v1.0 |
|--------|------|
| Phases | 13 |
| Plans | 17 |
| Duration (days) | 10 |
| Python LOC | 4,079 |
| Test count | 71 fast + 3 slow |
| Bugs found by running tests | 6 |
