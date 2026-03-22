"""Tests for OpenCodeInstaller — install, uninstall, status for OpenCode runtime."""

import shutil
from pathlib import Path

import pytest

from ai_codebase_mentor.converters.opencode import OpenCodeInstaller

# Path to the real plugin source (relative to project root)
REAL_PLUGIN_SOURCE = Path(__file__).parent.parent / "plugins" / "codebase-wizard"


@pytest.fixture
def source_plugin_dir(tmp_path):
    """Copy the real plugin source to a temp dir so tests don't touch the repo."""
    src = tmp_path / "plugin-source" / "codebase-wizard"
    shutil.copytree(REAL_PLUGIN_SOURCE, src)
    return src


@pytest.fixture
def installer(tmp_path, monkeypatch):
    """OpenCodeInstaller with home() and cwd() redirected to temp paths."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    return OpenCodeInstaller()


def test_global_install_creates_agent_files(installer, source_plugin_dir, tmp_path):
    """install(source, 'global') creates agents dir at ~/.config/opencode/codebase-wizard/agents/."""
    installer.install(source_plugin_dir, "global")
    agents_dir = (
        tmp_path / "home" / ".config" / "opencode" / "codebase-wizard" / "agents"
    )
    assert agents_dir.exists(), f"agents dir not found at {agents_dir}"
    assert (agents_dir / "codebase-wizard-agent.md").exists(), (
        "codebase-wizard-agent.md not found in agents dir"
    )


def test_project_install_creates_agent_files(installer, source_plugin_dir, tmp_path):
    """install(source, 'project') creates agents dir at ./.opencode/codebase-wizard/agents/."""
    installer.install(source_plugin_dir, "project")
    agents_dir = (
        tmp_path / "cwd" / ".opencode" / "codebase-wizard" / "agents"
    )
    assert agents_dir.exists(), f"agents dir not found at {agents_dir}"
    assert (agents_dir / "codebase-wizard-agent.md").exists(), (
        "codebase-wizard-agent.md not found in agents dir"
    )


def test_global_install_is_idempotent(installer, source_plugin_dir):
    """Calling install twice with target='global' does not raise."""
    installer.install(source_plugin_dir, "global")
    installer.install(source_plugin_dir, "global")  # should not raise


def test_global_uninstall_removes_directory(installer, source_plugin_dir, tmp_path):
    """uninstall('global') removes ~/.config/opencode/codebase-wizard/ entirely."""
    installer.install(source_plugin_dir, "global")
    installer.uninstall("global")
    dest = tmp_path / "home" / ".config" / "opencode" / "codebase-wizard"
    assert not dest.exists(), f"Expected directory to be removed: {dest}"


def test_project_uninstall_removes_directory(installer, source_plugin_dir, tmp_path):
    """uninstall('project') removes ./.opencode/codebase-wizard/."""
    installer.install(source_plugin_dir, "project")
    installer.uninstall("project")
    dest = tmp_path / "cwd" / ".opencode" / "codebase-wizard"
    assert not dest.exists(), f"Expected directory to be removed: {dest}"


def test_uninstall_when_not_installed_is_noop(installer):
    """uninstall('global') when nothing is installed does not raise."""
    installer.uninstall("global")  # must not raise


def test_status_after_global_install(installer, source_plugin_dir, tmp_path):
    """status() returns installed=True with correct location and version after global install."""
    installer.install(source_plugin_dir, "global")
    result = installer.status()
    expected_location = str(tmp_path / "home" / ".config" / "opencode" / "codebase-wizard")
    assert result["installed"] is True
    assert result["location"] == expected_location
    assert result["version"] == "1.0.0"


def test_status_before_install(installer):
    """status() returns installed=False with None fields before any install."""
    result = installer.status()
    assert result == {"installed": False, "location": None, "version": None}


def test_agent_tool_names_lowercased(installer, source_plugin_dir, tmp_path):
    """Converted agent file has tools: block with lowercase entries (e.g., read: true)."""
    installer.install(source_plugin_dir, "global")
    agent_file = (
        tmp_path / "home" / ".config" / "opencode" / "codebase-wizard"
        / "agents" / "codebase-wizard-agent.md"
    )
    content = agent_file.read_text()
    assert "read: true" in content, (
        f"Expected 'read: true' in converted agent file. Content snippet:\n{content[:500]}"
    )


def test_special_tool_mapping_applied(installer, source_plugin_dir, tmp_path):
    """AskUserQuestion is mapped to 'question' in the converted agent frontmatter."""
    # The setup agent has AskUserQuestion — but codebase-wizard-agent does not.
    # We verify either agent file if it has AskUserQuestion in its allowed_tools.
    # Since neither codebase-wizard agent has AskUserQuestion, we inject it for this test.
    # The setup agent has broader tools; let's check the conversion logic directly.
    # We test via the setup agent file which, if it had AskUserQuestion, would map it.
    # For this test we verify the setup-agent file converts correctly.
    # Actually, codebase-wizard-setup-agent has no AskUserQuestion either.
    # We verify via test_agent_tool_names_lowercased that mapping works, and
    # confirm that question: true would appear IF AskUserQuestion were in allowed_tools.
    # The real test: write a temp agent with AskUserQuestion and install from it.
    import tempfile, os

    # Create a minimal agent source dir with AskUserQuestion in allowed_tools
    temp_source = tmp_path / "special-source"
    shutil.copytree(source_plugin_dir, temp_source)

    test_agent = temp_source / "agents" / "codebase-wizard-agent.md"
    original = test_agent.read_text()
    # Inject AskUserQuestion into allowed_tools
    modified = original.replace(
        '  - "WebFetch"',
        '  - "WebFetch"\n  - "AskUserQuestion"',
    )
    test_agent.write_text(modified)

    installer.install(temp_source, "global")
    agent_out = (
        tmp_path / "home" / ".config" / "opencode" / "codebase-wizard"
        / "agents" / "codebase-wizard-agent.md"
    )
    content = agent_out.read_text()
    assert "question: true" in content, (
        f"Expected 'question: true' in converted agent. Content snippet:\n{content[:500]}"
    )


def test_name_field_stripped(installer, source_plugin_dir, tmp_path):
    """Converted agent file does not contain 'name:' in the frontmatter section."""
    installer.install(source_plugin_dir, "global")
    agent_file = (
        tmp_path / "home" / ".config" / "opencode" / "codebase-wizard"
        / "agents" / "codebase-wizard-agent.md"
    )
    content = agent_file.read_text()
    # Find the frontmatter section (between first and second '---')
    parts = content.split("---")
    # parts[0] is before first ---, parts[1] is the frontmatter, parts[2+] is body
    assert len(parts) >= 3, "Could not parse frontmatter from converted agent file"
    frontmatter_section = parts[1]
    assert "name:" not in frontmatter_section, (
        f"'name:' should not appear in frontmatter after conversion.\n"
        f"Frontmatter:\n{frontmatter_section}"
    )


def test_command_directory_singular(installer, source_plugin_dir, tmp_path):
    """install() creates command/ (singular) directory, not commands/."""
    installer.install(source_plugin_dir, "global")
    dest = tmp_path / "home" / ".config" / "opencode" / "codebase-wizard"
    assert (dest / "command").is_dir(), f"Expected command/ dir at {dest / 'command'}"
    assert not (dest / "commands").exists(), (
        f"commands/ (plural) should not exist; command/ (singular) should be used"
    )
    assert (dest / "command" / "codebase-wizard.md").exists(), (
        f"codebase-wizard.md not found in command/ dir"
    )


def test_subagent_type_normalized(installer, source_plugin_dir, tmp_path):
    """subagent_type: "general-purpose" is converted to "general" in output."""
    temp_source = tmp_path / "plugin-subagent"
    shutil.copytree(source_plugin_dir, temp_source)

    test_agent = temp_source / "agents" / "codebase-wizard-agent.md"
    original = test_agent.read_text()
    # Inject subagent_type field into frontmatter
    modified = original.replace(
        "name: codebase-wizard-agent",
        'name: codebase-wizard-agent\nsubagent_type: "general-purpose"',
    )
    test_agent.write_text(modified)

    installer.install(temp_source, "global")
    agent_out = (
        tmp_path / "home" / ".config" / "opencode" / "codebase-wizard"
        / "agents" / "codebase-wizard-agent.md"
    )
    content = agent_out.read_text()
    assert 'subagent_type: "general"' in content, (
        f"Expected subagent_type normalized to 'general'. Content:\n{content[:500]}"
    )
    assert "general-purpose" not in content, (
        "subagent_type 'general-purpose' should have been converted to 'general'"
    )


def test_install_raises_on_missing_source(installer):
    """install() raises RuntimeError with 'not found' message for missing source."""
    with pytest.raises(RuntimeError, match="not found"):
        installer.install(Path("/nonexistent/path/does/not/exist"), "global")
