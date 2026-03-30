# Phase 14: Gemini Converter Implementation - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning
**Source:** Extracted from conversation context, GSD source analysis, and existing OpenCode converter pattern

<domain>
## Phase Boundary

Add a `gemini.py` converter module that converts Claude Code plugin format to Gemini CLI native format at install time. Follows the same monorepo + converter pattern as the existing `opencode.py` converter. The converter is registered in `_get_converters()` and invoked via `ai-codebase-mentor install --for gemini`.

</domain>

<decisions>
## Implementation Decisions

### Converter Architecture
- Follow the same pattern as `opencode.py` — a converter class with `install()`, `uninstall()`, `status()` methods
- Register in `_get_converters()` dict (lazy import pattern established in Phase 8)
- Install destination: `~/.gemini/codebase-wizard/` (global) or `./.gemini/codebase-wizard/` (project)
- Environment variable override: `GEMINI_CONFIG_DIR`
- Clean-install approach: remove existing destination before writing new files

### Agent Conversion Rules (from GSD source analysis)
- `allowed_tools:` array → `tools:` array (keep array format, unlike OpenCode's object format)
- Tool names mapped to Gemini snake_case equivalents (10 explicit mappings)
- `color:` field stripped entirely (Gemini validator rejects unknown fields)
- `Task` tool excluded (Gemini auto-registers agents as callable tools)
- `mcp__*` tools excluded (Gemini auto-discovers MCP servers at runtime)
- `name:` field kept (unlike OpenCode which strips it)

### Tool Name Mapping Table (Claude Code → Gemini CLI)
| Claude Code | Gemini CLI |
|------------|-----------|
| Read | read_file |
| Write | write_file |
| Edit | replace |
| Bash | run_shell_command |
| Glob | glob |
| Grep | search_file_content |
| WebSearch | google_web_search |
| WebFetch | web_fetch |
| TodoWrite | write_todos |
| AskUserQuestion | ask_user |
- Tools not in the table pass through lowercased
- `mcp__*` tools are excluded entirely (not mapped)
- `Task` and `Agent` are excluded entirely

### Command Conversion Rules
- Markdown+YAML frontmatter → keep as Markdown but process content
- `/gsd:command` references rewritten to match Gemini's convention (if applicable)
- Path references `~/.claude` → `~/.gemini` in content

### Content Transforms
- `${VAR}` patterns converted to `$VAR` (Gemini template engine treats `${...}` as template expression)
- `<sub>` HTML tags converted to italic `*(text)*` (terminals can't render subscript)
- `~/.claude` → `~/.gemini` in all file content
- `$HOME/.claude` → `$HOME/.gemini` in all file content

### Directory Structure
- `~/.gemini/codebase-wizard/skill/` — skills copied verbatim (singular `skill/` matching Claude plugin convention)
- `~/.gemini/codebase-wizard/agent/` — converted agent files
- `~/.gemini/codebase-wizard/command/` — converted command files (flat naming)
- No permission system needed (unlike OpenCode's opencode.json permissions)
- No hooks installation in this phase (deferred)

### TDD Approach
- Write `tests/test_gemini_installer.py` first with RED tests
- Mirror the structure of `tests/test_opencode_installer.py`
- Test all 10 tool mappings individually
- Test agent conversion (color stripping, Task/mcp exclusion, tools array format)
- Test command conversion
- Test content transforms (${VAR}, <sub>, path rewriting)
- Test install/uninstall/status CLI operations

### Claude's Discretion
- Exact error messages and logging format
- Internal helper function decomposition within gemini.py
- Test fixture organization
- Whether to use tomli/tomli_w for TOML or simple string formatting

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Converter Pattern
- `ai_codebase_mentor/converters/opencode.py` — Reference implementation (follow same class structure)
- `tests/test_opencode_installer.py` — Reference test structure
- `ai_codebase_mentor/converters/base.py` — Base converter class (if exists)

### GSD Source (Gemini conversion logic)
- `/Users/richardhightower/src/get-shit-done/bin/install.js:1035-1160` — convertClaudeToGeminiAgent(), Gemini tool mapping, field stripping
- `/Users/richardhightower/src/get-shit-done/bin/install.js:1290-1370` — convertClaudeToGeminiToml(), command conversion
- `/Users/richardhightower/src/get-shit-done/bin/install.js:2540+` — Gemini install flow, directory resolution

### CLI Entry Point
- `ai_codebase_mentor/cli.py` — CLI commands (install, uninstall, status)
- `ai_codebase_mentor/converters/__init__.py` — `_get_converters()` dict

### Plugin Source Files (what gets converted)
- `plugin/` — Canonical Claude Code plugin files

</canonical_refs>

<specifics>
## Specific Ideas

- The TOML conversion for commands may not be needed — GSD does it because Gemini CLI originally used TOML config, but Gemini CLI also supports Markdown+YAML for custom commands. Verify Gemini's current format expectations before implementing TOML conversion.
- Consider whether `gemini` CLI is invoked differently than `opencode run` for headless testing (relevant for Phase 15 e2e tests, not this phase).
- The tool mapping table is identical to GSD's — reuse their proven mappings.

</specifics>

<deferred>
## Deferred Ideas

- Gemini hook installation — platform-specific, separate phase
- Gemini permission system — not needed (Gemini doesn't gate file reads)
- Gemini-specific status line or session tracking
- Two-way sync (Gemini → Claude)

</deferred>

---

*Phase: 14-gemini-converter-implementation*
*Context gathered: 2026-03-30 from conversation analysis and GSD source review*
