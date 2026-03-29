# Testing Guide

**Tests are only complete after execution.**

## Test Suites

| Suite | Command | Markers | When to Run |
|-------|---------|---------|-------------|
| Fast unit tests | `pytest` | default (excludes slow) | Every change |
| Integration + e2e | `scripts/run_integration_tests.sh` | `@pytest.mark.slow` | Before PR, after test changes |
| OpenCode e2e with artifacts | `scripts/run_opencode_e2e_with_artifacts.sh` | `@pytest.mark.slow` | When testing OpenCode + Agent Rulez integration |
| All tests | `pytest -m '' --tb=short` | all | Full validation |

## Prerequisites for Live Tests

Live/slow tests require external CLIs installed and authenticated:

| Tool | Check | Install |
|------|-------|---------|
| claude | `claude -p OK --max-budget-usd 0.01` | [Claude Code CLI](https://claude.ai/code) |
| opencode | `opencode run --dir /tmp echo hello` | [OpenCode CLI](https://github.com/opencode-ai/opencode) |
| rulez | `rulez --version` | `pip install agent-rulez` |
| ai-codebase-mentor | `ai-codebase-mentor --version` | `pip install -e .` |

Tests skip gracefully when prerequisites are missing — but skipped is not verified.

## Definition of Done

A test task is complete only when one of these is true:

1. **Ran and passed** — command and pytest summary line documented
2. **Ran and failed with artifacts** — command, error, and artifact path documented
3. **Blocked** — exact missing prerequisite listed, with the command to run once unblocked

A skipped test does not count as done.

## Failure Artifacts

E2e tests emit failure artifact bundles to `artifacts/` on failure:

```
artifacts/opencode-rulez-failure-<timestamp>/
  FAILURE_REPORT.md          # Summary for handoff
  env.json                   # Redacted environment
  versions.json              # Tool versions
  setup-stdout.txt           # Subprocess outputs
  setup-stderr.txt
  wizard-stdout.txt
  wizard-stderr.txt
  config/                    # Generated config files
  sessions/                  # Session artifacts
  tree.txt                   # Directory listing
  opencode-rulez-failure-<timestamp>.tar.gz  # Compressed bundle
```

## CI Workflows

| Workflow | Trigger | Tests Run |
|----------|---------|-----------|
| `test-installer.yml` | Every push | Fast unit + structure tests |
| `test-integration.yml` | Manual dispatch, nightly | Slow/live tests (requires secrets) |
| `publish-pypi.yml` | Semver tag push | Publish to PyPI |

## PR Checklist

If tests were added or changed:
- [ ] Tests were executed locally
- [ ] Exact command pasted in PR description
- [ ] Result (pass/fail/blocked) documented
- [ ] If failed: artifact location noted
