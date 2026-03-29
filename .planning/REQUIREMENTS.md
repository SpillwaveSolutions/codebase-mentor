# Requirements: Milestone v1.3 — Gemini CLI Converter

**Defined:** 2026-03-29
**Core Value:** A developer can run one command and walk away with a documented codebase — without clicking "Approve" fifteen times or writing documentation by hand.

## v1.3 Requirements

### Gemini Converter

- [ ] **GEMINI-01**: `ai-codebase-mentor install --for gemini` writes converted plugin to `~/.gemini/codebase-wizard/`
- [ ] **GEMINI-02**: `ai-codebase-mentor install --for gemini --project` writes to `./.gemini/codebase-wizard/`
- [ ] **GEMINI-03**: Agent frontmatter conversion — `allowed_tools:` array → `tools:` array with Gemini snake_case names
- [ ] **GEMINI-04**: Tool name mapping — 10 explicit mappings (Read→read_file, Write→write_file, Edit→replace, Bash→run_shell_command, Glob→glob, Grep→search_file_content, WebSearch→google_web_search, WebFetch→web_fetch, TodoWrite→write_todos, AskUserQuestion→ask_user)
- [ ] **GEMINI-05**: Agent `color:` field stripped (Gemini validator rejects unknown fields)
- [ ] **GEMINI-06**: `Task` and `mcp__*` tools excluded from agent tool lists (auto-registered/auto-discovered by Gemini)
- [ ] **GEMINI-07**: Command files converted from Markdown+YAML to TOML format (`.toml` extension)
- [ ] **GEMINI-08**: `${VAR}` patterns converted to `$VAR` in agent bodies (Gemini template engine conflict)
- [ ] **GEMINI-09**: `<sub>` HTML tags converted to italic `*(text)*` in output (terminals can't render subscript)
- [ ] **GEMINI-10**: Path rewriting — `~/.claude` → `~/.gemini`, `$HOME/.claude` → `$HOME/.gemini` in all content
- [ ] **GEMINI-11**: Skills copied verbatim to `skill/` directory (runtime-agnostic, singular directory name)
- [ ] **GEMINI-12**: Clean uninstall — removes installed directory; no-op if not installed
- [ ] **GEMINI-13**: Status reporting — `ai-codebase-mentor status` includes Gemini install state
- [ ] **GEMINI-14**: `--for all` includes Gemini in runtime iteration
- [ ] **GEMINI-15**: TDD test suite — covers all conversion rules, install/uninstall/status, tool mappings, TOML output

### E2E Integration Tests

- [ ] **E2E-01**: CliRunner e2e tests for `install --for gemini` — verify file output in temp dir (global + project)
- [ ] **E2E-02**: CliRunner e2e tests for `uninstall --for gemini` — verify clean removal
- [ ] **E2E-03**: CliRunner e2e tests for `status` — verify Gemini install state reporting
- [ ] **E2E-04**: Verify generated TOML command files parse correctly (valid TOML syntax)
- [ ] **E2E-05**: Verify agent files have correct `tools:` array with Gemini snake_case names
- [ ] **E2E-06**: Verify `--for all` includes Gemini alongside Claude and OpenCode
- [ ] **E2E-07**: Live Gemini CLI integration test — `gemini` headless invocation with fixture project, verify wizard output (marked `@pytest.mark.slow`, failure artifact bundle on failure)
- [ ] **E2E-08**: All e2e tests MUST be executed and results reported (per testing policy — writing is step 1, running is step 2)

## Out of Scope (v1.3)

| Feature | Reason |
|---------|--------|
| Gemini hook installation | Hooks are platform-specific; GSD handles them separately. Defer to future milestone. |
| Gemini permission system | Gemini CLI does not gate file reads behind permissions (unlike OpenCode). Not needed. |
| Two-way sync (Gemini → Claude) | Write-once, convert-at-install pattern. Source of truth is Claude format. |
| OpenCode skill activation fix | Tracked as separate todo. Not in scope for v1.3. |
| Codex converter | Deferred to future milestone. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GEMINI-01 | Phase 14 | Pending |
| GEMINI-02 | Phase 14 | Pending |
| GEMINI-03 | Phase 14 | Pending |
| GEMINI-04 | Phase 14 | Pending |
| GEMINI-05 | Phase 14 | Pending |
| GEMINI-06 | Phase 14 | Pending |
| GEMINI-07 | Phase 14 | Pending |
| GEMINI-08 | Phase 14 | Pending |
| GEMINI-09 | Phase 14 | Pending |
| GEMINI-10 | Phase 14 | Pending |
| GEMINI-11 | Phase 14 | Pending |
| GEMINI-12 | Phase 14 | Pending |
| GEMINI-13 | Phase 16 | Pending |
| GEMINI-14 | Phase 16 | Pending |
| GEMINI-15 | Phase 14 | Pending |
| E2E-01 | Phase 15 | Pending |
| E2E-02 | Phase 15 | Pending |
| E2E-03 | Phase 15 | Pending |
| E2E-04 | Phase 15 | Pending |
| E2E-05 | Phase 15 | Pending |
| E2E-06 | Phase 15 | Pending |
| E2E-07 | Phase 15 | Pending |
| E2E-08 | Phase 15 | Pending |

**Coverage:**
- v1.3 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29 — traceability filled after roadmap creation*
