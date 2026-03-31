#!/usr/bin/env bash
# Run Gemini e2e tests with guaranteed failure artifact capture.
#
# Usage:
#   scripts/run_gemini_e2e_with_artifacts.sh
#
# On failure, artifacts are written to:
#   artifacts/gemini-e2e-failure-<timestamp>/
#   artifacts/gemini-e2e-failure-<timestamp>.tar.gz
#
# Prerequisites:
#   - pytest, gemini CLI installed and authenticated
#   - ai-codebase-mentor installed (pip install -e .)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Prerequisite Probes ==="
echo -n "gemini CLI:   "; command -v gemini >/dev/null 2>&1 && echo "FOUND ($(gemini --version 2>&1 || echo 'version unknown'))" || { echo "NOT FOUND — test will skip"; }
echo -n "ai-codebase-mentor: "; command -v ai-codebase-mentor >/dev/null 2>&1 && echo "FOUND ($(ai-codebase-mentor --version 2>&1 || echo 'version unknown'))" || echo "NOT FOUND — install with: pip install -e ."
echo -n "Python:       "; python --version 2>&1
echo -n "OS:           "; uname -srm
echo ""

# Ensure artifacts directory exists
mkdir -p "$REPO_ROOT/artifacts"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
ARTIFACT_DIR="$REPO_ROOT/artifacts/gemini-e2e-failure-$TIMESTAMP"

echo "=== Running Gemini E2E Test ==="
echo "Command: pytest -m slow tests/test_wizard_live.py::test_gemini_describe_creates_transcript -v --tb=long"
echo ""

pytest -m "slow" tests/test_wizard_live.py::test_gemini_describe_creates_transcript -v --tb=long 2>&1 | tee "$REPO_ROOT/artifacts/gemini-e2e-output-$TIMESTAMP.log"
EXIT_CODE=${PIPESTATUS[0]}

echo ""
if [ $EXIT_CODE -ne 0 ]; then
    echo "=== TEST FAILED (exit code $EXIT_CODE) ==="
    mkdir -p "$ARTIFACT_DIR"
    cp "$REPO_ROOT/artifacts/gemini-e2e-output-$TIMESTAMP.log" "$ARTIFACT_DIR/"

    # Capture diagnostics
    {
        echo "# Gemini E2E Failure Report"
        echo ""
        echo "**Timestamp:** $TIMESTAMP"
        echo "**Exit code:** $EXIT_CODE"
        echo ""
        echo "## Environment"
        echo '```'
        echo "gemini: $(gemini --version 2>&1 || echo 'not found')"
        echo "python: $(python --version 2>&1)"
        echo "os: $(uname -srm)"
        echo '```'
        echo ""
        echo "## Test Output"
        echo '```'
        cat "$REPO_ROOT/artifacts/gemini-e2e-output-$TIMESTAMP.log"
        echo '```'
    } > "$ARTIFACT_DIR/FAILURE_REPORT.md"

    # Create tar.gz bundle
    tar -czf "$ARTIFACT_DIR.tar.gz" -C "$REPO_ROOT/artifacts" "gemini-e2e-failure-$TIMESTAMP"

    echo "Failure artifacts saved to: $ARTIFACT_DIR"
    echo "Tar bundle: $ARTIFACT_DIR.tar.gz"
    echo ""
    echo "Contents:"
    ls -la "$ARTIFACT_DIR/"
else
    echo "=== TEST PASSED (exit code 0) ==="
    # Clean up the output log on success
    rm -f "$REPO_ROOT/artifacts/gemini-e2e-output-$TIMESTAMP.log"
fi

exit $EXIT_CODE
