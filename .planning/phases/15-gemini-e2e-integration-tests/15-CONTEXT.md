# Phase 15: Gemini E2E Integration Tests — Context

## Phase Goal

CliRunner and live Gemini CLI tests confirm end-to-end install correctness.

## Success Criteria

1. CliRunner install/uninstall/status tests pass for `--for gemini` (global and project) in temp dirs
2. Generated TOML command files parse as valid TOML with no syntax errors
3. Generated agent files contain only valid Gemini snake_case tool names
4. `--for all` CliRunner test confirms Gemini files appear alongside Claude and OpenCode output
5. Live `gemini` headless test (marked `@pytest.mark.slow`) runs against the fixture project and produces wizard output; failure artifact bundle created on failure

## Dependencies

- **Phase 14** (Gemini Converter Implementation) — COMPLETE, VERIFIED (15/15 requirements, 36/36 tests pass)

## Requirements

| ID | Description |
|----|-------------|
| E2E-01 | CliRunner tests for `install --for gemini` (global + project) |
| E2E-02 | CliRunner tests for `uninstall --for gemini` |
| E2E-03 | CliRunner tests for `status` Gemini reporting |
| E2E-04 | Generated TOML command files parse as valid TOML |
| E2E-05 | Agent files have correct snake_case tool names |
| E2E-06 | `--for all` includes Gemini files |
| E2E-07 | Live Gemini CLI headless test with fixture project |
| E2E-08 | All tests executed with results reported |

## Plans

- **15-01:** CliRunner E2E tests (E2E-01 through E2E-06, E2E-08)
- **15-02:** Live Gemini CLI integration test (E2E-07) with failure artifact bundle

## Key Decisions

- Follow existing `cli_env` fixture pattern from `test_e2e_installer.py`
- New file `tests/test_e2e_gemini_installer.py` preferred over bloating existing file
- Live test uses `gemini -p "prompt" --approval-mode yolo -o text` for headless invocation
- Live test installs with `--project` to avoid HOME override complexity
- Accept Gemini "Skill conflict detected" warnings as benign in live tests
- TOML validation uses `tomllib.loads()` (stdlib 3.11+)
- Update existing `--for all` and status tests to assert Gemini presence

## Key Files

| File | Role |
|------|------|
| `ai_codebase_mentor/converters/gemini.py` | GeminiInstaller (390 lines, Phase 14) |
| `tests/test_gemini_installer.py` | Unit tests (36/36 pass, Phase 14) |
| `ai_codebase_mentor/cli.py` | CLI entry point, `_get_converters()` |
| `tests/test_e2e_installer.py` | Existing CliRunner E2E pattern |
| `tests/test_wizard_live.py` | Existing live CLI test pattern |
| `tests/integration/test_agent_rulez_e2e.py` | Failure artifact bundle pattern |
| `scripts/run_opencode_e2e_with_artifacts.sh` | Shell artifact runner pattern |
| `tests/fixtures/sample-wizard-project/` | Fixture project for live tests |
