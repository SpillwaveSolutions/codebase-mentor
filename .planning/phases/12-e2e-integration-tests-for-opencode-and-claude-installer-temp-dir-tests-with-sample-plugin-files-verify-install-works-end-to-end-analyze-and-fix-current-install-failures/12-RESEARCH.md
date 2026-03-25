# Phase 12: E2E Integration Tests for OpenCode and Claude Installer - Research

**Researched:** 2026-03-25
**Domain:** Python pytest integration testing + OpenCode installer bug fixes
**Confidence:** HIGH

## Summary

Phase 12 has two distinct deliverables: (1) a correctness fix to `opencode.py` — map `context: fork` in Claude command frontmatter to `subtask: true` in `opencode.json`, and (2) a new E2E integration test file (`tests/test_e2e_installer.py`) that exercises the real install workflow through the CLI against temp dirs.

The current test suite (28 tests across two files) already uses the correct patterns: `monkeypatch.setattr(Path, "home", ...)`, `monkeypatch.chdir(fake_cwd)`, and `shutil.copytree(REAL_PLUGIN_SOURCE, tmp_path)`. These are the right primitives for E2E tests too. The only gap is that existing tests call installer methods directly; E2E tests must call the CLI via Click's `CliRunner` or via `subprocess` with `pip install -e .` already done.

The `context: fork` bug is well-specified in the pending todo. All three bundled commands (`codebase-wizard.md`, `codebase-wizard-export.md`, `codebase-wizard-setup.md`) carry `context: fork`. The fix requires: detect `context: fork` during command iteration in `opencode.py::install()`, accumulate command names that need `subtask: true`, then merge them into `opencode.json` under the `command` key — same merge pattern as `_write_opencode_permissions()`.

**Primary recommendation:** Write the `context: fork` fix first (single method change + opencode.json merge), then write E2E tests that prove the full CLI install workflow produces the correct file outputs including the new `opencode.json` command entries.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| E2E-01 | E2E test: `install --for opencode --project` via CLI writes correct files to temp `.opencode/` dir | Click CliRunner pattern; monkeypatch home + cwd to tmp_path |
| E2E-02 | E2E test: `install --for claude --project` via CLI writes correct files to temp `plugins/` dir | Same CliRunner pattern; assert plugin.json, settings.json, installed_plugins.json |
| E2E-03 | E2E test: `install --for all` invokes both converters in one CLI call | CliRunner; assert both `.opencode/` and `plugins/` dirs created |
| E2E-04 | E2E test: `uninstall --for opencode --project` removes installed files | Install then uninstall; assert dirs gone |
| E2E-05 | E2E test: `status` reports both runtimes after `install --for all` | Assert output contains both "claude: installed" and "opencode: installed" |
| E2E-06 | Fix: `context: fork` → `subtask: true` in `opencode.json` for all three commands | `_write_opencode_permissions` merge pattern extended to `command` key |
| E2E-07 | Test: after install, `opencode.json` contains `command.codebase-wizard.subtask = true` | Assert all three commands get subtask entries |
| E2E-08 | Test: second install is idempotent — `opencode.json` has no duplicate command keys | Install twice; load JSON; assert no duplicate keys and subtask still true |
| E2E-09 | Test: `opencode.json` merge preserves pre-existing keys | Pre-create opencode.json with unrelated key; install; assert both old and new keys present |
| E2E-10 | Test: `--target` is not a valid flag — only `--project` is accepted | CLI invocation with `--target project` returns non-zero exit code |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=7.0 (already in dev deps) | Test runner | Already used in all 28 existing tests |
| click.testing.CliRunner | ships with click>=8.0 | CLI invocation in tests without subprocess | Standard pattern for click-based CLIs; captures stdout/stderr, returns exit code |
| pathlib.Path | stdlib | Temp dir management | Already used throughout; monkeypatch pattern established |
| json | stdlib | Assert opencode.json contents | Already used in test_claude_installer.py for registry assertions |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shutil | stdlib | Copy real plugin source to tmp_path | Already used in source_plugin_dir fixture |
| pytest monkeypatch | ships with pytest | Redirect Path.home() and chdir | Already used in installer fixture; required for both test files |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CliRunner | subprocess + real install | CliRunner is faster and doesn't require actual pip install; subprocess would test published package only |
| monkeypatch Path.home | tempfile.mkdtemp | monkeypatch is cleaner — auto-cleanup, no manual teardown |

