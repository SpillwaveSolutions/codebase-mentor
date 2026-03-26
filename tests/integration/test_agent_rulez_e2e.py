"""Agent Rulez end-to-end integration tests.

Proves the complete capture-to-export pipeline:

  1. Setup with real rulez — .claude/hooks.yaml deployed, rulez hook registered
  2. Wizard session — wizard writes structured mentoring turns to .code-wizard/sessions/
  3. Assert session JSON contains hook-event records AND wizard-turn structure
  4. Export — reads session JSON, generates SESSION-TRANSCRIPT.md + CODEBASE.md
  5. Assert exported docs exist under the same session_id, with fixture-specific content

Architecture note:
  Agent Rulez provides security enforcement (blocking rm -rf, force-push).
  capture-session.sh fires on PostToolUse and writes raw tool events.
  The wizard ALSO writes structured mentoring turns (question, anchor, explanation)
  via the Write tool — these are what the export skill consumes.
  Both end up in .code-wizard/sessions/ under their respective session IDs.

Schema contract verified by this test:
  Wizard turns:     {turn, question, anchor, explanation, next_options}
  Hook events:      {hook_event_name, tool_name, tool_input, session_id, timestamp}
  Export consumes:  wizard turns only (question, anchor, explanation fields)

Coverage:
  Claude:   full capture/export e2e (test_agent_rulez_claude_capture_to_export)
  OpenCode: full capture/export e2e (test_agent_rulez_opencode_capture_to_export) — skipped if opencode unavailable

Run:  pytest -m slow tests/integration/test_agent_rulez_e2e.py -v
Skip: included in default 'not slow' deselection via pyproject.toml addopts

Environment:
  Each test gets an isolated folder with its own .claude/ and .opencode/.
  Nothing is written to this project or the developer's global HOME.
"""

import json
import os
import platform
import shutil
import subprocess
import tarfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent.parent
SETUP_SH_REL = (
    "plugins/codebase-wizard/skills/configuring-codebase-wizard/scripts/setup.sh"
)
FIXTURE_PROJECT = REPO_ROOT / "tests" / "fixtures" / "sample-wizard-project"


# ─────────────────────────────────────────────────────────────────────────────
# Dependency probes — lazy, never at import time
# ─────────────────────────────────────────────────────────────────────────────


def _probe_rulez() -> bool:
    return shutil.which("rulez") is not None


