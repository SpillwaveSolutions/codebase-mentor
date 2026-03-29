#!/usr/bin/env bash
# Run OpenCode e2e tests with guaranteed failure artifact capture.
#
# Usage:
#   scripts/run_opencode_e2e_with_artifacts.sh
#
# On failure, artifacts are written to:
#   artifacts/opencode-rulez-failure-<timestamp>/
#   artifacts/opencode-rulez-failure-<timestamp>.tar.gz
#
# The test itself handles artifact collection via _collect_failure_artifacts().
# This script ensures the artifacts/ directory exists, runs the test, and
# reports the artifact location on failure.
#
# Prerequisites:
#   - pytest, opencode, rulez, claude CLIs installed and authenticated
#   - ai-codebase-mentor installed (pip install -e .)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Prerequisite Probes ==="
echo -n "opencode CLI: "; command -v opencode >/dev/null 2>&1 && echo "FOUND ($(opencode --version 2>&1 || echo 'version unknown'))" || { echo "NOT FOUND — test will skip"; }
echo -n "rulez CLI:    "; command -v rulez   >/dev/null 2>&1 && echo "FOUND ($(rulez --version 2>&1 || echo 'version unknown'))" || { echo "NOT FOUND — test will skip"; }
echo -n "claude CLI:   "; command -v claude  >/dev/null 2>&1 && echo "FOUND" || echo "NOT FOUND"
echo -n "ai-codebase-mentor: "; command -v ai-codebase-mentor >/dev/null 2>&1 && echo "FOUND ($(ai-codebase-mentor --version 2>&1 || echo 'version unknown'))" || echo "NOT FOUND — install with: pip install -e ."
echo -n "Python:       "; python --version 2>&1
echo -n "OS:           "; uname -srm
echo ""

# Ensure artifacts directory exists
mkdir -p "$REPO_ROOT/artifacts"

echo "=== Running OpenCode E2E Test ==="
echo "Command: pytest -m slow tests/integration/test_agent_rulez_e2e.py::test_agent_rulez_opencode_capture_to_export -v --tb=long"
echo ""

pytest -m "slow" tests/integration/test_agent_rulez_e2e.py::test_agent_rulez_opencode_capture_to_export -v --tb=long
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -ne 0 ]; then
    echo "=== TEST FAILED (exit code $EXIT_CODE) ==="
    LATEST_ARTIFACT=$(ls -td "$REPO_ROOT/artifacts/opencode-rulez-failure-"* 2>/dev/null | head -1)
    if [ -n "$LATEST_ARTIFACT" ]; then
        echo "Failure artifacts saved to: $LATEST_ARTIFACT"
        echo ""
        echo "Contents:"
        ls -la "$LATEST_ARTIFACT/"
        echo ""
        REPORT="$LATEST_ARTIFACT/FAILURE_REPORT.md"
        if [ -f "$REPORT" ]; then
            echo "=== FAILURE_REPORT.md ==="
            cat "$REPORT"
        fi
    else
        echo "WARNING: No failure artifacts found in artifacts/"
        echo "The _collect_failure_artifacts() helper may not have fired."
    fi
else
    echo "=== TEST PASSED (exit code 0) ==="
fi

exit $EXIT_CODE
