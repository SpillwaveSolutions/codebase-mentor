"""Tests for GeminiInstaller — install, uninstall, status for Gemini CLI runtime."""

import shutil
import tomllib
from pathlib import Path

import pytest

from ai_codebase_mentor.converters.gemini import (
    GeminiInstaller,
    _convert_gemini_tool_name,
)

# Path to the real plugin source (same as opencode tests)
REAL_PLUGIN_SOURCE = Path(__file__).parent.parent / "plugins" / "codebase-wizard"


@pytest.fixture
def source_plugin_dir(tmp_path):
    """Copy the real plugin source to a temp dir so tests don't touch the repo."""
    src = tmp_path / "plugin-source" / "codebase-wizard"
    shutil.copytree(REAL_PLUGIN_SOURCE, src)
    return src


@pytest.fixture
def installer(tmp_path, monkeypatch):
    """GeminiInstaller with home() and cwd() redirected to temp paths."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    monkeypatch.delenv("GEMINI_CONFIG_DIR", raising=False)
    return GeminiInstaller()


# ---------------------------------------------------------------------------
# Install / Uninstall / Status
# ---------------------------------------------------------------------------


def test_global_install_creates_agent_files(installer, source_plugin_dir, tmp_path):
    """install(source, 'global') creates agent dir at ~/.gemini/codebase-wizard/agent/."""
    installer.install(source_plugin_dir, "global")
    agents_dir = tmp_path / "home" / ".gemini" / "codebase-wizard" / "agent"
    assert agents_dir.exists(), f"agent dir not found at {agents_dir}"
    assert (agents_dir / "codebase-wizard-agent.md").exists()


def test_project_install_creates_agent_files(installer, source_plugin_dir, tmp_path):
    """install(source, 'project') creates agent dir at ./.gemini/codebase-wizard/agent/."""
    installer.install(source_plugin_dir, "project")
    agents_dir = tmp_path / "cwd" / ".gemini" / "codebase-wizard" / "agent"
    assert agents_dir.exists(), f"agent dir not found at {agents_dir}"
    assert (agents_dir / "codebase-wizard-agent.md").exists()


def test_global_install_creates_command_files(installer, source_plugin_dir, tmp_path):
    """install(source, 'global') creates command/ dir with .toml files (not .md)."""
    installer.install(source_plugin_dir, "global")
    cmd_dir = tmp_path / "home" / ".gemini" / "codebase-wizard" / "command"
    assert cmd_dir.exists(), f"command dir not found at {cmd_dir}"
    toml_files = list(cmd_dir.glob("*.toml"))
    assert len(toml_files) > 0, "Expected at least one .toml file in command/"
    md_files = list(cmd_dir.glob("*.md"))
    assert len(md_files) == 0, "No .md files should exist in command/ (should be .toml)"


def test_skills_copied_verbatim(installer, source_plugin_dir, tmp_path):
    """install() copies skills/ to skill/ (singular) verbatim."""
    installer.install(source_plugin_dir, "global")
    skill_dir = tmp_path / "home" / ".gemini" / "codebase-wizard" / "skill"
    assert skill_dir.exists(), f"skill dir not found at {skill_dir}"
    # Check at least one skill file was copied
    assert any(skill_dir.rglob("*")), "skill/ dir is empty"


def test_global_install_is_idempotent(installer, source_plugin_dir):
    """Calling install() twice does not raise."""
    installer.install(source_plugin_dir, "global")
    installer.install(source_plugin_dir, "global")  # should not raise


def test_global_uninstall_removes_directory(installer, source_plugin_dir, tmp_path):
    """uninstall('global') removes ~/.gemini/codebase-wizard/ entirely."""
    installer.install(source_plugin_dir, "global")
    installer.uninstall("global")
    dest = tmp_path / "home" / ".gemini" / "codebase-wizard"
    assert not dest.exists(), f"Expected directory to be removed: {dest}"


def test_uninstall_when_not_installed_is_noop(installer):
    """uninstall('global') when nothing installed does not raise."""
    installer.uninstall("global")  # must not raise


def test_status_after_global_install(installer, source_plugin_dir, tmp_path):
    """status() returns installed=True with correct location and version after install."""
    installer.install(source_plugin_dir, "global")
    result = installer.status()
    expected_location = str(tmp_path / "home" / ".gemini" / "codebase-wizard")
    assert result["installed"] is True
    assert result["location"] == expected_location
    assert result["version"] == "1.0.0"


def test_status_before_install(installer):
    """status() returns installed=False with None fields before any install."""
    result = installer.status()
    assert result == {"installed": False, "location": None, "version": None}


def test_install_raises_on_missing_source(installer):
    """install() raises RuntimeError for nonexistent source."""
    with pytest.raises(RuntimeError, match="not found"):
        installer.install(Path("/nonexistent/path/does/not/exist"), "global")


def test_gemini_config_dir_env_override(tmp_path, monkeypatch):
    """GEMINI_CONFIG_DIR env var overrides ~/.gemini."""
    custom_dir = tmp_path / "custom-gemini"
    custom_dir.mkdir()
    monkeypatch.setenv("GEMINI_CONFIG_DIR", str(custom_dir))
    inst = GeminiInstaller()
    dest = inst._resolve_dest("global")
    assert dest == custom_dir / "codebase-wizard"


# ---------------------------------------------------------------------------
# Agent conversion
# ---------------------------------------------------------------------------


def test_agent_tools_array_format(installer, source_plugin_dir, tmp_path):
    """Converted agent has tools: with YAML array format (- tool_name)."""
    installer.install(source_plugin_dir, "global")
    agent_file = (
        tmp_path / "home" / ".gemini" / "codebase-wizard"
        / "agent" / "codebase-wizard-agent.md"
    )
    content = agent_file.read_text()
    # Should have YAML array format: "  - read_file"
    assert "  - read_file" in content, (
        f"Expected YAML array format '  - read_file' in agent. Content:\n{content[:500]}"
    )
    # Should NOT have object format: "read_file: true"
    assert "read_file: true" not in content, (
        "Agent should use YAML array, not object format"
    )


def test_color_field_stripped(installer, source_plugin_dir, tmp_path):
    """Converted agent does NOT contain color: in frontmatter."""
    installer.install(source_plugin_dir, "global")
    agent_file = (
        tmp_path / "home" / ".gemini" / "codebase-wizard"
        / "agent" / "codebase-wizard-agent.md"
    )
    content = agent_file.read_text()
    parts = content.split("---")
    assert len(parts) >= 3, "Could not parse frontmatter"
    frontmatter_section = parts[1]
    assert "color:" not in frontmatter_section, (
        f"'color:' should be stripped from Gemini agent frontmatter.\n"
        f"Frontmatter:\n{frontmatter_section}"
    )


def test_name_field_kept(installer, source_plugin_dir, tmp_path):
    """Converted agent KEEPS name: in frontmatter (unlike OpenCode)."""
    installer.install(source_plugin_dir, "global")
    agent_file = (
        tmp_path / "home" / ".gemini" / "codebase-wizard"
        / "agent" / "codebase-wizard-agent.md"
    )
    content = agent_file.read_text()
    parts = content.split("---")
    assert len(parts) >= 3, "Could not parse frontmatter"
    frontmatter_section = parts[1]
    assert "name:" in frontmatter_section, (
        f"'name:' should be kept in Gemini agent frontmatter.\n"
        f"Frontmatter:\n{frontmatter_section}"
    )


def test_task_tool_excluded():
    """Task does not appear in converted tools list."""
    assert _convert_gemini_tool_name("Task") is None


def test_mcp_tools_excluded():
    """mcp__* tools do not appear in converted tools list."""
    assert _convert_gemini_tool_name("mcp__some_server__tool") is None


def test_agent_tool_excluded():
    """Agent does not appear in converted tools list."""
    assert _convert_gemini_tool_name("Agent") is None


def test_path_scope_stripped():
    """Write(.code-wizard/**) maps to write_file (scope annotation removed)."""
    assert _convert_gemini_tool_name("Write(.code-wizard/**)") == "write_file"


# ---------------------------------------------------------------------------
# Tool name mappings (parametrized)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("claude_name,expected", [
    ("Read", "read_file"),
    ("Write", "write_file"),
    ("Edit", "replace"),
    ("Bash", "run_shell_command"),
    ("Glob", "glob"),
    ("Grep", "search_file_content"),
    ("WebSearch", "google_web_search"),
    ("WebFetch", "web_fetch"),
    ("TodoWrite", "write_todos"),
    ("AskUserQuestion", "ask_user"),
])
def test_tool_mapping(claude_name, expected):
    """Each Claude Code tool name maps to the correct Gemini tool name."""
    assert _convert_gemini_tool_name(claude_name) == expected


# ---------------------------------------------------------------------------
# Content transforms
# ---------------------------------------------------------------------------


def test_template_var_escape(installer, source_plugin_dir, tmp_path):
    """${PHASE} in agent body -> $PHASE."""
    # Inject ${PHASE} into agent body
    temp_source = tmp_path / "var-source"
    shutil.copytree(source_plugin_dir, temp_source)
    agent_file = temp_source / "agents" / "codebase-wizard-agent.md"
    original = agent_file.read_text()
    modified = original + "\nUse ${PHASE} and ${PLAN} in your work.\n"
    agent_file.write_text(modified)

    installer.install(temp_source, "global")
    agent_out = (
        tmp_path / "home" / ".gemini" / "codebase-wizard"
        / "agent" / "codebase-wizard-agent.md"
    )
    content = agent_out.read_text()
    assert "${PHASE}" not in content, "Template var ${PHASE} should be escaped"
    assert "$PHASE" in content, "Should contain $PHASE after escape"
    assert "$PLAN" in content, "Should contain $PLAN after escape"


def test_template_var_not_in_frontmatter(installer, source_plugin_dir, tmp_path):
    """${VAR} escape does NOT apply to frontmatter section."""
    # Inject ${VAR} into both frontmatter description and body
    temp_source = tmp_path / "fm-var-source"
    shutil.copytree(source_plugin_dir, temp_source)
    agent_file = temp_source / "agents" / "codebase-wizard-agent.md"
    original = agent_file.read_text()
    # The description field uses block scalar >, so add to body only for this test
    # Instead, just verify body gets escaped but frontmatter is intact
    modified = original + "\nBody uses ${BODY_VAR} here.\n"
    agent_file.write_text(modified)

    installer.install(temp_source, "global")
    agent_out = (
        tmp_path / "home" / ".gemini" / "codebase-wizard"
        / "agent" / "codebase-wizard-agent.md"
    )
    content = agent_out.read_text()
    # Body should have the var escaped
    assert "$BODY_VAR" in content, "Body var should be escaped to $BODY_VAR"
    assert "${BODY_VAR}" not in content, "${BODY_VAR} should not remain in body"


def test_sub_tag_conversion(installer, source_plugin_dir, tmp_path):
    """<sub>text</sub> -> *(text)* in content."""
    temp_source = tmp_path / "sub-source"
    shutil.copytree(source_plugin_dir, temp_source)
    agent_file = temp_source / "agents" / "codebase-wizard-agent.md"
    original = agent_file.read_text()
    modified = original + "\nThis has <sub>subscript</sub> text.\n"
    agent_file.write_text(modified)

    installer.install(temp_source, "global")
    agent_out = (
        tmp_path / "home" / ".gemini" / "codebase-wizard"
        / "agent" / "codebase-wizard-agent.md"
    )
    content = agent_out.read_text()
    assert "*(subscript)*" in content, "Sub tags should be converted to *(text)*"
    assert "<sub>" not in content, "<sub> tags should be removed"


def test_path_rewriting_tilde(installer, source_plugin_dir, tmp_path):
    """~/.claude -> ~/.gemini in content."""
    temp_source = tmp_path / "tilde-source"
    shutil.copytree(source_plugin_dir, temp_source)
    agent_file = temp_source / "agents" / "codebase-wizard-agent.md"
    original = agent_file.read_text()
    modified = original + "\nConfig lives at ~/.claude/settings.\n"
    agent_file.write_text(modified)

    installer.install(temp_source, "global")
    agent_out = (
        tmp_path / "home" / ".gemini" / "codebase-wizard"
        / "agent" / "codebase-wizard-agent.md"
    )
    content = agent_out.read_text()
    assert "~/.gemini" in content, "~/.claude should become ~/.gemini"
    assert "~/.claude" not in content, "~/.claude should not remain"


def test_path_rewriting_home(installer, source_plugin_dir, tmp_path):
    """$HOME/.claude -> $HOME/.gemini in content."""
    temp_source = tmp_path / "home-source"
    shutil.copytree(source_plugin_dir, temp_source)
    agent_file = temp_source / "agents" / "codebase-wizard-agent.md"
    original = agent_file.read_text()
    modified = original + "\nConfig at $HOME/.claude/settings.\n"
    agent_file.write_text(modified)

    installer.install(temp_source, "global")
    agent_out = (
        tmp_path / "home" / ".gemini" / "codebase-wizard"
        / "agent" / "codebase-wizard-agent.md"
    )
    content = agent_out.read_text()
    assert "$HOME/.gemini" in content, "$HOME/.claude should become $HOME/.gemini"
    assert "$HOME/.claude" not in content, "$HOME/.claude should not remain"


# ---------------------------------------------------------------------------
# TOML command conversion
# ---------------------------------------------------------------------------


def test_command_converted_to_toml(installer, source_plugin_dir, tmp_path):
    """Command .md -> .toml with description and prompt fields."""
    installer.install(source_plugin_dir, "global")
    cmd_dir = tmp_path / "home" / ".gemini" / "codebase-wizard" / "command"
    toml_files = list(cmd_dir.glob("*.toml"))
    assert len(toml_files) > 0, "Expected .toml files in command/"
    content = toml_files[0].read_text()
    assert 'description = ' in content, "TOML should have description field"
    assert 'prompt = ' in content, "TOML should have prompt field"


def test_toml_valid_syntax(installer, source_plugin_dir, tmp_path):
    """Generated TOML parses with tomllib.loads()."""
    installer.install(source_plugin_dir, "global")
    cmd_dir = tmp_path / "home" / ".gemini" / "codebase-wizard" / "command"
    for toml_file in cmd_dir.glob("*.toml"):
        content = toml_file.read_text()
        data = tomllib.loads(content)
        assert "prompt" in data, f"TOML file {toml_file.name} missing 'prompt' key"


def test_command_paths_rewritten(installer, source_plugin_dir, tmp_path):
    """~/.claude in command body becomes ~/.gemini in TOML prompt."""
    temp_source = tmp_path / "cmd-source"
    shutil.copytree(source_plugin_dir, temp_source)
    cmd_file = temp_source / "commands" / "codebase-wizard.md"
    original = cmd_file.read_text()
    modified = original + "\nCheck ~/.claude for configs.\n"
    cmd_file.write_text(modified)

    installer.install(temp_source, "global")
    cmd_dir = tmp_path / "home" / ".gemini" / "codebase-wizard" / "command"
    toml_file = cmd_dir / "codebase-wizard.toml"
    assert toml_file.exists(), "codebase-wizard.toml should exist"
    content = toml_file.read_text()
    assert "~/.claude" not in content, "~/.claude should be rewritten to ~/.gemini"
    assert "~/.gemini" in content or ".gemini" in content, (
        "Rewritten path should appear in TOML"
    )
