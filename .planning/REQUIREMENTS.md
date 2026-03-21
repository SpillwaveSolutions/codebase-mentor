# Requirements: Milestone v1.2 — OpenCode Converter + PyPI Publish

**Milestone:** v1.2
**Status:** Draft — pending confirmation
**Last updated:** 2026-03-21
**Reference:** `docs/superpowers/specs/2026-03-20-codebase-wizard-multi-runtime-design.md`

---

## OpenCode Converter (`opencode.py`)

The OpenCode converter reads the bundled Claude Code plugin source
(`ai_codebase_mentor/plugin/`) and generates OpenCode-native files at
install time. No runtime artifacts are committed to the repo — they are
generated on install (same Approach A pattern as `claude.py`).

### OPENCODE-01 — Global install path
`ai-codebase-mentor install --for opencode` writes the converted plugin to
`~/.config/opencode/codebase-wizard/`.

### OPENCODE-02 — Project install path
`ai-codebase-mentor install --for opencode --project` writes the converted
plugin to `./.opencode/codebase-wizard/`.

### OPENCODE-03 — Agent frontmatter conversion
`opencode.py` converts Claude agent files (`plugin/agents/*.md`) from
Claude Code format to OpenCode format:

**Schema change:** `allowed_tools:` (PascalCase array) → `tools:` (lowercase object)

```yaml
# Before (Claude Code)
allowed_tools:
  - "Read"
  - "Glob"
  - "Write(.code-wizard/**)"
  - "Bash(node*)"

# After (OpenCode)
tools:
  read: true
  glob: true
  write: true
  bash: true
```

Path-scoped tools (e.g., `Write(.code-wizard/**)`) are stripped of their
scope annotation; the path scope is handled separately via
`opencode.json` permissions (see OPENCODE-06).

### OPENCODE-04 — Tool name special mappings
Beyond simple lowercasing, five tools have special OpenCode names:

| Claude Code | OpenCode |
|-------------|----------|
| `AskUserQuestion` | `question` |
| `SkillTool` | `skill` |
| `TodoWrite` | `todowrite` |
| `WebFetch` | `webfetch` |
| `WebSearch` | `websearch` |

All other tools lowercase directly (`Read` → `read`, `Bash` → `bash`).
`mcp__*` tool names pass through unchanged.

### OPENCODE-05 — Agent metadata normalization
- **`name:` field removed** — OpenCode derives agent name from filename
- **Named colors → hex** — `cyan` → `"#00FFFF"`, `red` → `"#FF0000"`, etc. (13 named colors mapped)
- **`subagent_type: "general-purpose"` → `subagent_type: "general"`**

### OPENCODE-06 — Permission auto-configuration
After writing agent and command files, the converter writes (or updates)
`opencode.json` in the install directory to pre-authorize file access,
eliminating per-file permission prompts during wizard sessions:

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

For project installs, paths reference `./.opencode/codebase-wizard/*`.
Existing `opencode.json` content is merged (not overwritten).

### OPENCODE-07 — Command directory rename
Command files are copied from `plugin/commands/` → `command/` (singular,
flat) in the output directory. Our commands are already flat-named (no
colon namespacing), so only the directory name changes:

```
plugin/commands/codebase-wizard.md        → command/codebase-wizard.md
plugin/commands/codebase-wizard-export.md → command/codebase-wizard-export.md
plugin/commands/codebase-wizard-setup.md  → command/codebase-wizard-setup.md
```

### OPENCODE-08 — Content path rewriting
All file content is rewritten to replace Claude-specific paths with
OpenCode equivalents:
- `~/.claude` → `~/.config/opencode`
- `~/.claude/plugins/` → `~/.config/opencode/`

### OPENCODE-09 — Skills copied verbatim
`plugin/skills/` is copied to `skills/` in the output directory with no
transformation. SKILL.md files are runtime-agnostic and need no
conversion.

### OPENCODE-10 — Clean uninstall
`ai-codebase-mentor uninstall --for opencode` removes the installed
directory. `uninstall --for opencode --project` removes the project-local
copy. Uninstall on a non-existent target is a no-op (no error).

### OPENCODE-11 — Status reporting
`ai-codebase-mentor status` reports OpenCode install state (installed/not
installed, location, version) alongside Claude install state.

### OPENCODE-12 — `--for all` support
`ai-codebase-mentor install --for all` and `uninstall --for all` include
OpenCode in the runtime iteration.

### OPENCODE-13 — TDD test suite
`tests/test_opencode_installer.py` covers:
- Global install writes files to `~/.config/opencode/codebase-wizard/`
- Project install writes files to `./.opencode/codebase-wizard/`
- Idempotent re-install (updates in place)
- Global uninstall removes all installed files
- Project uninstall removes project-local copy
- Uninstall no-op when not installed
- Status after global install
- Status before any install
- Agent tool names lowercased in output files
- Special tool mappings applied (`AskUserQuestion` → `question`)
- `name:` field stripped from agent frontmatter
- Command directory named `command/` (not `commands/`) in output
- `RuntimeError` raised on missing source

---

## PyPI Publish

### PYPI-01 — Workflow trigger
`.github/workflows/publish-pypi.yml` fires only on semver tag push
(`v[0-9]+.[0-9]+.[0-9]+`), not on every push or PR.

### PYPI-02 — Trusted Publishers (OIDC)
The workflow uses PyPI Trusted Publishers for authentication — no
`PYPI_TOKEN` secret required. The workflow requests `id-token: write`
permission for OIDC. One-time human setup: configure publisher on
pypi.org and create a `pypi` GitHub environment.

### PYPI-03 — Build and upload
The workflow builds a source distribution (`sdist`) and wheel
(`bdist_wheel`) via `python -m build`, then uploads to PyPI using
`pypa/gh-action-pypi-publish@release/v1`.

### PYPI-04 — `pyproject.toml` metadata completeness
Add missing fields required for a complete PyPI listing:
`authors`, `readme = "README.md"`, `classifiers`, `[project.urls]`
(Homepage, Repository). Version bumped to `1.2.0` after opencode.py ships.

### PYPI-05 — Version consistency
The version uploaded to PyPI matches the `__version__` string in
`ai_codebase_mentor/__init__.py` and the `version` field in `pyproject.toml`.

### PYPI-06 — Installability
After publish, `pip install ai-codebase-mentor` installs the package from
PyPI and `ai-codebase-mentor --version` outputs the correct version.

### PYPI-07 — No test duplication
The publish workflow does NOT re-run installer smoke tests. Testing is
the responsibility of `test-installer.yml` (runs on push). The publish
workflow runs only: checkout → build → publish.

---

## Out of Scope (v1.2)

- Gemini converter — deferred to v1.4
- Codex converter — deferred to v1.3
- LangChain DeepAgent — deferred to v1.5
- TestPyPI staging — publish goes directly to PyPI
- Changelog automation or release notes generation
- JSONC parser for `opencode.json` (use standard JSON; warn if parse fails)
