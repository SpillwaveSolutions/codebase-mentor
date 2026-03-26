---
phase: 12
slug: e2e-integration-tests-for-opencode-and-claude-installer-temp-dir-tests-with-sample-plugin-files-verify-install-works-end-to-end-analyze-and-fix-current-install-failures
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `python -m pytest tests/test_opencode_installer.py -v` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_opencode_installer.py -v`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | context:fork→subtask | unit | `python -m pytest tests/test_opencode_installer.py -k subtask -v` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 1 | opencode.json merge | unit | `python -m pytest tests/test_opencode_installer.py -k subtask -v` | ❌ W0 | ⬜ pending |
| 12-01-03 | 01 | 2 | e2e install verify | e2e | `python -m pytest tests/test_e2e_installer.py -v` | ❌ W0 | ⬜ pending |
| 12-01-04 | 01 | 2 | cli flag correction | e2e | `python -m pytest tests/test_e2e_installer.py -k cli -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_e2e_installer.py` — new file for CliRunner-based E2E tests
- [ ] Existing `tests/test_opencode_installer.py` — add 3 new subtask tests (no new file needed)

*Existing pytest infrastructure covers all other phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live opencode.json written to real project | E2E correctness | Requires real filesystem + opencode installed | Run `ai-codebase-mentor install --for opencode --project` in evinova-agent-3, check `.opencode/codebase-wizard/command/` and root `opencode.json` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