**Installation:**
No new dependencies. All libraries already installed:
```bash
# Already satisfied by existing pyproject.toml dev deps:
# pytest>=7.0, click>=8.0
pip install -e ".[dev]"
```

---

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── test_claude_installer.py    # existing: 14 unit tests (all pass)
├── test_opencode_installer.py  # existing: 14 unit tests (all pass) — add 3 subtask tests here
└── test_e2e_installer.py       # NEW: E2E tests via CliRunner
```

The `context: fork` → `subtask: true` tests belong in `test_opencode_installer.py` (they test opencode.py behavior), not in the new E2E file.

### Pattern 1: CliRunner for CLI E2E Tests
**What:** Click's `CliRunner` invokes the CLI entry point in-process. It captures stdout/stderr and returns an exit code. The monkeypatch fixture redirects `Path.home()` and `cwd()` before the runner invokes the command.
**When to use:** All CLI-level tests where we want to verify the full command path from `cli.py` through to file writes.
**Example:**
```python
# Source: Click testing docs / existing test pattern in this project
from click.testing import CliRunner
from ai_codebase_mentor.cli import main

def test_cli_install_opencode_project(installer_env, tmp_path):
    """install --for opencode --project writes files to .opencode/codebase-wizard/."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "opencode", "--project"])
    assert result.exit_code == 0, f"CLI failed: {result.output}"
    dest = tmp_path / "cwd" / ".opencode" / "codebase-wizard"
    assert dest.exists()
    assert (dest / "command" / "codebase-wizard.md").exists()
```

### Pattern 2: Shared `installer_env` Fixture
**What:** A single fixture that sets up both `fake_home` and `fake_cwd` as temp dirs, patches `Path.home()` and `monkeypatch.chdir()`, and returns `tmp_path` for assertions.
**When to use:** All E2E tests in `test_e2e_installer.py`.
**Example:**
```python
@pytest.fixture
def installer_env(tmp_path, monkeypatch):
    """Redirect home() and cwd() to temp dirs for full CLI isolation."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    return tmp_path
```

### Pattern 3: context:fork Detection and opencode.json Merge
**What:** In `opencode.py::install()`, after iterating commands, collect names where `context: fork` appears in frontmatter, then merge into `opencode.json` under `command` key — exactly like `_write_opencode_permissions()` merges `permission` keys.
**When to use:** In `OpenCodeInstaller.install()`, called after command files are written.
**Example:**
```python
# In install(), after command copy loop:
fork_commands = []
for cmd_file in commands_src.glob("*.md"):
    content = cmd_file.read_text(encoding="utf-8")
    if _has_context_fork(content):
        fork_commands.append(cmd_file.stem)  # e.g. "codebase-wizard-export"
    content = _rewrite_paths(content)
    (command_dst / cmd_file.name).write_text(content, encoding="utf-8")

# After _write_opencode_permissions:
if fork_commands:
    self._write_opencode_subtasks(destination, fork_commands)
```

### Pattern 4: Context-Fork Detection Helper
**What:** Pure function that reads frontmatter and returns True if `context: fork` appears.
**When to use:** Called per command file during install.
**Example:**
```python
def _has_context_fork(content: str) -> bool:
    """Return True if frontmatter contains 'context: fork'."""
    if not content.startswith("---"):
        return False
    rest = content[3:]
    close_idx = re.search(r'\n---(\n|$)', rest)
    if not close_idx:
        return False
    frontmatter = rest[:close_idx.start()]
    return bool(re.search(r'^context:\s*fork\s*$', frontmatter, re.MULTILINE))
