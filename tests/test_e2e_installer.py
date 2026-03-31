"""E2E integration tests — exercise full CLI install/uninstall/status via CliRunner."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ai_codebase_mentor.cli import main


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    """Redirect home() and cwd() to temp dirs for full CLI isolation."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    return tmp_path


def test_cli_install_opencode_project(cli_env):
    """E2E-01: CLI install --for opencode --project writes correct files to .opencode/."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "opencode", "--project"])
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    assert (
        cli_env / "cwd" / ".opencode" / "codebase-wizard" / "command" / "codebase-wizard.md"
    ).exists(), "codebase-wizard.md not found in command/ dir"
    assert (
        cli_env / "cwd" / ".opencode" / "codebase-wizard" / "agent" / "codebase-wizard-agent.md"
    ).exists(), "codebase-wizard-agent.md not found in agent/ dir"
    assert (
        cli_env / "cwd" / ".opencode" / "codebase-wizard" / "skill"
    ).is_dir(), "skill/ directory not found"


def test_cli_install_claude_project(cli_env):
    """E2E-02: CLI install --for claude --project writes correct files to plugins/."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "claude", "--project"])
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    assert (
        cli_env / "cwd" / "plugins" / "codebase-wizard" / ".claude-plugin" / "plugin.json"
    ).exists(), "plugin.json not found in plugins/codebase-wizard/.claude-plugin/"
    assert (
        cli_env / "cwd" / "plugins" / "codebase-wizard" / "commands" / "codebase-wizard.md"
    ).exists(), "codebase-wizard.md not found in plugins/codebase-wizard/commands/"


def test_cli_install_all(cli_env):
    """E2E-03: CLI install --for all --project creates both .opencode/ and plugins/ dirs."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "all", "--project"])
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    assert (
        cli_env / "cwd" / ".opencode" / "codebase-wizard"
    ).exists(), ".opencode/codebase-wizard/ not found after install --for all"
    assert (
        cli_env / "cwd" / "plugins" / "codebase-wizard"
    ).exists(), "plugins/codebase-wizard/ not found after install --for all"
    assert (
        cli_env / "cwd" / ".gemini" / "codebase-wizard"
    ).exists(), ".gemini/codebase-wizard/ not found after install --for all"


def test_cli_uninstall_opencode_project(cli_env):
    """E2E-04: CLI uninstall --for opencode --project removes installed files."""
    runner = CliRunner()
    install_result = runner.invoke(main, ["install", "--for", "opencode", "--project"])
    assert install_result.exit_code == 0, f"Install failed.\nOutput:\n{install_result.output}"
    uninstall_result = runner.invoke(main, ["uninstall", "--for", "opencode", "--project"])
    assert uninstall_result.exit_code == 0, f"Uninstall failed.\nOutput:\n{uninstall_result.output}"
    assert not (
        cli_env / "cwd" / ".opencode" / "codebase-wizard"
    ).exists(), ".opencode/codebase-wizard/ should not exist after uninstall"


def test_cli_status_after_install_all(cli_env):
    """E2E-05: CLI status reports both runtimes installed after install --for all."""
    runner = CliRunner()
    runner.invoke(main, ["install", "--for", "all", "--project"])
    result = runner.invoke(main, ["status"])
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    assert "claude: installed" in result.output, (
        f"Expected 'claude: installed' in status output.\nOutput:\n{result.output}"
    )
    assert "opencode: installed" in result.output, (
        f"Expected 'opencode: installed' in status output.\nOutput:\n{result.output}"
    )
    assert "gemini: installed" in result.output, (
        f"Expected 'gemini: installed' in status output.\nOutput:\n{result.output}"
    )


def test_cli_target_flag_invalid(cli_env):
    """E2E-10: --target flag is rejected (only --project is valid); Click returns exit_code 2."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "opencode", "--target", "project"])
    assert result.exit_code != 0, (
        f"Expected non-zero exit_code for invalid --target flag, got {result.exit_code}."
    )


def test_cli_install_opencode_writes_subtask_entries(cli_env):
    """E2E-07: After CLI install for opencode, opencode.json contains subtask:true entries."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "opencode", "--project"])
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    json_path = cli_env / "cwd" / ".opencode" / "opencode.json"
    assert json_path.exists(), f"opencode.json not found at {json_path}"
    data = json.loads(json_path.read_text())
    assert "command" in data, f"opencode.json missing 'command' key. Keys: {list(data.keys())}"
    for cmd_name, cmd_cfg in data["command"].items():
        assert cmd_cfg.get("subtask") is True, (
            f"Expected subtask:true for command '{cmd_name}', got: {cmd_cfg}"
        )


def test_cli_install_opencode_global(cli_env):
    """E2E-01 global variant: CLI install --for opencode (no --project) installs to ~/.config/opencode/."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "opencode"])
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    assert (
        cli_env / "home" / ".config" / "opencode" / "codebase-wizard" / "agent"
    ).exists(), "agent/ dir not found at ~/.config/opencode/codebase-wizard/agent/"


def test_cli_status_before_install(cli_env):
    """Baseline: CLI status before any install reports not installed for all runtimes."""
    runner = CliRunner()
    result = runner.invoke(main, ["status"])
    assert result.exit_code == 0, f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    assert "not installed" in result.output, (
        f"Expected 'not installed' in status output before any install.\nOutput:\n{result.output}"
    )
