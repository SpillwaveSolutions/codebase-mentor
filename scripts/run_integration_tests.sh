#!/usr/bin/env bash
# Run all integration and e2e tests (including slow-marked tests).
#
# Usage:
#   scripts/run_integration_tests.sh          # all integration + e2e
#   scripts/run_integration_tests.sh -k opencode  # filter by keyword
#
# Prerequisites:
#   - pytest installed (pip install -e '.[dev]')
#   - For live tests: claude, opencode, rulez CLIs installed and authenticated
#
# This script probes for prerequisites before running and reports
# what will be skipped if tools are missing.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Prerequisite Probes ==="
echo -n "claude CLI:  "; command -v claude  >/dev/null 2>&1 && echo "FOUND" || echo "NOT FOUND (live claude tests will skip)"
echo -n "opencode CLI: "; command -v opencode >/dev/null 2>&1 && echo "FOUND" || echo "NOT FOUND (live opencode tests will skip)"
echo -n "rulez CLI:   "; command -v rulez   >/dev/null 2>&1 && echo "FOUND" || echo "NOT FOUND (agent rulez tests will skip)"
echo -n "Python:      "; python --version 2>&1
echo -n "pytest:      "; python -m pytest --version 2>&1 | head -1
echo ""

echo "=== Running Integration + E2E Tests (including slow) ==="
echo "Command: pytest -m 'slow' tests/ -v --tb=long $*"
echo ""

pytest -m "slow" tests/ -v --tb=long "$@"

EXIT_CODE=$?
echo ""
echo "=== Result: exit code $EXIT_CODE ==="
exit $EXIT_CODE