```

### Anti-Patterns to Avoid
- **Testing against real home directory:** Never call `installer.install()` without monkeypatching `Path.home()` — it will write to the real `~/.config/opencode/`.
- **Using `--target` flag:** The CLI uses `--project` (a flag, not `--target value`). Writing tests that use `--target` documents a real bug. The test should assert that `--target` fails with a non-zero exit code.
- **Overwriting opencode.json instead of merging:** The `_write_opencode_subtasks()` method must merge, not overwrite. The existing `_write_opencode_permissions()` shows the correct pattern.
- **Separate opencode.json file for subtasks:** Do not write a second `opencode.json` — merge `command` entries into the same file that `_write_opencode_permissions()` writes to.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI test invocation | subprocess + shell | `click.testing.CliRunner` | CliRunner is in-process, captures stdout/stderr cleanly, no PATH issues |
| JSON merge logic | Custom deep-merge | Existing `_write_opencode_permissions()` pattern | Same file, same merge pattern — extend it, don't duplicate |
| YAML frontmatter parse for `context:` | Full YAML library | Simple regex `^context:\s*fork\s*$` in multiline mode | Frontmatter is already parsed line-by-line in `_convert_agent_frontmatter()`; same approach works |
| Temp dir management | `os.makedirs` + manual cleanup | pytest `tmp_path` fixture | Auto-cleaned, isolated per test |

---

## Common Pitfalls

### Pitfall 1: Test Source vs. Bundled Source Mismatch
**What goes wrong:** The existing unit tests use `plugins/codebase-wizard` as the install source (copied to tmp_path via `source_plugin_dir` fixture). The CLI's `plugin_source` property points to `ai_codebase_mentor/plugin`. These are two different directories. E2E tests that go through the CLI use the bundled source automatically — no `source_plugin_dir` fixture needed.
**Why it happens:** The base class `RuntimeInstaller.plugin_source` resolves relative to the installed package, not the repo root.
**How to avoid:** E2E tests should NOT pass `source_plugin_dir` to anything. They invoke the CLI which uses `installer.plugin_source` automatically.
**Warning signs:** Test references `plugins/codebase-wizard` path — that's unit test territory, not E2E.

### Pitfall 2: opencode.json Location
**What goes wrong:** `_write_opencode_permissions()` writes `opencode.json` to `dest.parent` (e.g., `~/.config/opencode/opencode.json`), NOT inside the `codebase-wizard/` subdirectory. The subtask entries must go in the same file.
**Why it happens:** OpenCode reads a single `opencode.json` at the config root, not per-plugin.
**How to avoid:** `_write_opencode_subtasks()` must write to `dest.parent / "opencode.json"` — same path as permissions.
**Warning signs:** Test asserts `opencode.json` exists inside `codebase-wizard/` — that's wrong.

### Pitfall 3: install() Deletes and Recreates the Destination
**What goes wrong:** `OpenCodeInstaller.install()` calls `shutil.rmtree(destination)` then recreates it. But `_write_opencode_permissions()` writes to `dest.parent` (the parent), not to `destination` itself. The subtask write also goes to `dest.parent`. So both calls are safe from the rmtree. However, if a pre-existing `opencode.json` is in `dest.parent`, it must be merged (not overwritten). This is already handled by `_write_opencode_permissions()`.
**How to avoid:** Pass pre-existing `opencode.json` test to confirm merge behavior.

### Pitfall 4: All Three Commands Have context:fork
**What goes wrong:** Only testing `codebase-wizard-export` in the subtask assertion, missing the other two commands.
**How to avoid:** Assert all three command names appear in `opencode.json["command"]`.

### Pitfall 5: CliRunner Does Not Inherit monkeypatch
**What goes wrong:** `monkeypatch.setattr(Path, "home", ...)` affects the test process, but CliRunner runs in the same process — so it does inherit the monkeypatch. However, `monkeypatch.chdir()` changes the process working directory, so all relative paths in `OpenCodeInstaller._resolve_dest("project")` are correctly redirected.
**How to avoid:** Confirm with a minimal test that `Path.cwd()` inside the CLI resolves to the patched cwd.

---

## Code Examples

Verified patterns from the existing codebase:

### Existing fixture pattern (from both test files)
```python
# Source: tests/test_opencode_installer.py and test_claude_installer.py
@pytest.fixture
def installer(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    return OpenCodeInstaller()
```

### CliRunner E2E pattern (new pattern for phase 12)
```python
# Source: Click docs — click.testing.CliRunner
from click.testing import CliRunner
from ai_codebase_mentor.cli import main

@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    return tmp_path

def test_cli_install_opencode_project(cli_env):
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "opencode", "--project"])
    assert result.exit_code == 0, result.output
    dest = cli_env / "cwd" / ".opencode" / "codebase-wizard"
    assert dest.exists()