def _probe_claude() -> bool:
    if shutil.which("claude") is None:
        return False
    try:
        r = subprocess.run(
            [
                "claude", "-p", "OK",
                "--dangerously-skip-permissions",
                "--max-budget-usd", "0.01",
            ],
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


def _probe_opencode() -> bool:
    """Check that opencode binary exists AND can run headlessly."""
    if shutil.which("opencode") is None:
        return False
    try:
        r = subprocess.run(
            ["opencode", "run", "--dir", "/tmp", "echo hello"],
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode == 0
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Session-scoped availability fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def rulez_available() -> bool:
    return _probe_rulez()


@pytest.fixture(scope="session")
def claude_available() -> bool:
    return _probe_claude()


@pytest.fixture(scope="session")
def opencode_available() -> bool:
    return _probe_opencode()


# ─────────────────────────────────────────────────────────────────────────────
# Isolated integration env — owns .claude/ and .opencode/ completely
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def integration_env(tmp_path) -> Dict[str, Path]:
    """Create a fully isolated integration folder with .claude/ and .opencode/.

    Layout:
        tmp/
          home/                   ← isolated HOME (plugin install + auth)
            .claude/
              auth.json           ← copied from real HOME (auth only, not plugins)
              plugins/            ← plugin installed from current checkout
          project/                ← wizard project (copy of fixture)
            src/main.py
            README.md
            .claude/              ← created by setup.sh (rulez hook, settings)
            .opencode/            ← created by setup.sh for opencode
            .code-wizard/         ← created by setup.sh (config, sessions, docs)

    Nothing from this codebase's own .claude/ or .code-wizard/ is used.
    """
    home = tmp_path / "home"
    isolated_claude = home / ".claude"
    isolated_claude.mkdir(parents=True)

    # Copy only auth credentials — not global plugins, settings, or history
    real_claude = Path.home() / ".claude"
    for auth_file in ("auth.json", ".credentials.json"):
        src = real_claude / auth_file
        if src.exists():
            shutil.copy2(src, isolated_claude / auth_file)

    # Install plugin from current checkout into isolated HOME
    install_result = subprocess.run(
        ["ai-codebase-mentor", "install", "--for", "claude"],
        env={**os.environ, "HOME": str(home)},
        capture_output=True, text=True, timeout=60,
    )
    if install_result.returncode != 0:
        pytest.skip(
            f"ai-codebase-mentor install --for claude failed "
            f"(rc={install_result.returncode}).\nstderr: {install_result.stderr}"
        )

    # Create isolated project from fixture
    project = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project)

    # Locate setup.sh inside the installed plugin cache
    # Installer puts it at: ~/.claude/plugins/cache/codebase-mentor/codebase-wizard/{version}/
    cache_plugin_dir = home / ".claude" / "plugins" / "cache" / "codebase-mentor" / "codebase-wizard"
    if not cache_plugin_dir.exists():
        pytest.skip(
            f"Plugin cache directory not found: {cache_plugin_dir}\n"
            f"ai-codebase-mentor install --for claude may have failed silently."
        )
    version_dirs = sorted([d for d in cache_plugin_dir.iterdir() if d.is_dir()])
    if not version_dirs:
        pytest.skip(f"No versioned plugin directories found under {cache_plugin_dir}")
    plugin_dir = version_dirs[-1]
    plugin_setup_sh = plugin_dir / "skills" / "configuring-codebase-wizard" / "scripts" / "setup.sh"
    if not plugin_setup_sh.exists():
        pytest.skip(f"setup.sh not found in installed plugin: {plugin_setup_sh}")

    return {
        "home": home,
        "project": project,
        "setup_sh": plugin_setup_sh,
        "plugin_dir": plugin_dir,
    }


@pytest.fixture
def opencode_integration_env(tmp_path) -> Dict[str, Path]:
    """Create a fully isolated integration folder for OpenCode testing.

    Same layout as integration_env but installs with --for opencode:
        tmp/
          home/                   <- isolated HOME (plugin install + auth)
            .claude/
              auth.json           <- copied from real HOME (auth only, not plugins)
            .opencode/            <- created by installer for opencode
          project/                <- wizard project (copy of fixture)
            src/main.py
            README.md
            .claude/              <- created by setup.sh (rulez hook, settings)
            .opencode/            <- created by setup.sh for opencode
            .code-wizard/         <- created by setup.sh (config, sessions, docs)

    Nothing from this codebase's own .claude/ or .code-wizard/ is used.
    """
    home = tmp_path / "home"
    isolated_claude = home / ".claude"
    isolated_claude.mkdir(parents=True)

    # Copy only auth credentials — not global plugins, settings, or history
    real_claude = Path.home() / ".claude"
    for auth_file in ("auth.json", ".credentials.json"):
        src = real_claude / auth_file
        if src.exists():
            shutil.copy2(src, isolated_claude / auth_file)

    # Install plugin from current checkout into isolated HOME (opencode variant)
    install_result = subprocess.run(
        ["ai-codebase-mentor", "install", "--for", "opencode"],
        env={**os.environ, "HOME": str(home)},
        capture_output=True, text=True, timeout=60,
    )
    if install_result.returncode != 0:
        pytest.skip(
            f"ai-codebase-mentor install --for opencode failed "
            f"(rc={install_result.returncode}).\nstderr: {install_result.stderr}"
        )

    # Create isolated project from fixture
    project = tmp_path / "project"
    shutil.copytree(FIXTURE_PROJECT, project)

    # Locate setup.sh inside the installed plugin cache
    # Installer puts it at: ~/.claude/plugins/cache/codebase-mentor/codebase-wizard/{version}/
    cache_plugin_dir = home / ".claude" / "plugins" / "cache" / "codebase-mentor" / "codebase-wizard"
    if not cache_plugin_dir.exists():
        pytest.skip(
            f"Plugin cache directory not found: {cache_plugin_dir}\n"
            f"ai-codebase-mentor install --for opencode may have failed silently."
        )
    version_dirs = sorted([d for d in cache_plugin_dir.iterdir() if d.is_dir()])
    if not version_dirs:
        pytest.skip(f"No versioned plugin directories found under {cache_plugin_dir}")
    plugin_dir = version_dirs[-1]
    plugin_setup_sh = plugin_dir / "skills" / "configuring-codebase-wizard" / "scripts" / "setup.sh"
    if not plugin_setup_sh.exists():
        pytest.skip(f"setup.sh not found in installed plugin: {plugin_setup_sh}")

    return {
        "home": home,
        "project": project,
        "setup_sh": plugin_setup_sh,
        "plugin_dir": plugin_dir,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI helpers
# ─────────────────────────────────────────────────────────────────────────────


def _env_for(env: Dict[str, Path]) -> Dict[str, str]:
    return {**os.environ, "HOME": str(env["home"])}


def run_setup(env: Dict[str, Path], runtime: str = "claude") -> subprocess.CompletedProcess:
    """Run setup.sh inside the isolated project directory."""
    return subprocess.run(
        ["bash", str(env["setup_sh"]), runtime],
        cwd=str(env["project"]),
        env=_env_for(env),
        capture_output=True, text=True, timeout=60,
        input="1\n",   # select ".code-wizard/" if prompted for storage location
    )


def run_claude(
    prompt: str,
    env: Dict[str, Path],
    budget: float = 1.00,
    timeout: int = 240,
) -> subprocess.CompletedProcess:
    """Run claude -p with plugin loaded from isolated install dir.

    Uses --plugin-dir instead of HOME override so macOS keychain auth works.
    The plugin files come from the current checkout's installed location.
    """
    return subprocess.run(
        [
            "claude", "-p", prompt,
            "--plugin-dir", str(env["plugin_dir"]),
            "--dangerously-skip-permissions",
            "--max-budget-usd", str(budget),
        ],
        cwd=str(env["project"]),
        capture_output=True, text=True, timeout=timeout,
    )


def run_opencode(
    prompt: str,
    env: Dict[str, Path],
    timeout: int = 240,
) -> subprocess.CompletedProcess:
    """Run opencode with positional message args and --dir for project directory.

    Uses positional message args (NOT --command which hangs silently per Phase 13 decision).
    """
    return subprocess.run(
        ["opencode", "run", "--dir", str(env["project"]), prompt],
        cwd=str(env["project"]),
        env={**os.environ, "HOME": str(env["home"])},
        capture_output=True, text=True, timeout=timeout,
    )


def find_output(project: Path, filename: str) -> Optional[Path]:
    """Find wizard output under .code-wizard/docs/*/<filename> (session_id is dynamic)."""
    matches = list((project / ".code-wizard" / "docs").glob(f"*/{filename}"))
    return matches[0] if matches else None


def load_session_files(project: Path) -> List[Dict[str, Any]]:
    """Load all JSON files from .code-wizard/sessions/."""
    sessions = []
    sessions_dir = project / ".code-wizard" / "sessions"
    if sessions_dir.exists():
        for path in sessions_dir.glob("*.json"):
            try:
                sessions.append(json.loads(path.read_text()))
            except (json.JSONDecodeError, OSError):
                pass
    return sessions


# ─────────────────────────────────────────────────────────────────────────────
# Phase assertion helpers
# ─────────────────────────────────────────────────────────────────────────────


def assert_phase1_setup(project: Path) -> None:
    """Phase 1: verify setup.sh created all required artifacts."""
    # config.json — storage resolved
    config_path = project / ".code-wizard" / "config.json"
    assert config_path.exists(), "setup.sh did not create .code-wizard/config.json"
    config = json.loads(config_path.read_text())
    assert config.get("resolved_storage") == ".code-wizard", (
        f"config.json resolved_storage is wrong: {config}"
    )

    # .claude/hooks.yaml — rules file rulez reads at hook-fire time
    hooks_yaml = project / ".claude" / "hooks.yaml"
    assert hooks_yaml.exists(), (
        ".claude/hooks.yaml missing.\n"
        "deploy_hooks() must copy agent-rulez.yaml → .claude/hooks.yaml before rulez install."
    )
    hooks_text = hooks_yaml.read_text()
    assert "rules:" in hooks_text, (
        ".claude/hooks.yaml missing 'rules:' top-level key — wrong schema"
    )
    assert "capture-session" in hooks_text, (
        ".claude/hooks.yaml does not contain capture-session rule"
    )

    # capture-session.sh — deployed and executable
    capture_sh = project / ".code-wizard" / "scripts" / "capture-session.sh"
    assert capture_sh.exists(), ".code-wizard/scripts/capture-session.sh not deployed"
    assert os.access(str(capture_sh), os.X_OK), "capture-session.sh not executable"

    # .claude/settings.json — rulez hook registered (PostToolUse)
    settings_path = project / ".claude" / "settings.json"
    assert settings_path.exists(), (
        ".claude/settings.json missing — rulez install did not register hook"
    )
    settings = json.loads(settings_path.read_text())
    post_hooks = settings.get("hooks", {}).get("PostToolUse", [])
    assert post_hooks, (
        ".claude/settings.json has no PostToolUse hooks — rulez install failed"
    )
    hook_commands = [
        h.get("command", "")
        for entry in post_hooks
        for h in entry.get("hooks", [])
    ]
    assert any("rulez" in cmd for cmd in hook_commands), (
        f"PostToolUse hook does not reference rulez binary.\nFound: {hook_commands}"
    )


def assert_phase3_session_captured(project: Path) -> List[Dict[str, Any]]:
    """Phase 3: verify session JSON exists and contains wizard-turn-shaped records.

    The wizard always writes structured turns (question, anchor, explanation) via
    the Write tool. Agent Rulez capture-session.sh may also have written raw hook
    events (tool_name, tool_input). Both land in .code-wizard/sessions/*.json.

    We assert:
    - At least one session file exists
    - At least one session has a 'turns' array with ≥1 entry
    - At least one turn has 'question' field (wizard-written, export-consumable)
    """
    sessions_dir = project / ".code-wizard" / "sessions"
    session_files = list(sessions_dir.glob("*.json")) if sessions_dir.exists() else []
    assert session_files, (
        "No session JSON files in .code-wizard/sessions/.\n"
        "The wizard must write structured turns via the Write tool (Step 6 of Answer Loop)."
    )

    all_sessions = load_session_files(project)
    assert all_sessions, "Session files exist but could not be parsed as JSON"

    all_turns = [turn for s in all_sessions for turn in s.get("turns", [])]
    assert all_turns, (
        "Session JSON exists but has 0 turns.\n"
        f"Session file count: {len(session_files)}\n"
        f"First session preview: {json.dumps(all_sessions[0], indent=2)[:400]}"
    )

    # At least one turn must have 'question' — proves wizard wrote it, not just rulez raw events
    wizard_turns = [t for t in all_turns if "question" in t]
    assert wizard_turns, (
        "No turns have 'question' field. Session contains only raw hook events.\n"
        "The SKILL.md Step 6 must always write structured wizard turns regardless of Agent Rulez.\n"
        "Raw hook events (tool_name/tool_input) cannot be consumed by the export skill.\n"
        f"Turn fields found: {sorted({k for t in all_turns for k in t.keys()})}"
    )

    return all_sessions


def assert_phase3_rulez_fired(project: Path) -> None:
    """Phase 3b: verify Agent Rulez capture-session.sh actually recorded hook events.

    Agent Rulez writes raw tool events to .code-wizard/sessions/{claude-session-id}.json
    via capture-session.sh on PostToolUse. These events have a different schema from
    wizard turns: they contain hook_event_name, tool_name, tool_input fields.

    A test that only checks for wizard turns (question field) cannot detect whether
    rulez hooks fired. This assertion closes that gap.
    """
    all_sessions = load_session_files(project)

    # Collect all turns across all session files (wizard and rulez write to different files)
    all_turns = [turn for s in all_sessions for turn in s.get("turns", [])]

    # Look for turns shaped like Agent Rulez hook events
    hook_event_turns = [
        t for t in all_turns
        if "hook_event_name" in t or "tool_name" in t
    ]

    assert hook_event_turns, (
        "No Agent Rulez hook events found in .code-wizard/sessions/.\n"
        "capture-session.sh must fire on PostToolUse and write raw tool events.\n"
        "Fields expected: hook_event_name, tool_name, tool_input, session_id, timestamp\n"
        f"Session files found: {len(all_sessions)}\n"
        f"Turn fields across all sessions: {sorted({k for t in all_turns for k in t.keys()})}\n"
        "Possible causes:\n"
        "  1. rulez install did not register the PostToolUse hook\n"
        "  2. capture-session.sh was not deployed to .code-wizard/scripts/\n"
        "  3. .claude/hooks.yaml was not written (rulez reads this at hook-fire time)\n"
        "  4. rulez binary not found on PATH during hook execution"
    )

    # At least one hook event must have tool_name — proves it fired on a real tool call
    tool_events = [t for t in hook_event_turns if t.get("tool_name")]
    assert tool_events, (
        "Hook events exist but none have tool_name field.\n"
        f"Hook event fields found: {sorted({k for t in hook_event_turns for k in t.keys()})}\n"
        "Expected shape: {hook_event_name, tool_name, tool_input, session_id, timestamp}"
    )


def assert_phase5_docs(project: Path, sessions_before_export: List[Dict[str, Any]]) -> None:
    """Phase 5: verify export generated SESSION-TRANSCRIPT.md and CODEBASE.md.

    Also verifies the docs reference fixture-specific content, proving the wizard
    actually scanned the project (not just produced a generic boilerplate response).
    """
    transcript = find_output(project, "SESSION-TRANSCRIPT.md")
    assert transcript is not None, (
        "SESSION-TRANSCRIPT.md not found under .code-wizard/docs/*/.\n"
        "Export skill must generate it from the session JSON."
    )
    transcript_text = transcript.read_text()
    assert len(transcript_text) > 200, (
        f"SESSION-TRANSCRIPT.md too small ({len(transcript_text)} bytes)"
    )
    assert "calculate" in transcript_text or "src/main.py" in transcript_text, (
        "SESSION-TRANSCRIPT.md does not reference fixture content (calculate / src/main.py).\n"
        f"Preview: {transcript_text[:500]}"
    )

    codebase_md = find_output(project, "CODEBASE.md")
    assert codebase_md is not None, (
        "CODEBASE.md not found under .code-wizard/docs/*/.\n"
        "Export skill must generate CODEBASE.md in describe mode."
    )
    codebase_text = codebase_md.read_text()
    assert len(codebase_text) > 100, (
        f"CODEBASE.md too small ({len(codebase_text)} bytes)"
    )
    has_section = any(
        h in codebase_text
        for h in ("## Overview", "# Overview", "## Entry Points", "## Constraints")
    )
    assert has_section, (
        f"CODEBASE.md missing expected section headings (Overview/Entry Points/Constraints).\n"
        f"Preview: {codebase_text[:500]}"
    )

    # Verify session_id continuity: docs directory name matches the session_id in JSON
    # (proves export used the captured session, not an independent LLM generation)
    session_ids_in_json = {
        s.get("session_id") for s in sessions_before_export if s.get("session_id")
    }
    if session_ids_in_json:
        docs_dirs = list((project / ".code-wizard" / "docs").iterdir()) if (
            project / ".code-wizard" / "docs"
        ).exists() else []
        docs_session_ids = {d.name for d in docs_dirs if d.is_dir()}
        overlap = session_ids_in_json & docs_session_ids
        assert overlap, (
            f"Docs session_id does not match any session JSON session_id.\n"
            f"Session JSON IDs: {session_ids_in_json}\n"
            f"Docs directories: {docs_session_ids}\n"
            "Export must write docs to {{resolved_storage}}/docs/{{session_id}}/ where "
            "session_id comes from the session JSON."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Failure artifact bundle helper
# ─────────────────────────────────────────────────────────────────────────────


def _collect_failure_artifacts(
    project: Path,
    env: Dict[str, Path],
    label: str,
    subprocess_results: Dict[str, Any],
    assertion_error: BaseException,
) -> None:
    """Create a comprehensive failure artifact bundle for CI diagnostics.

    Writes to artifacts/opencode-rulez-failure-{timestamp}/ under the repo root.
    Produces FAILURE_REPORT.md and a .tar.gz archive of the entire artifact dir.
    """
    artifact_dir = (
        REPO_ROOT / "artifacts"
        / f"{label}-rulez-failure-{datetime.now().strftime('%Y%m%dT%H%M%S')}"
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)

    # ── Project snapshot ──────────────────────────────────────────────────────
    try:
        shutil.copytree(str(project), str(artifact_dir / "project-snapshot"))
    except Exception:
        pass

    # ── Version info ──────────────────────────────────────────────────────────
    version_info: Dict[str, str] = {}
    version_cmds = [
        ("rulez", ["rulez", "--version"]),
        ("opencode", ["opencode", "--version"]),
        ("ai-codebase-mentor", ["pip", "show", "ai-codebase-mentor"]),
        ("python", ["python", "--version"]),
    ]
    for name, cmd in version_cmds:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            version_info[name] = (r.stdout + r.stderr).strip()
        except Exception as e:
            version_info[name] = f"error: {e}"
    try:
        version_info["platform"] = platform.platform()
    except Exception:
        version_info["platform"] = "unknown"

    # ── Subprocess results ────────────────────────────────────────────────────
    proc_lines: List[str] = []
    for step_name, result in subprocess_results.items():
        if result is None:
            proc_lines.append(f"## {step_name}: (not run)\n")
            continue
        proc_lines.append(f"## {step_name}")
        proc_lines.append(f"returncode: {result.returncode}")
        proc_lines.append(f"stdout:\n{result.stdout or '(empty)'}")
        proc_lines.append(f"stderr:\n{result.stderr or '(empty)'}")
        proc_lines.append("")
    (artifact_dir / "subprocess-results.txt").write_text("\n".join(proc_lines))

    # ── Config files ──────────────────────────────────────────────────────────
    config_files = [
        project / ".claude" / "hooks.yaml",
        project / ".claude" / "settings.json",
        project / ".code-wizard" / "config.json",
        project / ".code-wizard" / "scripts" / "capture-session.sh",
    ]
    configs_dir = artifact_dir / "config-files"
    configs_dir.mkdir(exist_ok=True)
    for cfg in config_files:
        if cfg.exists():
            try:
                dest = configs_dir / cfg.name
                shutil.copy2(str(cfg), str(dest))
            except Exception:
                pass

    # Copy all files under .opencode/
    opencode_dir = project / ".opencode"
    if opencode_dir.exists():
        try:
            shutil.copytree(str(opencode_dir), str(configs_dir / ".opencode"))
        except Exception:
            pass

    # ── Diagnostics ───────────────────────────────────────────────────────────
    diag_lines: List[str] = []
    for diag_name, diag_cmd in [
        ("rulez validate", ["rulez", "validate"]),
        ("rulez opencode doctor", ["rulez", "opencode", "doctor"]),
    ]:
        try:
            r = subprocess.run(
                diag_cmd, capture_output=True, text=True, timeout=15, cwd=str(project)
            )
            diag_lines.append(f"## {diag_name} (rc={r.returncode})")
            diag_lines.append(r.stdout + r.stderr)
        except Exception as e:
            diag_lines.append(f"## {diag_name}: error: {e}")
    (artifact_dir / "diagnostics.txt").write_text("\n".join(diag_lines))

    # ── Directory tree ────────────────────────────────────────────────────────
    tree_lines: List[str] = []
    for root, dirs, files in os.walk(project):
        depth = len(Path(root).relative_to(project).parts)
        indent = "  " * depth
        tree_lines.append(f"{indent}{Path(root).name}/")
        for f in sorted(files):
            tree_lines.append(f"{indent}  {f}")
    (artifact_dir / "dir-tree.txt").write_text("\n".join(tree_lines))

    # ── Session files ─────────────────────────────────────────────────────────
    sessions_src = project / ".code-wizard" / "sessions"
    if sessions_src.exists():
        try:
            shutil.copytree(str(sessions_src), str(artifact_dir / "sessions"))
        except Exception:
            pass

    docs_src = project / ".code-wizard" / "docs"
    if docs_src.exists():
        try:
            shutil.copytree(str(docs_src), str(artifact_dir / "docs"))
        except Exception:
            pass

    # ── Artifact file index ───────────────────────────────────────────────────
    artifact_files = sorted(
        str(p.relative_to(artifact_dir))
        for p in artifact_dir.rglob("*")
        if p.is_file()
    )

    # ── FAILURE_REPORT.md ─────────────────────────────────────────────────────
    tb_str = "".join(traceback.format_exception(type(assertion_error), assertion_error, assertion_error.__traceback__))
    failure_report = f"""# FAILURE REPORT: {label}-rulez e2e

## Test Name

`test_agent_rulez_{label}_capture_to_export`

## Purpose

Full capture-to-export pipeline e2e: setup → wizard session → session captured → export → docs generated.
On failure, this artifact bundle is written for handoff-quality diagnostics.

## Setup Steps Taken

{chr(10).join(f"- {k}: rc={v.returncode if v is not None else 'N/A'}" for k, v in subprocess_results.items())}

## Observed Failure

```
{str(assertion_error)}
```

### Traceback

```
{tb_str}
```

## Likely Failure Layer

Based on which subprocess results are present:
- setup missing → failure in Phase 1 (setup.sh)
- wizard missing → failure in Phase 2 (wizard session)
- export missing → failure in Phase 4 (export session)
- all present → failure in Phase 3 or Phase 5 (assertion layer)

## Reproduction Recipe

```bash
# Ensure rulez + {label} are installed and authenticated
cd /path/to/codebase-mentor
pytest -m slow tests/integration/test_agent_rulez_e2e.py::test_agent_rulez_{label}_capture_to_export -v -s
```

## Version Info

{chr(10).join(f"- {k}: {v}" for k, v in version_info.items())}

## Artifact File Index

{chr(10).join(f"- {f}" for f in artifact_files)}
"""
    (artifact_dir / "FAILURE_REPORT.md").write_text(failure_report)

    # ── Tarball ───────────────────────────────────────────────────────────────
    tarball_path = artifact_dir.with_suffix(".tar.gz")
    try:
        with tarfile.open(str(tarball_path), "w:gz") as tar:
            tar.add(str(artifact_dir), arcname=artifact_dir.name)
    except Exception:
        pass

    print(f"\n[FAILURE ARTIFACT] {tarball_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main integration test — Claude Code + Agent Rulez
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_agent_rulez_claude_capture_to_export(
    integration_env, rulez_available, claude_available
):
    """Full Agent Rulez pipeline: setup → wizard capture → export → docs.

    Phase 1 — Setup (rulez):
      setup.sh deploys .claude/hooks.yaml (Agent Rulez rules), registers rulez
      PostToolUse hook in .claude/settings.json. Security rules active.

    Phase 2 — Wizard session (claude -p):
      Wizard runs in describe mode. Step 6 of the Answer Loop writes structured
      turns to .code-wizard/sessions/{session_id}.json via the Write tool.
      Agent Rulez PostToolUse hook also fires but writes raw tool events (separate).

    Phase 3 — Assert session captured:
      .code-wizard/sessions/*.json must have wizard turns with 'question' field.
      SESSION-TRANSCRIPT.md must NOT exist yet — proves export generates it, not
      the wizard session itself.

    Phase 4 — Export (claude -p):
      Export skill reads session JSON and writes SESSION-TRANSCRIPT.md + CODEBASE.md
      to .code-wizard/docs/{session_id}/.

    Phase 5 — Assert docs:
      Both files exist, have expected headings, contain fixture-specific content
      (calculate, src/main.py), and docs session_id matches the session JSON.
    """
    if not rulez_available:
        pytest.skip("rulez not installed — cannot test Agent Rulez pipeline")
    if not claude_available:
        pytest.skip("claude not available or not authenticated")

    project = integration_env["project"]

    # ── Phase 1: Setup ────────────────────────────────────────────────────────
    setup_result = run_setup(integration_env, runtime="claude")
    assert setup_result.returncode == 0, (
        f"setup.sh failed (rc={setup_result.returncode}).\n"
        f"stdout: {setup_result.stdout}\nstderr: {setup_result.stderr}"
    )
    assert_phase1_setup(project)

    # ── Phase 2: Wizard session ───────────────────────────────────────────────
    # Use natural language trigger phrases rather than slash command syntax.
    # claude -p does not support context:fork commands (the /codebase-wizard command
    # uses context:fork to spawn codebase-wizard-agent). The explaining-codebase
    # SKILL.md is triggered by the same natural language phrases — the command is a
    # thin entry point only. Command file structure (frontmatter, registration) is
    # verified by test_command_files_have_correct_structure() in tests/test_plugin_structure.py.
    session_result = run_claude(
        "describe this codebase. Use describe mode. "
        "Save each answer turn to the session log as you go. "
        "Proceed without asking questions.",
        integration_env,
    )
    assert session_result.returncode == 0, (
        f"claude -p wizard session failed (rc={session_result.returncode}).\n"
        f"stdout: {session_result.stdout}\nstderr: {session_result.stderr}"
    )

    # ── Phase 3: Assert session captured ──────────────────────────────────────
    sessions = assert_phase3_session_captured(project)
    assert_phase3_rulez_fired(project)  # NEW: verify rulez hook events, not just wizard turns

    # SESSION-TRANSCRIPT.md must NOT exist yet — export generates it
    assert find_output(project, "SESSION-TRANSCRIPT.md") is None, (
        "SESSION-TRANSCRIPT.md already exists before export was run.\n"
        "The wizard session should only write .code-wizard/sessions/*.json.\n"
        "SESSION-TRANSCRIPT.md must be generated by the export step, not inline."
    )

    # ── Phase 4: Export ───────────────────────────────────────────────────────
    # Same rationale: /codebase-wizard-export uses context:fork, not supported in -p mode.
    # The exporting-conversation SKILL.md handles the export logic directly.
    export_result = run_claude(
        "export the wizard session. Read the latest session JSON from "
        ".code-wizard/sessions/ and generate SESSION-TRANSCRIPT.md and CODEBASE.md.",
        integration_env,
    )
    assert export_result.returncode == 0, (
        f"claude -p export failed (rc={export_result.returncode}).\n"
        f"stdout: {export_result.stdout}\nstderr: {export_result.stderr}"
    )

    # ── Phase 5: Assert docs generated from session JSON ─────────────────────
    assert_phase5_docs(project, sessions)


@pytest.mark.slow
def test_opencode_setup_deploys_hooks_yaml(integration_env, rulez_available):
    """Verify setup.sh opencode path writes .claude/hooks.yaml and deploys capture-session.sh.

    This test verifies the OpenCode hook installation path of setup.sh:
      - deploy_hooks() is called with runtime="opencode"
      - .claude/hooks.yaml is written (rules file rulez reads at hook-fire time)
      - capture-session.sh is deployed
      - config.json is created

    The `rulez opencode install` step may fail if opencode is not installed — that
    is acceptable. We assert the artifacts created BEFORE the rulez call, not the
    rulez registration itself (which is tested indirectly by the Claude-side test).

    If setup.sh fails AND .claude/hooks.yaml was not created, the test fails —
    indicating a regression in the opencode deploy_hooks() path.
    """
    if not rulez_available:
        pytest.skip("rulez not installed — cannot test OpenCode setup path")

    project = integration_env["project"]

    # Run setup.sh with opencode runtime
    setup_result = run_setup(integration_env, runtime="opencode")

    # setup.sh may fail on `rulez opencode install` if opencode is not installed.
    # Check if the pre-rulez artifacts were created regardless of exit code.
    hooks_yaml = project / ".claude" / "hooks.yaml"
    capture_sh = project / ".code-wizard" / "scripts" / "capture-session.sh"
    config_json = project / ".code-wizard" / "config.json"

    # If setup.sh failed AND none of the artifacts exist, it's a real regression.
    artifacts_created = hooks_yaml.exists() or capture_sh.exists() or config_json.exists()
    if setup_result.returncode != 0 and not artifacts_created:
        pytest.fail(
            f"setup.sh opencode path failed before creating any artifacts.\n"
            f"Exit code: {setup_result.returncode}\n"
            f"stdout: {setup_result.stdout}\nstderr: {setup_result.stderr}"
        )

    # If artifacts were created, verify them regardless of whether rulez step succeeded.
    assert config_json.exists(), (
        f"setup.sh did not create .code-wizard/config.json for opencode runtime.\n"
        f"stdout: {setup_result.stdout}\nstderr: {setup_result.stderr}"
    )
    assert hooks_yaml.exists(), (
        ".claude/hooks.yaml not created for opencode runtime.\n"
        "deploy_hooks() must copy agent-rulez.yaml → .claude/hooks.yaml.\n"
        f"stdout: {setup_result.stdout}\nstderr: {setup_result.stderr}"
    )
    assert capture_sh.exists(), (
        ".code-wizard/scripts/capture-session.sh not deployed for opencode runtime.\n"
        f"stdout: {setup_result.stdout}\nstderr: {setup_result.stderr}"
    )

    # Check .claude/hooks.yaml content
    hooks_text = hooks_yaml.read_text()
    assert "rules:" in hooks_text, (
        ".claude/hooks.yaml missing 'rules:' top-level key — wrong schema deployed"
    )

    # If setup completed fully (rulez opencode install worked), verify output message
    if setup_result.returncode == 0:
        assert "OpenCode" in setup_result.stdout or "opencode" in setup_result.stdout.lower(), (
            "setup.sh opencode output does not mention OpenCode"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main integration test — OpenCode + Agent Rulez
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.slow
def test_agent_rulez_opencode_capture_to_export(
    opencode_integration_env, rulez_available, opencode_available
):
    """Full Agent Rulez pipeline with OpenCode: setup → wizard capture → export → docs.

    On failure, a handoff-quality artifact bundle is written to artifacts/ for the
    Agent Rulez project team.

    Phase 1 — Setup (rulez + opencode):
      setup.sh deploys .claude/hooks.yaml, registers rulez PostToolUse hook,
      and configures .opencode/ directory for OpenCode runtime.

    Phase 2 — Wizard session (opencode run):
      Wizard runs in describe mode via opencode. Step 6 of the Answer Loop writes
      structured turns to .code-wizard/sessions/{session_id}.json via the Write tool.

    Phase 3 — Assert session captured:
      .code-wizard/sessions/*.json must have wizard turns with 'question' field.
      Agent Rulez hook events (tool_name, hook_event_name) must also be present.

    Phase 4 — Export (opencode run):
      Export skill reads session JSON and writes SESSION-TRANSCRIPT.md + CODEBASE.md.

    Phase 5 — Assert docs:
      Both files exist, have expected headings, contain fixture-specific content,
      and docs session_id matches the session JSON.
    """
    if not rulez_available:
        pytest.skip("rulez not installed")
    if not opencode_available:
        pytest.skip("opencode not available or cannot run headlessly")

    project = opencode_integration_env["project"]
    subprocess_results: Dict[str, Any] = {}
    assertion_error: Optional[BaseException] = None

    try:
        # ── Phase 1: Setup ────────────────────────────────────────────────────
        setup_result = run_setup(opencode_integration_env, runtime="opencode")
        subprocess_results["setup"] = setup_result
        assert setup_result.returncode == 0, (
            f"setup.sh failed (rc={setup_result.returncode}).\n"
            f"stdout: {setup_result.stdout}\nstderr: {setup_result.stderr}"
        )
        assert_phase1_setup(project)

        # Also verify opencode-specific artifacts
        opencode_dir = project / ".opencode"
        assert opencode_dir.exists() or (project / ".claude" / "hooks.yaml").exists(), (
            "Neither .opencode/ nor .claude/hooks.yaml found after opencode setup.\n"
            "setup.sh opencode path must create at least one of these."
        )

        # ── Phase 2: Wizard session via opencode run ──────────────────────────
        wizard_result = run_opencode(
            "describe this codebase. Use describe mode. "
            "Save each answer turn to the session log as you go. "
            "Proceed without asking questions.",
            opencode_integration_env,
        )
        subprocess_results["wizard"] = wizard_result
        assert wizard_result.returncode == 0, (
            f"opencode run wizard failed (rc={wizard_result.returncode}).\n"
            f"stdout: {wizard_result.stdout}\nstderr: {wizard_result.stderr}"
        )

        # ── Phase 3: Assert session captured ──────────────────────────────────
        sessions = assert_phase3_session_captured(project)
        assert_phase3_rulez_fired(project)

        # ── Phase 4: Export via opencode run ──────────────────────────────────
        export_result = run_opencode(
            "export the wizard session. Read the latest session JSON from "
            ".code-wizard/sessions/ and generate SESSION-TRANSCRIPT.md and CODEBASE.md.",
            opencode_integration_env,
        )
        subprocess_results["export"] = export_result
        assert export_result.returncode == 0, (
            f"opencode run export failed (rc={export_result.returncode}).\n"
            f"stdout: {export_result.stdout}\nstderr: {export_result.stderr}"
        )

        # ── Phase 5: Assert docs generated from session JSON ──────────────────
        assert_phase5_docs(project, sessions)

    except (AssertionError, Exception) as exc:
        assertion_error = exc
        raise
    finally:
        if assertion_error is not None:
            try:
                _collect_failure_artifacts(
                    project,
                    opencode_integration_env,
                    "opencode",
                    subprocess_results,
                    assertion_error,
                )
            except Exception:
                pass  # never mask the real failure
