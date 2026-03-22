# Phase 8: OpenCode Converter — Context

**Gathered:** 2026-03-21
**Status:** Ready for planning
**Source:** Conversation, REQUIREMENTS.md, design spec, GSD multi-runtime article

---

<domain>
## Phase Boundary

Phase 8 delivers `ai_codebase_mentor/converters/opencode.py` — an install-time
converter that reads the bundled Claude Code plugin source and generates
OpenCode-native files at `~/.config/opencode/codebase-wizard/` (global) or
`./.opencode/codebase-wizard/` (project). The converter is wired into the
existing CLI via `_get_converters()`. This phase also ships a TDD test suite
(`tests/test_opencode_installer.py`) mirroring the existing `test_claude_installer.py`.

**What this phase does NOT include:** OpenCode hook installation, JSONC parsing
for existing opencode.json content, Gemini/Codex converters.

</domain>

<decisions>
## Implementation Decisions

### Architecture — Locked

- `opencode.py` implements the same `RuntimeInstaller` ABC as `claude.py`
  (`install`, `uninstall`, `status`, `_resolve_dest`)
- Converter is registered in `_get_converters()` in `cli.py` as `"opencode": OpenCodeInstaller`
- `_resolve_dest("global")` returns `Path.home() / ".config" / "opencode" / "codebase-wizard"`
- `_resolve_dest("project")` returns `Path.cwd() / ".opencode" / "codebase-wizard"`
- `install()` is idempotent: remove existing destination before copying (same as ClaudeInstaller)
- `uninstall()` is a no-op if destination does not exist (no exception)
- `status()` checks global first, then project; returns `{installed, location, version}`

### Output Directory Structure — Locked

```
~/.config/opencode/codebase-wizard/        (global)
  command/                                  ← renamed from commands/ (singular)
    codebase-wizard.md
    codebase-wizard-export.md
    codebase-wizard-setup.md
  agents/
    codebase-wizard-agent.md               ← frontmatter converted
    codebase-wizard-setup-agent.md         ← frontmatter converted
  skills/
    explaining-codebase/                   ← verbatim copy
    configuring-codebase-wizard/           ← verbatim copy
    exporting-conversation/                ← verbatim copy
```

### Agent Frontmatter Conversion — Locked

Input (Claude Code):
```yaml
allowed_tools:
  - "Read"
  - "Write(.code-wizard/**)"
  - "AskUserQuestion"
name: codebase-wizard-agent
color: cyan
```

Output (OpenCode):
```yaml
tools:
  read: true
  write: true
  question: true
color: "#00FFFF"
```

Rules:
- `allowed_tools:` array → `tools:` object with `{tool: true}` entries
- Path-scoped tools (`Write(.code-wizard/**)`) → strip scope, lowercase tool name only
- `name:` field removed (OpenCode derives name from filename)
- Named colors → hex: cyan→#00FFFF, red→#FF0000, green→#00FF00, blue→#0000FF,
  yellow→#FFFF00, magenta→#FF00FF, orange→#FFA500, purple→#800080,
  pink→#FFC0CB, white→#FFFFFF, black→#000000, gray→#808080, grey→#808080

### Tool Name Special Mappings — Locked

| Claude Code | OpenCode |
|-------------|----------|
| AskUserQuestion | question |
| SkillTool | skill |
| TodoWrite | todowrite |
| WebFetch | webfetch |
| WebSearch | websearch |

All others: lowercase directly. `mcp__*` names pass through unchanged.

### Command File Handling — Locked

