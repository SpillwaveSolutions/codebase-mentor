# Phase 14: Gemini Converter Implementation - Research

**Researched:** 2026-03-26
**Domain:** Gemini CLI plugin format, Python converter pattern, TDD with pytest
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Converter Architecture
- Follow the same pattern as `opencode.py` — a converter class with `install()`, `uninstall()`, `status()` methods
- Register in `_get_converters()` dict (lazy import pattern established in Phase 8)
- Install destination: `~/.gemini/codebase-wizard/` (global) or `./.gemini/codebase-wizard/` (project)
- Environment variable override: `GEMINI_CONFIG_DIR`
- Clean-install approach: remove existing destination before writing new files

#### Agent Conversion Rules (from GSD source analysis)
- `allowed_tools:` array → `tools:` array (keep array format, unlike OpenCode's object format)
- Tool names mapped to Gemini snake_case equivalents (10 explicit mappings)
- `color:` field stripped entirely (Gemini validator rejects unknown fields)
- `Task` tool excluded (Gemini auto-registers agents as callable tools)
- `mcp__*` tools excluded (Gemini auto-discovers MCP servers at runtime)
- `name:` field kept (unlike OpenCode which strips it)

#### Tool Name Mapping Table (Claude Code → Gemini CLI)
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

#### Command Conversion Rules
- Markdown+YAML frontmatter → convert to TOML format with `.toml` extension (GEMINI-07 is confirmed)
- Path references `~/.claude` → `~/.gemini` in content

#### Content Transforms
- `${VAR}` patterns converted to `$VAR` (Gemini template engine treats `${...}` as template expression)
- `<sub>` HTML tags converted to italic `*(text)*` (terminals can't render subscript)
- `~/.claude` → `~/.gemini` in all file content
- `$HOME/.claude` → `$HOME/.gemini` in all file content

#### Directory Structure
- `~/.gemini/codebase-wizard/skill/` — skills copied verbatim (singular `skill/` matching Claude plugin convention)
- `~/.gemini/codebase-wizard/agent/` — converted agent files
- `~/.gemini/codebase-wizard/command/` — converted command files (TOML, `.toml` extension)
- No permission system needed (unlike OpenCode's opencode.json permissions)
- No hooks installation in this phase (deferred)

#### TDD Approach
- Write `tests/test_gemini_installer.py` first with RED tests
- Mirror the structure of `tests/test_opencode_installer.py`
- Test all 10 tool mappings individually
- Test agent conversion (color stripping, Task/mcp exclusion, tools array format)
- Test command conversion
- Test content transforms (`${VAR}`, `<sub>`, path rewriting)
- Test install/uninstall/status CLI operations

### Claude's Discretion
- Exact error messages and logging format
- Internal helper function decomposition within gemini.py
- Test fixture organization
- Whether to use tomli/tomli_w for TOML or simple string formatting

### Deferred Ideas (OUT OF SCOPE)
- Gemini hook installation — platform-specific, separate phase
- Gemini permission system — not needed (Gemini doesn't gate file reads)
- Gemini-specific status line or session tracking
- Two-way sync (Gemini → Claude)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GEMINI-01 | `ai-codebase-mentor install --for gemini` writes to `~/.gemini/codebase-wizard/` | _resolve_dest() pattern from opencode.py; verified `~/.gemini` is the real Gemini config dir |
| GEMINI-02 | `--project` writes to `./.gemini/codebase-wizard/` | Same _resolve_dest() pattern; cwd-relative path for project scope |
| GEMINI-03 | Agent frontmatter: `allowed_tools:` → `tools:` array with Gemini snake_case names | Confirmed from live ~/.gemini/agents/gsd-codebase-mapper.md: uses `tools:\n  - read_file` YAML array format |
| GEMINI-04 | 10 explicit tool name mappings | Verified from GSD install.js `claudeToGeminiTools` const (lines 457-468) and live agent files |
| GEMINI-05 | `color:` field stripped from agent frontmatter | Confirmed in GSD convertClaudeToGeminiAgent() — `if (trimmed.startsWith('color:')) continue;` |
| GEMINI-06 | `Task` and `mcp__*` excluded from tools list | Confirmed in GSD convertGeminiToolName() — null return for both |
| GEMINI-07 | Commands converted from Markdown+YAML to TOML with `.toml` extension | **CONFIRMED**: Live files in `~/.gemini/commands/gsd/` are all `.toml`; format: `description = "..."` + `prompt = "..."` |
| GEMINI-08 | `${VAR}` → `$VAR` in agent bodies | Confirmed in GSD: `body.replace(/\$\{(\w+)\}/g, '$$$1')` with comment explaining Gemini templateString() conflict |
| GEMINI-09 | `<sub>` HTML → `*(text)*` italic | Confirmed in GSD `stripSubTags()` function |
| GEMINI-10 | Path rewriting `~/.claude` → `~/.gemini`, `$HOME/.claude` → `$HOME/.gemini` | Standard PATH_REWRITES pattern from opencode.py; apply same pattern |
| GEMINI-11 | Skills copied verbatim to `skill/` directory | Same shutil.copytree pattern as opencode.py's `destination / "skill"` |
| GEMINI-12 | Clean uninstall removes directory; no-op if not installed | Identical to opencode.py uninstall() — shutil.rmtree + existence check |
| GEMINI-13 | Status reporting (NOTE: Traceability map says Phase 16) | status() dict pattern identical to opencode.py; registered in _get_converters() means it auto-appears |
| GEMINI-14 | `--for all` includes Gemini (NOTE: Traceability map says Phase 16) | Adding to _get_converters() is sufficient — CLI already iterates all registered converters |
| GEMINI-15 | TDD test suite covering all rules | Mirror test_opencode_installer.py structure with Gemini-specific assertions |
</phase_requirements>

---

## Summary

Phase 14 implements a `GeminiInstaller` converter class in `ai_codebase_mentor/converters/gemini.py` that converts the Claude Code plugin format to Gemini CLI-native files at install time. The implementation is a direct Python port of the JavaScript `convertClaudeToGeminiAgent()` and `convertClaudeToGeminiToml()` functions from the GSD codebase.

The key differences from the OpenCode converter are: (1) Gemini uses a YAML array for `tools:` (not an object with `true` values), (2) commands become `.toml` files (not `.md`), (3) `name:` is kept in agent frontmatter (OpenCode strips it), (4) `color:` is stripped entirely (OpenCode converts to hex), and (5) there is no permissions JSON file to write. The live `~/.gemini/` directory confirms all of these behaviors from the GSD source.

TOML generation does NOT require the `tomllib`/`tomli` library. The GSD source uses simple string formatting (`description = "..."` + `prompt = "..."`), which is valid TOML. Python's `json.dumps()` produces JSON-escaped strings that are also valid TOML basic strings. The generated TOML has exactly two fields: `description` and `prompt`. No TOML library is needed for writing, only for testing TOML validity (using stdlib `tomllib` on Python 3.11+ or falling back to string checks on earlier versions).

**Primary recommendation:** Port GSD's `convertClaudeToGeminiAgent()` and `convertClaudeToGeminiToml()` logic directly to Python following the opencode.py class structure. Use `json.dumps()` for TOML string escaping. Register in `_get_converters()` with key `"gemini"`.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib: `re`, `shutil`, `pathlib` | 3.9+ | Regex, file operations, path handling | No external deps; matches opencode.py pattern |
| Python stdlib: `json` | 3.9+ | TOML string escaping via `json.dumps()` | JSON strings are valid TOML basic strings |
| Python stdlib: `tomllib` | 3.11+ (3.9 has no stdlib TOML) | TOML parse validation in tests only | Available in test environment (Python 3.13 confirmed) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 7.0+ | Test runner | Already in `[dev]` dependencies |
| `click.testing.CliRunner` | 8.0+ | CLI integration tests | Already used in existing test suite |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `json.dumps()` for TOML escaping | `tomli_w` | tomli_w is cleaner but adds a dependency and is overkill for two-field TOML |
| Stdlib `tomllib` (3.11+) for test validation | String assertions | Tomllib is cleaner and available in dev environment (Python 3.13); but tests can also just check `description =` and `prompt =` directly |

**Installation:** No new dependencies required. All needed libraries are in Python stdlib or already installed.

**Version verification:** All stdlib, no npm required.

---

## Architecture Patterns

### Recommended Project Structure
```
ai_codebase_mentor/converters/
├── __init__.py          # Empty (existing)
├── base.py              # RuntimeInstaller ABC + _read_version() (existing)
├── claude.py            # ClaudeInstaller (existing)
├── opencode.py          # OpenCodeInstaller (existing — reference)
└── gemini.py            # GeminiInstaller (NEW)

tests/
├── test_opencode_installer.py    # Reference test structure
└── test_gemini_installer.py      # NEW — TDD, written first as RED tests
```

### Pattern 1: Converter Class Structure

**What:** Subclass `RuntimeInstaller` ABC, implement `install()`, `uninstall()`, `status()`. The `plugin_source` property is inherited from the base class and points to `ai_codebase_mentor/plugin/`.

**When to use:** All runtime converters follow this pattern.

**Example (from opencode.py — exact structure to replicate):**
```python
class GeminiInstaller(RuntimeInstaller):
    def _resolve_dest(self, target: str) -> Path:
        if target == "global":
            config_dir = os.environ.get("GEMINI_CONFIG_DIR")
            if config_dir:
                return Path(config_dir).expanduser() / "codebase-wizard"
            return Path.home() / ".gemini" / "codebase-wizard"
        return Path.cwd() / ".gemini" / "codebase-wizard"

    def install(self, source: Path, target: str = "global") -> None:
        ...

    def uninstall(self, target: str = "global") -> None:
        ...

    def status(self) -> dict:
        ...
```

### Pattern 2: Agent Frontmatter Conversion

**What:** Line-by-line YAML parser that strips/transforms specific fields. Gemini uses `tools:` as a YAML array (one tool per line, `  - tool_name` format).

**When to use:** For all `.md` files in the `agents/` source directory.

**Example (ported from GSD convertClaudeToGeminiAgent):**
```python
GEMINI_TOOL_MAP = {
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "replace",
    "Bash": "run_shell_command",
    "Glob": "glob",
    "Grep": "search_file_content",
    "WebSearch": "google_web_search",
    "WebFetch": "web_fetch",
    "TodoWrite": "write_todos",
    "AskUserQuestion": "ask_user",
}

def _convert_gemini_tool_name(tool: str) -> str | None:
    """Returns None for tools that should be excluded."""
    base = tool.split("(")[0]   # strip path scope annotation
    if base.startswith("mcp__"):
        return None             # excluded: auto-discovered
    if base in ("Task", "Agent"):
        return None             # excluded: auto-registered
    return GEMINI_TOOL_MAP.get(base, base.lower())

def _convert_agent_frontmatter(content: str) -> str:
    # ... line-by-line parser
    # Output tools as YAML array:
    #   tools:
    #     - read_file
    #     - run_shell_command
```

**Critical difference from OpenCode:** OpenCode outputs `tools:\n  read_file: true` (object). Gemini outputs `tools:\n  - read_file` (array).

**Verified from live `~/.gemini/agents/gsd-codebase-mapper.md`:**
```yaml
---
name: gsd-codebase-mapper
description: Explores codebase and writes structured analysis documents...
tools:
  - read_file
  - run_shell_command
  - search_file_content
  - glob
  - write_file
---
```

### Pattern 3: TOML Command Conversion

**What:** Convert Markdown+YAML frontmatter commands to two-field TOML files. Extension changes from `.md` to `.toml`.

**When to use:** For all `.md` files in the `commands/` source directory.

**Example (ported from GSD convertClaudeToGeminiToml):**
```python
import json

def _convert_command_to_toml(content: str) -> str:
    """Convert Claude Code Markdown command to Gemini TOML format."""
    # Apply content transforms first
    content = _rewrite_paths(content)
    content = _strip_sub_tags(content)
    content = _escape_template_vars(content)

    if not content.startswith("---"):
        return f"prompt = {json.dumps(content)}\n"

    # Extract frontmatter
    rest = content[3:]
    close_idx = re.search(r'\n---(\n|$)', rest)
    if not close_idx:
        return f"prompt = {json.dumps(content)}\n"

    frontmatter = rest[:close_idx.start()]
    body = rest[close_idx.end():].strip()

    # Extract description from frontmatter
    description = ""
    for line in frontmatter.splitlines():
        if line.strip().startswith("description:"):
            description = line.strip()[len("description:"):].strip().strip('"\'')
            break

    toml = ""
    if description:
        toml += f"description = {json.dumps(description)}\n"
    toml += f"prompt = {json.dumps(body)}\n"
    return toml
```

**Verified TOML format from live `~/.gemini/commands/gsd/add-phase.toml`:**
```toml
description = "Add phase to end of current milestone in roadmap"
prompt = "..."
```

### Pattern 4: Content Transform Helpers

**What:** Three standalone helper functions applied to agent bodies and command content.

```python
PATH_REWRITES_GEMINI = [
    ("$HOME/.claude", "$HOME/.gemini"),
    ("~/.claude", "~/.gemini"),
]

def _rewrite_paths(content: str) -> str:
    for old, new in PATH_REWRITES_GEMINI:
        content = content.replace(old, new)
    return content

def _escape_template_vars(content: str) -> str:
    """${VAR} -> $VAR to avoid Gemini templateString() conflicts."""
    return re.sub(r'\$\{(\w+)\}', r'$\1', content)

def _strip_sub_tags(content: str) -> str:
    """<sub>text</sub> -> *(text)* for terminal rendering."""
    return re.sub(r'<sub>(.*?)</sub>', r'*(\1)*', content)
```

**Note on path rewrite ordering:** `$HOME/.claude` must be replaced before `~/.claude` to avoid partial match issues. Longer/more-specific string first.

### Pattern 5: _get_converters() Registration

**What:** Single line addition to `cli.py` to register the new converter.

```python
def _get_converters():
    """Lazy import converters to avoid import errors if optional deps missing."""
    from ai_codebase_mentor.converters.claude import ClaudeInstaller
    from ai_codebase_mentor.converters.opencode import OpenCodeInstaller
    from ai_codebase_mentor.converters.gemini import GeminiInstaller   # ADD THIS
    return {
        "claude": ClaudeInstaller,
        "opencode": OpenCodeInstaller,
        "gemini": GeminiInstaller,   # ADD THIS
    }
```

**Effect:** Automatically enables `--for gemini`, `--for all`, and `status` for Gemini with no other CLI changes.

### Pattern 6: Test Fixture Pattern

**What:** Same fixture pattern as `test_opencode_installer.py` — `source_plugin_dir` copies real plugin to tmp; `installer` fixture patches `Path.home()` and `monkeypatch.chdir()`.

```python
REAL_PLUGIN_SOURCE = Path(__file__).parent.parent / "ai_codebase_mentor" / "plugin"

@pytest.fixture
def source_plugin_dir(tmp_path):
    src = tmp_path / "plugin-source"
    shutil.copytree(REAL_PLUGIN_SOURCE, src)
    return src

@pytest.fixture
def installer(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    return GeminiInstaller()
```

**Note:** The existing `test_opencode_installer.py` uses `Path(__file__).parent.parent / "plugins" / "codebase-wizard"` — verify whether this points to `ai_codebase_mentor/plugin` or a separate `plugins/` directory. The real plugin source for the base class is `ai_codebase_mentor/plugin/`. The opencode test used a different path (`plugins/codebase-wizard/`), so gemini tests should consistently use `ai_codebase_mentor/plugin/`.

### Anti-Patterns to Avoid

- **Reusing opencode.py's `_convert_agent_frontmatter`:** They look similar but have different output formats (object vs array). Build a separate Gemini-specific version.
- **Using `yaml.safe_load` for frontmatter parsing:** The existing converters use line-by-line parsing intentionally to avoid the `pyyaml` dependency. Follow the same approach.
- **Calling `tomllib` for TOML writing:** Use `json.dumps()` for string escaping. `tomllib` is read-only (parse only).
- **Applying content transforms to frontmatter during agent conversion:** The `${VAR}` escape and `<sub>` strip should apply to the agent BODY, not the frontmatter.
- **Forgetting path scope annotations:** `"Write(.code-wizard/**)"` must be stripped to `"Write"` before tool name mapping. The `tool.split("(")[0]` pattern handles this.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TOML string escaping | Custom escape function | `json.dumps(string)` | JSON strings are valid TOML basic strings; already handles `"`, `\`, newlines, and Unicode |
| TOML parsing (test validation) | String regex assertions | `tomllib.loads()` (Python 3.11+) | stdlib, no deps; already available in dev environment |
| Recursive skills copy | Manual file loop | `shutil.copytree()` | Handles nested directory structures (skills have subdirectories) |
| Agent frontmatter extraction | Full YAML parser | Line-by-line regex parser | Avoids `pyyaml` dep; pattern already proven in opencode.py |

**Key insight:** The TOML output for Gemini commands is intentionally simple (two fields: `description` and `prompt`). No TOML library needed for generation — `json.dumps()` handles escaping perfectly.

---

## Common Pitfalls

### Pitfall 1: TOML String Quoting
**What goes wrong:** Generating invalid TOML by using Python `repr()` or naive string concatenation.
**Why it happens:** TOML basic strings require `"` quotes with JSON-style escaping (`\n`, `\t`, `\\`, `\"`).
**How to avoid:** Use `json.dumps(value)` for all TOML string values. This is exactly what GSD does (`JSON.stringify()`).
**Warning signs:** TOML parse error in tests, or missing escape for embedded newlines in `prompt =` field.

### Pitfall 2: `${VAR}` Escape Applied in Wrong Scope
**What goes wrong:** Escaping `${VAR}` patterns in agent frontmatter, breaking YAML parsing.
**Why it happens:** The transform should apply only to the agent body (after the closing `---`), not the frontmatter.
**How to avoid:** In `_convert_agent_frontmatter()`, apply `_escape_template_vars()` and `_strip_sub_tags()` only to the `body` variable after splitting on `---`.
**Warning signs:** Test agent with `${PHASE}` in frontmatter description breaks YAML structure.

### Pitfall 3: Path Rewrite Order (for content with both patterns)
**What goes wrong:** `~/.claude` replacement leaving partial `$HOME` → `$HOME/.gemini` doesn't match because `$HOME/.claude` was already partially replaced.
**Why it happens:** If `~/.claude` is replaced first and `$HOME/.claude` contains `~/.claude`, you get double-replacement.
**How to avoid:** In `PATH_REWRITES_GEMINI`, place `$HOME/.claude` before `~/.claude` (more specific first).
**Warning signs:** Test with `$HOME/.claude/plugins` shows `$HOME/.gemini/plugins` correctly but `~/.claude` variant fails.

### Pitfall 4: Skills Path — Singular vs Plural
**What goes wrong:** Writing to `skills/` (plural) instead of `skill/` (singular).
**Why it happens:** The source directory in the plugin is `skills/` (plural), but the destination must be `skill/` (singular) to match Gemini CLI's convention.
**How to avoid:** Always map `skills_src = source / "skills"` → `destination / "skill"` (same as opencode.py pattern).
**Warning signs:** Gemini CLI cannot discover skills after install.

### Pitfall 5: GEMINI_CONFIG_DIR Not Honored
**What goes wrong:** `_resolve_dest()` ignores the `GEMINI_CONFIG_DIR` environment variable.
**Why it happens:** OpenCode has no env var override so the pattern wasn't needed there.
**How to avoid:** In `_resolve_dest()`, check `os.environ.get("GEMINI_CONFIG_DIR")` before falling back to `Path.home() / ".gemini"`.
**Warning signs:** Test with `GEMINI_CONFIG_DIR` set fails to write to expected directory.

### Pitfall 6: `allowed_tools:` vs `allowed-tools:` Key Name
**What goes wrong:** Parser only checks for `allowed_tools:` but the source YAML uses `allowed_tools:` (underscore).
**Why it happens:** GSD code checks for `allowed-tools:` (hyphen), but Claude Code plugin uses `allowed_tools:` (underscore). The two codebases differ here.
**How to avoid:** Inspect the actual source agent file at `ai_codebase_mentor/plugin/agents/codebase-wizard-agent.md` — it uses `allowed_tools:` (underscore, confirmed). Match that key name in the parser.
**Warning signs:** No tools appear in converted agent file.

---

## Code Examples

Verified patterns from official sources and live inspection:

### Live Gemini Agent Format (from `~/.gemini/agents/gsd-codebase-mapper.md`)
```yaml
---
name: gsd-codebase-mapper
description: Explores codebase and writes structured analysis documents. Spawned by map-codebase with a focus area (tech, arch, quality, concerns). Writes documents directly to reduce orchestrator context load.
tools:
  - read_file
  - run_shell_command
  - search_file_content
  - glob
  - write_file
---
```
Key: tools is a YAML array, name is kept, no color field.

### Live Gemini Command Format (from `~/.gemini/commands/gsd/add-phase.toml`)
```toml
description = "Add phase to end of current milestone in roadmap"
prompt = "..."
```
Key: only two fields, both are TOML basic strings, `.toml` extension.

### GSD Tool Mapping (from install.js lines 457-468, HIGH confidence)
```javascript
const claudeToGeminiTools = {
  Read: 'read_file',
  Write: 'write_file',
  Edit: 'replace',
  Bash: 'run_shell_command',
  Glob: 'glob',
  Grep: 'search_file_content',
  WebSearch: 'google_web_search',
  WebFetch: 'web_fetch',
  TodoWrite: 'write_todos',
  AskUserQuestion: 'ask_user',
};
```

### GSD `${VAR}` Escape (from install.js line 1141, HIGH confidence)
```javascript
const escapedBody = body.replace(/\$\{(\w+)\}/g, '$$$1');
```
Python equivalent: `re.sub(r'\$\{(\w+)\}', r'$\1', body)`

### GSD `<sub>` Strip (from install.js lines 1039-1041, HIGH confidence)
```javascript
function stripSubTags(content) {
  return content.replace(/<sub>(.*?)<\/sub>/g, '*($1)*');
}
```
Python equivalent: `re.sub(r'<sub>(.*?)</sub>', r'*(\1)*', content)`

### GEMINI_CONFIG_DIR Resolution (from install.js lines 196-205, HIGH confidence)
```
Priority: GEMINI_CONFIG_DIR env var > ~/.gemini
No --config-dir equivalent in this Python CLI (that's a GSD CLI flag, not ours)
```

### Registering in _get_converters() (cli.py)
```python
def _get_converters():
    from ai_codebase_mentor.converters.claude import ClaudeInstaller
    from ai_codebase_mentor.converters.opencode import OpenCodeInstaller
    from ai_codebase_mentor.converters.gemini import GeminiInstaller
    return {
        "claude": ClaudeInstaller,
        "opencode": OpenCodeInstaller,
        "gemini": GeminiInstaller,
    }
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Gemini commands as Markdown | Gemini commands as TOML | Current (verified 2026-03-26) | Must generate `.toml` files, not `.md` |
| Gemini experimental.enableAgents required | Agents work without settings change | Not relevant to this phase | GSD sets this in settings.json; our converter does not touch settings.json |

**Verified current state:**
- Gemini CLI stores config at `~/.gemini/` (verified on this machine)
- Agents at `~/.gemini/agents/*.md` with `tools:` as YAML array
- Commands at `~/.gemini/commands/**/*.toml` with `description` + `prompt` fields
- Skills at `~/.gemini/skills/` (subdirectory per skill)
- `GEMINI_CONFIG_DIR` env var is the official override (verified in GSD source)

---

## Open Questions

1. **`plugins/codebase-wizard` vs `ai_codebase_mentor/plugin` path in tests**
   - What we know: `test_opencode_installer.py` uses `Path(__file__).parent.parent / "plugins" / "codebase-wizard"` but the base class `plugin_source` points to `ai_codebase_mentor/plugin/`
   - What's unclear: Which path the `test_gemini_installer.py` should use
   - Recommendation: Use `ai_codebase_mentor/plugin/` consistently (matches the base class), but read `test_opencode_installer.py` fixture path before finalizing

2. **Skills field stripping**
   - What we know: GSD strips `skills:` from Gemini agents (line 1104-1107) — "causes validation error"
   - What's unclear: Does the codebase-wizard agent have a `skills:` field in its frontmatter?
   - Recommendation: Inspect agent source file before writing parser. Add `skills:` stripping as a safety measure regardless.

3. **TOML command directory structure**
   - What we know: GSD installs Gemini commands to `~/.gemini/commands/gsd/` (nested), but our plugin has flat commands in `commands/*.md`
   - What's unclear: Whether Gemini CLI expects `command/` (singular, as decided) or `commands/` (plural, as GSD uses)
   - Recommendation: The CONTEXT.md decision says `~/.gemini/codebase-wizard/command/` (singular). This is the locked decision — follow it. The GSD uses `commands/` at the root but our plugin is under `codebase-wizard/` subdirectory.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.0+ |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `pytest tests/test_gemini_installer.py -x` |
| Full suite command | `pytest tests/ -m 'not slow'` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GEMINI-01 | Global install writes to `~/.gemini/codebase-wizard/` | unit | `pytest tests/test_gemini_installer.py::test_global_install_creates_agent_files -x` | ❌ Wave 0 |
| GEMINI-02 | Project install writes to `./.gemini/codebase-wizard/` | unit | `pytest tests/test_gemini_installer.py::test_project_install_creates_agent_files -x` | ❌ Wave 0 |
| GEMINI-03 | `allowed_tools:` → `tools:` YAML array | unit | `pytest tests/test_gemini_installer.py::test_agent_tools_array_format -x` | ❌ Wave 0 |
| GEMINI-04 | 10 tool name mappings | unit | `pytest tests/test_gemini_installer.py -k "tool_mapping" -x` | ❌ Wave 0 |
| GEMINI-05 | `color:` stripped | unit | `pytest tests/test_gemini_installer.py::test_color_field_stripped -x` | ❌ Wave 0 |
| GEMINI-06 | Task and mcp__ excluded | unit | `pytest tests/test_gemini_installer.py::test_task_and_mcp_excluded -x` | ❌ Wave 0 |
| GEMINI-07 | Commands → `.toml` files | unit | `pytest tests/test_gemini_installer.py::test_command_converted_to_toml -x` | ❌ Wave 0 |
| GEMINI-08 | `${VAR}` → `$VAR` | unit | `pytest tests/test_gemini_installer.py::test_template_var_escape -x` | ❌ Wave 0 |
| GEMINI-09 | `<sub>` → `*(text)*` | unit | `pytest tests/test_gemini_installer.py::test_sub_tag_conversion -x` | ❌ Wave 0 |
| GEMINI-10 | Path rewriting | unit | `pytest tests/test_gemini_installer.py::test_path_rewriting -x` | ❌ Wave 0 |
| GEMINI-11 | Skills copied verbatim to `skill/` | unit | `pytest tests/test_gemini_installer.py::test_skills_copied_verbatim -x` | ❌ Wave 0 |
| GEMINI-12 | Uninstall removes dir, no-op if absent | unit | `pytest tests/test_gemini_installer.py -k "uninstall" -x` | ❌ Wave 0 |
| GEMINI-15 | TDD test suite covers all rules | unit | `pytest tests/test_gemini_installer.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_gemini_installer.py -x`
- **Per wave merge:** `pytest tests/ -m 'not slow'`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_gemini_installer.py` — covers GEMINI-01 through GEMINI-15 (written RED first, then GREEN)
- [ ] `ai_codebase_mentor/converters/gemini.py` — the converter module itself

*(No framework or fixture infrastructure gaps — pytest and the fixture pattern are already established.)*

---

## Sources

### Primary (HIGH confidence)
- Live filesystem inspection: `~/.gemini/agents/gsd-codebase-mapper.md` — confirmed YAML array `tools:` format
- Live filesystem inspection: `~/.gemini/commands/gsd/add-phase.toml` and `add-todo.toml` — confirmed TOML format with two fields
- GSD source: `/Users/richardhightower/src/get-shit-done/bin/install.js` lines 455-468 — `claudeToGeminiTools` mapping table
- GSD source: install.js lines 488-510 — `convertGeminiToolName()` function
- GSD source: install.js lines 1035-1144 — `stripSubTags()` and `convertClaudeToGeminiAgent()`
- GSD source: install.js lines 1285-1325 — `convertClaudeToGeminiToml()`
- GSD source: install.js lines 196-205 — `GEMINI_CONFIG_DIR` env var resolution
- Existing codebase: `ai_codebase_mentor/converters/opencode.py` — reference implementation pattern
- Existing codebase: `tests/test_opencode_installer.py` — reference test structure
- Python stdlib docs: `tomllib` available since Python 3.11 (local environment: Python 3.13.3)
- Project config: `pyproject.toml` — `requires-python = ">=3.9"`, confirms no tomllib in runtime deps

### Secondary (MEDIUM confidence)
- `~/.gemini/settings.json` directory listing — confirms `agents/`, `commands/`, `skills/` exist as standard dirs
- GSD source: install.js line 2724-2732 — `settings.experimental.enableAgents` for Gemini (deferred from this phase)

### Tertiary (LOW confidence)
- None — all key claims verified from primary sources

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all stdlib, no new deps, verified pattern from opencode.py
- Architecture: HIGH — ported directly from GSD JS source, verified against live Gemini files
- Pitfalls: HIGH — identified from direct code inspection of GSD source and Python-specific concerns
- Tool mappings: HIGH — verified from both GSD source (`claudeToGeminiTools` const) and live agent files

**Research date:** 2026-03-26
**Valid until:** 2026-06-26 (Gemini CLI format is stable; TOML format verified from live files)
