"""E2E tests for codebase-wizard setup.sh and Agent Rulez hooks installation.

These tests verify:
- setup.sh deploys agent-rulez.yaml with the correct 'rules:' schema (not 'hooks:')
- setup.sh calls 'rulez install' (not the old broken 'rulez hook add --config')
- setup.sh deploys capture-session.sh to .code-wizard/scripts/ and makes it executable
- setup.sh creates .code-wizard/config.json
- capture-session.sh writes tool events to .code-wizard/sessions/{session_id}.json

The fake rulez fixture injects a mock 'rulez' binary via PATH prepending so these
tests run without requiring Agent Rulez to be installed on the host system.
"""

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

SETUP_SH = (
    Path(__file__).parent.parent
    / "plugins"
    / "codebase-wizard"
    / "skills"
    / "configuring-codebase-wizard"
    / "scripts"
    / "setup.sh"
)

CAPTURE_SH = (
    Path(__file__).parent.parent
    / "plugins"
    / "codebase-wizard"
    / "skills"
    / "configuring-codebase-wizard"
    / "scripts"
    / "capture-session.sh"
)


@pytest.fixture
def wizard_project(tmp_path):
    """Project dir with .code-wizard/ pre-created and a mock rulez binary in PATH.

    Pre-creating .code-wizard/sessions and .code-wizard/docs prevents setup.sh
    from prompting interactively for a storage location (resolve_storage() picks
    up the existing directory automatically).
    """
    project = tmp_path / "project"
    project.mkdir()

    # Pre-create wizard storage so resolve_storage() skips the interactive prompt
    (project / ".code-wizard" / "sessions").mkdir(parents=True)
    (project / ".code-wizard" / "docs").mkdir(parents=True)

    # Fake rulez binary: records each invocation's args to a log file, exits 0
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    rulez_log = tmp_path / "rulez-calls.log"
    fake_rulez = fake_bin / "rulez"
    fake_rulez.write_text(
        f'#!/usr/bin/env bash\necho "$@" >> {rulez_log}\nexit 0\n'
    )
    fake_rulez.chmod(fake_rulez.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    return {
        "project": project,
        "fake_bin": fake_bin,
        "rulez_log": rulez_log,
    }


def _run_setup(wizard_project, runtime="claude"):
    """Run setup.sh in the project dir with the mock rulez prepended to PATH."""
    env = os.environ.copy()
    env["PATH"] = str(wizard_project["fake_bin"]) + ":" + env.get("PATH", "")
    return subprocess.run(
        ["bash", str(SETUP_SH), runtime],
        cwd=str(wizard_project["project"]),
        capture_output=True,
        text=True,
        env=env,
    )


# ─────────────────────────────────────────────────────────────────────────────
# setup.sh: file deployment tests
# ─────────────────────────────────────────────────────────────────────────────


def test_setup_deploys_agent_rulez_yaml(wizard_project):
    """SETUP-01: setup.sh copies agent-rulez-sample.yaml to .code-wizard/agent-rulez.yaml."""
    result = _run_setup(wizard_project)
    assert result.returncode == 0, (
        f"setup.sh exited {result.returncode}:\n{result.stdout}\n{result.stderr}"
    )
    deployed = wizard_project["project"] / ".code-wizard" / "agent-rulez.yaml"
    assert deployed.exists(), (
        f"agent-rulez.yaml not found at {deployed} after setup.\n"
        f"stdout: {result.stdout}"
    )


def test_setup_agent_rulez_yaml_uses_rules_schema(wizard_project):
    """SETUP-02: Deployed agent-rulez.yaml uses 'rules:' top-level key (not 'hooks:').

    Phase 10 rewrote the sample to fix this schema — this test locks in the fix.
    If 'hooks:' ever reappears at the top level, capture will silently fail.
    """
    _run_setup(wizard_project)
    deployed = wizard_project["project"] / ".code-wizard" / "agent-rulez.yaml"
    content = deployed.read_text()
    assert "rules:" in content, (
        f"'rules:' not found in deployed agent-rulez.yaml. Content:\n{content}"
    )
    # 'hooks:' as a top-level key is the old broken schema
    top_level_keys = [
        line.split(":")[0].strip()
        for line in content.splitlines()
        if line and not line.startswith(" ") and not line.startswith("#") and ":" in line
    ]
    assert "hooks" not in top_level_keys, (
        f"agent-rulez.yaml uses 'hooks:' at top level (wrong schema). "
        f"Top-level keys found: {top_level_keys}"
    )


def test_setup_deploys_capture_session_script(wizard_project):
    """SETUP-03: setup.sh copies capture-session.sh to .code-wizard/scripts/ as executable."""
    result = _run_setup(wizard_project)
    assert result.returncode == 0, (
        f"setup.sh exited {result.returncode}:\n{result.stdout}\n{result.stderr}"
    )
    script = wizard_project["project"] / ".code-wizard" / "scripts" / "capture-session.sh"
    assert script.exists(), (
        f"capture-session.sh not deployed to .code-wizard/scripts/\nstdout: {result.stdout}"
    )
    assert os.access(str(script), os.X_OK), (
        "capture-session.sh exists but is not executable (chmod +x was not applied)"
    )


def test_setup_creates_config_json(wizard_project):
    """SETUP-04: setup.sh creates .code-wizard/config.json with version and resolved_storage."""
    result = _run_setup(wizard_project)
    assert result.returncode == 0, (
        f"setup.sh exited {result.returncode}:\n{result.stdout}\n{result.stderr}"
    )
    config = wizard_project["project"] / ".code-wizard" / "config.json"
    assert config.exists(), ".code-wizard/config.json not created by setup.sh"
    data = json.loads(config.read_text())
    assert "version" in data, f"config.json missing 'version' key. Keys: {list(data.keys())}"
    assert data["version"] == 1, f"Expected version=1, got {data['version']}"
    assert "resolved_storage" in data, (
        f"config.json missing 'resolved_storage' key. Keys: {list(data.keys())}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# setup.sh: rulez command verification
# ─────────────────────────────────────────────────────────────────────────────


def test_setup_calls_rulez_install(wizard_project):
    """SETUP-05: setup.sh calls 'rulez install', not 'rulez hook add --config'.

    This is the Phase 10 fix. The old command ('rulez hook add --config') exited
    with code 2 (unrecognized subcommand). 'rulez install' is the correct command.
    """
    _run_setup(wizard_project)
    rulez_log = wizard_project["rulez_log"]
    assert rulez_log.exists(), (
        "rulez was never invoked — fake rulez log not created. "
        "setup.sh may have skipped deploy_hooks()."
    )
    calls = [line.strip() for line in rulez_log.read_text().splitlines() if line.strip()]
    assert any(call == "install" for call in calls), (
        f"Expected 'rulez install' call but got: {calls}"
    )


def test_setup_does_not_call_rulez_hook_add(wizard_project):
    """SETUP-06: setup.sh does NOT call 'rulez hook add --config' (the old broken command)."""
    _run_setup(wizard_project)
    rulez_log = wizard_project["rulez_log"]
    if not rulez_log.exists():
        return  # rulez never called — SETUP-05 will catch the missing call
    calls = [line.strip() for line in rulez_log.read_text().splitlines() if line.strip()]
    broken_calls = [c for c in calls if c.startswith("hook")]
    assert not broken_calls, (
        f"setup.sh called 'rulez hook ...' (old broken subcommand): {broken_calls}. "
        "The correct command is 'rulez install'."
    )


# ─────────────────────────────────────────────────────────────────────────────
# capture-session.sh: session capture tests
# ─────────────────────────────────────────────────────────────────────────────


def test_capture_session_writes_session_file(tmp_path):
    """SETUP-07: capture-session.sh creates .code-wizard/sessions/{session_id}.json."""
    project = tmp_path / "project"
    (project / ".code-wizard" / "sessions").mkdir(parents=True)

    event = json.dumps({
        "hook_event_name": "PostToolUse",
        "tool_name": "Read",
        "tool_input": {"file_path": "/src/main.py"},
        "session_id": "test-session-abc",
        "timestamp": "2026-03-25T12:00:00Z",
    })
    result = subprocess.run(
        ["bash", str(CAPTURE_SH)],
        input=event,
        capture_output=True,
        text=True,
        cwd=str(project),
    )
    session_file = project / ".code-wizard" / "sessions" / "test-session-abc.json"
    assert session_file.exists(), (
        f"Session file not created at {session_file}.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    data = json.loads(session_file.read_text())
    assert data.get("session_id") == "test-session-abc", (
        f"Wrong session_id. Got: {data.get('session_id')}"
    )


def test_capture_session_appends_turn(tmp_path):
    """SETUP-08: capture-session.sh appends each event as a turn in the session JSON."""
    project = tmp_path / "project"
    (project / ".code-wizard" / "sessions").mkdir(parents=True)

    def send_event(tool_name):
        event = json.dumps({
            "hook_event_name": "PostToolUse",
            "tool_name": tool_name,
            "tool_input": {},
            "session_id": "test-session-xyz",
            "timestamp": "2026-03-25T12:00:00Z",
        })
        subprocess.run(
            ["bash", str(CAPTURE_SH)],
            input=event,
            capture_output=True,
            text=True,
            cwd=str(project),
        )

    send_event("Read")
    send_event("Grep")
    send_event("Write")

    session_file = project / ".code-wizard" / "sessions" / "test-session-xyz.json"
    assert session_file.exists(), "Session file not created after 3 events"
    data = json.loads(session_file.read_text())
    turns = data.get("turns", [])
    assert len(turns) == 3, f"Expected 3 turns (one per event), got {len(turns)}"
    tool_names = [t.get("tool_name") for t in turns]
    assert tool_names == ["Read", "Grep", "Write"], (
        f"Turns not appended in order. Got: {tool_names}"
    )