- `plugin/commands/*.md` → copied to `command/` (singular) in output dir
- No frontmatter conversion needed for commands (commands don't have tool lists)
- Content rewriting applied: `~/.claude` → `~/.config/opencode`
- Command cross-references (e.g., `/codebase-wizard`) remain unchanged (no colon
  namespacing in our commands — they're already flat)

### Content Path Rewriting — Locked

Applied to all output files (agents and commands):
- `~/.claude` → `~/.config/opencode`
- `~/.claude/plugins/` → `~/.config/opencode/`

### Skills Handling — Locked

`plugin/skills/` copied verbatim to `skills/` in output dir. SKILL.md files
are runtime-agnostic and require no transformation.

### opencode.json Permission Pre-Authorization — Locked

After writing files, converter writes (or creates) `opencode.json` in the
**parent** directory of the install dir (i.e., `~/.config/opencode/opencode.json`
for global, `./.opencode/opencode.json` for project) with:

```json
{
  "permission": {
    "read": {
      "~/.config/opencode/codebase-wizard/*": "allow"
    },
    "external_directory": {
      "~/.config/opencode/codebase-wizard/*": "allow"
    }
  }
}
```

For project installs, replace path with `./.opencode/codebase-wizard/*`.

If `opencode.json` already exists with valid JSON, **merge** the permission
entries (do not overwrite). If parse fails, write a warning to stderr and skip
permission configuration (don't abort the install).

### TDD Approach — Locked

Same pattern as `tests/test_claude_installer.py`:
- `REAL_PLUGIN_SOURCE` points to `plugins/codebase-wizard/`
- `source_plugin_dir` fixture: `shutil.copytree(REAL_PLUGIN_SOURCE, tmp_path/...)`
- `installer` fixture: `monkeypatch.setattr(Path, "home", ...)` + `monkeypatch.chdir(...)`
- RED phase first: write all 13 tests, confirm they fail, then implement

### Test Coverage (13 cases) — Locked

1. Global install writes to `~/.config/opencode/codebase-wizard/`
2. Project install writes to `./.opencode/codebase-wizard/`
3. Idempotent re-install (updates in place without error)
4. Global uninstall removes installed directory
5. Project uninstall removes project-local copy
6. Uninstall no-op when not installed (no exception)
7. Status reports installed=True after global install
8. Status reports installed=False before any install
9. Agent tool names lowercased in output (Read → read in `tools:` object)
10. Special tool mapping applied (AskUserQuestion → question)
11. `name:` field stripped from agent frontmatter output
12. Output directory contains `command/` (singular), not `commands/`
13. RuntimeError raised on missing source

### Claude's Discretion

- Implementation language for frontmatter parsing: stdlib `re` + string manipulation
  is fine; no YAML parser needed for this level of conversion
- Whether `_convert_agent_frontmatter()` and `_convert_tools()` are standalone
  functions or private methods on `OpenCodeInstaller`
- Whether `opencode.json` merge logic is inline or a helper function
- Error message wording (must be human-readable; exact phrasing is discretionary)
- Whether to test `opencode.json` permission writing in a dedicated test case
  (beyond the 13 mandatory cases) — recommended but not required

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Implementation patterns (read these first)
- `ai_codebase_mentor/converters/base.py` — RuntimeInstaller ABC (interface to implement)
- `ai_codebase_mentor/converters/claude.py` — reference implementation (mirror this pattern)
- `tests/test_claude_installer.py` — reference test suite (mirror this structure)
- `ai_codebase_mentor/cli.py` — `_get_converters()` dict to extend

### Plugin source files (what gets converted)
- `plugins/codebase-wizard/agents/codebase-wizard-agent.md` — agent with `allowed_tools:`
- `plugins/codebase-wizard/agents/codebase-wizard-setup-agent.md` — second agent
- `plugins/codebase-wizard/commands/` — three command files
- `plugins/codebase-wizard/skills/` — three skill directories (verbatim copy)

### Requirements and design
- `.planning/REQUIREMENTS.md` — OPENCODE-01 through OPENCODE-13
- `docs/superpowers/specs/2026-03-20-codebase-wizard-multi-runtime-design.md` — Section 2 converter table
- `ai_codebase_mentor/plugin/skills/explaining-codebase/references/codex-tools.md` — tool name matrix

</canonical_refs>

<specifics>
## Specific Implementation Notes

### Tool name conversion logic (pseudo-code)
```python
SPECIAL_MAPPINGS = {
    "AskUserQuestion": "question",
    "SkillTool": "skill",
    "TodoWrite": "todowrite",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
}

def _convert_tool_name(tool: str) -> str:
    # Strip path scope annotation: "Write(.code-wizard/**)" → "Write"
    base = tool.split("(")[0]
    if base in SPECIAL_MAPPINGS:
        return SPECIAL_MAPPINGS[base]
    if base.startswith("mcp__"):
        return base  # pass through unchanged
    return base.lower()
```

### Color conversion (13 named colors)
```python
COLOR_MAP = {
    "cyan": "#00FFFF", "red": "#FF0000", "green": "#00FF00",
    "blue": "#0000FF", "yellow": "#FFFF00", "magenta": "#FF00FF",
    "orange": "#FFA500", "purple": "#800080", "pink": "#FFC0CB",
    "white": "#FFFFFF", "black": "#000000", "gray": "#808080", "grey": "#808080",
}
```

### opencode.json permission key paths
- Global: `"~/.config/opencode/codebase-wizard/*": "allow"`
- Project: `./.opencode/codebase-wizard/*` resolved to absolute path

</specifics>

<deferred>
## Deferred Ideas

- JSONC parser for existing opencode.json with comments — out of scope v1.2
- Hook installation for OpenCode — out of scope v1.2 (OpenCode has hooks but
  Agent Rulez integration for OpenCode is future work)
- Gemini/Codex converters — v1.3 and v1.4 respectively
- `subagent_type: "general-purpose"` → `"general"` rewrite — included in conversion
  but only if the field appears in codebase-wizard agent files (check first)

</deferred>

---

*Phase: 08-opencode-converter*
*Context gathered: 2026-03-21 from conversation + requirements + design spec*
