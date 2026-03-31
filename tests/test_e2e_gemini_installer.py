"""E2E integration tests — Gemini CLI install/uninstall/status via CliRunner."""

import re
import tomllib
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


VALID_GEMINI_TOOLS = {
    "read_file", "write_file", "replace", "run_shell_command",
    "glob", "search_file_content", "google_web_search", "web_fetch",
    "write_todos", "ask_user",
}


def test_cli_install_gemini_project(cli_env):
    """E2E-01 project: CLI install --for gemini --project writes correct files to .gemini/."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "gemini", "--project"])
    assert result.exit_code == 0, (
        f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    )
    gemini_root = cli_env / "cwd" / ".gemini" / "codebase-wizard"
    cmd_dir = gemini_root / "command"
    assert cmd_dir.is_dir(), "command/ directory not found"
    toml_files = list(cmd_dir.glob("*.toml"))
    assert len(toml_files) > 0, "No .toml files found in command/ dir"
    agent_dir = gemini_root / "agent"
    assert agent_dir.is_dir(), "agent/ directory not found"
    agent_files = list(agent_dir.glob("*.md"))
    assert len(agent_files) > 0, "No .md files found in agent/ dir"
    assert (gemini_root / "skill").is_dir(), "skill/ directory not found"


def test_cli_install_gemini_global(cli_env):
    """E2E-01 global: CLI install --for gemini (no --project) installs to ~/.gemini/."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "gemini"])
    assert result.exit_code == 0, (
        f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    )
    gemini_root = cli_env / "home" / ".gemini" / "codebase-wizard"
    assert (gemini_root / "agent").is_dir(), "agent/ dir not found at ~/.gemini/codebase-wizard/"
    assert (gemini_root / "command").is_dir(), "command/ dir not found at ~/.gemini/codebase-wizard/"


def test_cli_uninstall_gemini_project(cli_env):
    """E2E-02: CLI uninstall --for gemini --project removes .gemini/codebase-wizard/ cleanly."""
    runner = CliRunner()
    install_result = runner.invoke(main, ["install", "--for", "gemini", "--project"])
    assert install_result.exit_code == 0, f"Install failed.\nOutput:\n{install_result.output}"
    gemini_root = cli_env / "cwd" / ".gemini" / "codebase-wizard"
    assert gemini_root.exists(), "Install did not create .gemini/codebase-wizard/"
    uninstall_result = runner.invoke(main, ["uninstall", "--for", "gemini", "--project"])
    assert uninstall_result.exit_code == 0, (
        f"Uninstall failed.\nOutput:\n{uninstall_result.output}"
    )
    assert not gemini_root.exists(), ".gemini/codebase-wizard/ should not exist after uninstall"


def test_cli_status_gemini(cli_env):
    """E2E-03: CLI status reports 'gemini: installed' after install."""
    runner = CliRunner()
    runner.invoke(main, ["install", "--for", "gemini", "--project"])
    result = runner.invoke(main, ["status"])
    assert result.exit_code == 0, (
        f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    )
    assert "gemini: installed" in result.output, (
        f"Expected 'gemini: installed' in status output.\nOutput:\n{result.output}"
    )


def test_gemini_toml_valid(cli_env):
    """E2E-04: Generated TOML command files parse as valid TOML with prompt + description."""
    runner = CliRunner()
    runner.invoke(main, ["install", "--for", "gemini", "--project"])
    cmd_dir = cli_env / "cwd" / ".gemini" / "codebase-wizard" / "command"
    toml_files = list(cmd_dir.glob("*.toml"))
    assert len(toml_files) > 0, "No TOML files found after install"
    for toml_file in toml_files:
        content = toml_file.read_text()
        parsed = tomllib.loads(content)
        assert "prompt" in parsed, f"{toml_file.name} missing 'prompt' key"
        assert "description" in parsed, f"{toml_file.name} missing 'description' key"


def test_gemini_agent_snake_case_tools(cli_env):
    """E2E-05: Agent files contain only valid Gemini snake_case tool names."""
    runner = CliRunner()
    runner.invoke(main, ["install", "--for", "gemini", "--project"])
    agent_dir = cli_env / "cwd" / ".gemini" / "codebase-wizard" / "agent"
    agent_files = list(agent_dir.glob("*.md"))
    assert len(agent_files) > 0, "No agent files found after install"
    for agent_file in agent_files:
        content = agent_file.read_text()
        tools = re.findall(r"^\s+-\s+(\S+)", content, re.MULTILINE)
        for tool in tools:
            assert tool in VALID_GEMINI_TOOLS, (
                f"Agent {agent_file.name} has invalid tool: {tool}"
            )
            assert not re.match(r"^[A-Z]", tool), (
                f"Agent {agent_file.name} has PascalCase tool leaked through: {tool}"
            )


def test_cli_install_all_includes_gemini(cli_env):
    """E2E-06: --for all installs Gemini alongside Claude and OpenCode."""
    runner = CliRunner()
    result = runner.invoke(main, ["install", "--for", "all", "--project"])
    assert result.exit_code == 0, (
        f"Expected exit_code 0, got {result.exit_code}.\nOutput:\n{result.output}"
    )
    assert (
        cli_env / "cwd" / ".gemini" / "codebase-wizard"
    ).exists(), ".gemini/codebase-wizard/ not found after install --for all"
    assert (
        cli_env / "cwd" / ".opencode" / "codebase-wizard"
    ).exists(), ".opencode/codebase-wizard/ not found after install --for all"
    assert (
        cli_env / "cwd" / "plugins" / "codebase-wizard"
    ).exists(), "plugins/codebase-wizard/ not found after install --for all"