```

### opencode.json merge (extend existing _write_opencode_permissions pattern)
```python
# Source: ai_codebase_mentor/converters/opencode.py _write_opencode_permissions
def _write_opencode_subtasks(self, dest: Path, fork_commands: list[str]) -> None:
    json_path = dest.parent / "opencode.json"
    data: dict = {}
    if json_path.exists():
        try:
            with json_path.open() as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not parse {json_path}: {e}. Skipping subtask config.",
                  file=sys.stderr)
            return
    if "command" not in data:
        data["command"] = {}
    for cmd_name in fork_commands:
        data["command"][cmd_name] = {"subtask": True}
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
```

### context:fork detection (new pure function)
```python
# Source: pattern consistent with _convert_agent_frontmatter in opencode.py
def _has_context_fork(content: str) -> bool:
    if not content.startswith("---"):
        return False
    rest = content[3:]
    close_idx = re.search(r'\n---(\n|$)', rest)
    if not close_idx:
        return False
    frontmatter = rest[:close_idx.start()]
    return bool(re.search(r'^context:\s*fork\s*$', frontmatter, re.MULTILINE))
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `context: fork` silently dropped | Map to `subtask: true` in opencode.json | Phase 12 | All three commands run in isolated context as intended |
| No CLI-level tests | CliRunner E2E tests verify full install path | Phase 12 | Catches flag regressions (`--target` vs `--project`) and missing registry entries |

**Known bugs confirmed in first real run (from phase description):**
1. `ai-codebase-mentor install --for opencode --target project` — `--target` is not a valid flag. The correct flag is `--project`. CLI exits with error 2 (UsageError). This is correct behavior — the flag name is `--project`. The real run used the wrong flag. No code change needed; but the E2E test should document the correct invocation.
2. `context: fork` silently dropped — real correctness bug. Fix in opencode.py.
3. No `.code-wizard/` created after install — this is expected. `.code-wizard/` is created by the wizard session itself during runtime, not by the installer.
4. No E2E test coverage — gap closed by this phase.

---

## Key Discoveries from Source Code Audit

### Discovery 1: Bundled Plugin vs. Repo Plugin
The CLI uses `ai_codebase_mentor/plugin/` (the bundled copy), not `plugins/codebase-wizard/` (the source-of-truth). The bundled copy was confirmed to contain `context: fork` in all three command files. Both copies are in sync. E2E tests go through the CLI and therefore use the bundled plugin automatically.

### Discovery 2: All Three Commands Need subtask:true
`grep -r "context:"` shows all three bundled commands carry `context: fork`:
- `ai_codebase_mentor/plugin/commands/codebase-wizard.md`
- `ai_codebase_mentor/plugin/commands/codebase-wizard-export.md`
- `ai_codebase_mentor/plugin/commands/codebase-wizard-setup.md`

The `opencode.json` after install must contain all three:
```json
{
  "command": {
    "codebase-wizard": {"subtask": true},
    "codebase-wizard-export": {"subtask": true},
    "codebase-wizard-setup": {"subtask": true}
  }
}
```

### Discovery 3: opencode.json Is Written to dest.parent
`_write_opencode_permissions()` writes to `dest.parent / "opencode.json"` where `dest` is the `codebase-wizard/` dir. For global: `~/.config/opencode/opencode.json`. For project: `./.opencode/opencode.json`. The subtask writer must target the same file.

### Discovery 4: install() Sequence Matters
Current order in `OpenCodeInstaller.install()`:
1. rmtree(destination) then mkdir
2. Convert + copy agents
3. Copy + rewrite commands
4. Copy skills verbatim
5. Copy .claude-plugin
6. `_write_opencode_permissions(destination, target)`

The `context: fork` detection must happen in step 3 (during command iteration). The subtask merge happens as step 6b (after or merged with permissions write). The cleanest implementation: detect during step 3, store in a local list, then call `_write_opencode_subtasks(destination, fork_commands)` after `_write_opencode_permissions`.

