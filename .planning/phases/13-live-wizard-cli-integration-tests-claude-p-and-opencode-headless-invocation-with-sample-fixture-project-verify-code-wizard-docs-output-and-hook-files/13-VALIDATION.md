---
phase: 13
slug: live-wizard-cli-integration-tests-claude-p-and-opencode-headless-invocation-with-sample-fixture-project-verify-code-wizard-docs-output-and-hook-files
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `python -m pytest tests/test_wizard_live.py -v -m slow` |
| **Full suite command** | `python -m pytest tests/ -v` (fast only) / `python -m pytest tests/ -v -m slow` (with live) |
| **Estimated runtime** | Fast suite ~2s; live suite ~5–10 min (real LLM calls) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -v` (fast tests only, no -m slow)
- **After every plan wave:** Run `python -m pytest tests/test_wizard_live.py -v -m slow --co` (collect/dry-run to verify test structure)
- **Before `/gsd:verify-work`:** Full fast suite must be green; live suite run once manually
- **Max feedback latency:** 10 seconds (fast suite)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | fixture project | setup | `ls tests/fixtures/sample-wizard-project/` | ❌ W0 | ⬜ pending |
| 13-01-02 | 01 | 1 | slow marker | config | `grep "slow" pyproject.toml` | ❌ W0 | ⬜ pending |
| 13-01-03 | 01 | 1 | claude -p describe → SESSION-TRANSCRIPT.md | slow | `python -m pytest tests/test_wizard_live.py::test_claude_describe_creates_transcript -v -m slow` | ❌ W0 | ⬜ pending |
| 13-01-04 | 01 | 1 | claude -p describe → CODEBASE.md path | slow | `python -m pytest tests/test_wizard_live.py::test_claude_describe_creates_codebase_md -v -m slow` | ❌ W0 | ⬜ pending |
| 13-01-05 | 01 | 1 | opencode describe → SESSION-TRANSCRIPT.md | slow | `python -m pytest tests/test_wizard_live.py::test_opencode_describe_creates_transcript -v -m slow` | ❌ W0 | ⬜ pending |
| 13-01-06 | 01 | 1 | skip when claude auth absent | fast | `python -m pytest tests/test_wizard_live.py::test_claude_skip_when_no_auth -v` | ❌ W0 | ⬜ pending |
| 13-01-07 | 01 | 1 | skip when opencode auth absent | fast | `python -m pytest tests/test_wizard_live.py::test_opencode_skip_when_no_auth -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/fixtures/sample-wizard-project/` — 3-file Python project (main.py, utils.py, README.md)
- [ ] `tests/test_wizard_live.py` — file stub with `@pytest.mark.slow` + skip-if-no-auth logic
- [ ] `pyproject.toml` updated — add `slow` to `markers` list and configure `addopts` to skip slow by default

*Existing pytest infrastructure covers fast tests. Wave 0 adds fixtures + slow marker.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SESSION-TRANSCRIPT.md contains meaningful codebase summary | Quality | LLM output non-deterministic | Read `.code-wizard/docs/*/SESSION-TRANSCRIPT.md`, verify it describes the sample project |
| `rulez install` hook activation in real project | Depends on `rulez` installed | CI may not have Agent Rulez | Run setup.sh in test project, check `~/.config/rulez/` or `.claude/hooks.yaml` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s (fast suite)
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
