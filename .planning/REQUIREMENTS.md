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
| GEMINI-01 | TBD | Pending |
| GEMINI-02 | TBD | Pending |
| GEMINI-03 | TBD | Pending |
| GEMINI-04 | TBD | Pending |
| GEMINI-05 | TBD | Pending |
| GEMINI-06 | TBD | Pending |
| GEMINI-07 | TBD | Pending |
| GEMINI-08 | TBD | Pending |
| GEMINI-09 | TBD | Pending |
| GEMINI-10 | TBD | Pending |
| GEMINI-11 | TBD | Pending |
| GEMINI-12 | TBD | Pending |
| GEMINI-13 | TBD | Pending |
| GEMINI-14 | TBD | Pending |
| GEMINI-15 | TBD | Pending |

**Coverage:**
- v1.3 requirements: 15 total
- Mapped to phases: 0
- Unmapped: 15 ⚠️

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29 after initial definition*