### Discovery 5: Current Test Count
28 tests across two files, all pass. Phase 12 adds approximately:
- 3 subtask-related tests to `test_opencode_installer.py`
- 8-10 E2E tests in new `test_e2e_installer.py`
- Target total: ~39 tests

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x (already installed) |
| Config file | none — pytest discovers tests/ automatically |
| Quick run command | `python -m pytest tests/test_opencode_installer.py tests/test_e2e_installer.py -x` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| E2E-01 | CLI install --for opencode --project creates .opencode/ | E2E | `pytest tests/test_e2e_installer.py::test_cli_install_opencode_project -x` | Wave 0 |
| E2E-02 | CLI install --for claude --project creates plugins/ + registry files | E2E | `pytest tests/test_e2e_installer.py::test_cli_install_claude_project -x` | Wave 0 |
| E2E-03 | CLI install --for all creates both dirs | E2E | `pytest tests/test_e2e_installer.py::test_cli_install_all -x` | Wave 0 |
| E2E-04 | CLI uninstall --for opencode --project removes files | E2E | `pytest tests/test_e2e_installer.py::test_cli_uninstall_opencode_project -x` | Wave 0 |
| E2E-05 | CLI status reports both runtimes | E2E | `pytest tests/test_e2e_installer.py::test_cli_status_after_install_all -x` | Wave 0 |
| E2E-06 | opencode.py maps context:fork to subtask:true | unit | `pytest tests/test_opencode_installer.py::test_context_fork_written_to_opencode_json -x` | Wave 0 |
| E2E-07 | All three commands get subtask entries | unit | `pytest tests/test_opencode_installer.py::test_all_fork_commands_get_subtask -x` | Wave 0 |
| E2E-08 | Second install idempotent for subtask entries | unit | `pytest tests/test_opencode_installer.py::test_subtask_idempotent -x` | Wave 0 |
| E2E-09 | opencode.json merge preserves pre-existing keys | unit | `pytest tests/test_opencode_installer.py::test_subtask_merge_preserves_existing -x` | Wave 0 |
| E2E-10 | --target flag fails with usage error | E2E | `pytest tests/test_e2e_installer.py::test_target_flag_invalid -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green (all ~39 tests) before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_e2e_installer.py` — new file; covers E2E-01 through E2E-05, E2E-10
- [ ] Three new test functions in `tests/test_opencode_installer.py` — covers E2E-06 through E2E-09

*(No new framework install needed — pytest and click already available)*

---

## Open Questions

1. **Does OpenCode read opencode.json from the plugin subdirectory or the config root?**
   - What we know: `_write_opencode_permissions()` writes to `dest.parent` (config root), which is consistent with how OpenCode loads permissions.
   - What's unclear: Whether `command` entries in opencode.json must also be at the config root, or if OpenCode would read a per-plugin opencode.json.
   - Recommendation: Follow the existing `dest.parent` pattern. The todo spec also shows this location. Confidence HIGH based on todo spec and existing code pattern.

2. **Should `_write_opencode_subtasks()` be a separate method or merged into `_write_opencode_permissions()`?**
   - What we know: Both write to the same `opencode.json` file. Merging into a single write would avoid two sequential read/write cycles.
   - Recommendation: Keep separate methods for testability, but call them in sequence. The second call will read and merge the file written by the first call. This is idempotent.

---

## Sources

### Primary (HIGH confidence)
- `ai_codebase_mentor/converters/opencode.py` — full source audit, confirmed structure
- `ai_codebase_mentor/converters/claude.py` — registry merge pattern reference
- `tests/test_opencode_installer.py` — confirmed test patterns, fixture shapes
- `tests/test_claude_installer.py` — confirmed fixture shapes, JSON assertion patterns
- `ai_codebase_mentor/cli.py` — confirmed `--project` flag (not `--target`), CliRunner entry point
- `ai_codebase_mentor/plugin/commands/*.md` — confirmed all three have `context: fork`
- `.planning/todos/pending/2026-03-25-map-context-fork-to-opencode-subtask-in-converter.md` — full bug spec

### Secondary (MEDIUM confidence)
- OpenCode docs at `https://opencode.ai/docs/commands/` — confirmed `subtask: true` is the correct field, confirmed it forces subagent invocation (verified via WebFetch)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use; no new deps
- Architecture: HIGH — patterns copied from existing test files; opencode.py structure fully read
- Pitfalls: HIGH — found by direct source inspection (not speculation)
- Bug analysis: HIGH — all five reported failures explained by source code audit

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain — Python + Click + pytest)
