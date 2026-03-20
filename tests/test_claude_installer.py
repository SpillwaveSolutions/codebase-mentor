"""Tests for ClaudeInstaller — install, uninstall, status for Claude Code runtime."""

import shutil
from pathlib import Path

import pytest

from ai_codebase_mentor.converters.claude import ClaudeInstaller

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
    """ClaudeInstaller with home() and cwd() redirected to temp paths."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    fake_cwd = tmp_path / "cwd"
    fake_cwd.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    monkeypatch.chdir(fake_cwd)
    return ClaudeInstaller()


def test_global_install_copies_plugin_json(installer, source_plugin_dir, tmp_path):
    """install(source, 'global') copies plugin.json to ~/.claude/plugins/codebase-wizard/."""
    installer.install(source_plugin_dir, "global")
    dest_manifest = (
        tmp_path / "home" / ".claude" / "plugins" / "codebase-wizard"
        / ".claude-plugin" / "plugin.json"
    )
    assert dest_manifest.exists(), f"plugin.json not found at {dest_manifest}"


def test_project_install_copies_plugin_json(installer, source_plugin_dir, tmp_path):
    """install(source, 'project') copies plugin.json to ./plugins/codebase-wizard/."""
    installer.install(source_plugin_dir, "project")
    dest_manifest = (
        tmp_path / "cwd" / "plugins" / "codebase-wizard"
        / ".claude-plugin" / "plugin.json"
    )
    assert dest_manifest.exists(), f"plugin.json not found at {dest_manifest}"


def test_global_install_is_idempotent(installer, source_plugin_dir):
    """Calling install twice with target='global' does not raise."""
    installer.install(source_plugin_dir, "global")
    installer.install(source_plugin_dir, "global")  # should not raise


def test_global_uninstall_removes_directory(installer, source_plugin_dir, tmp_path):
    """uninstall('global') removes ~/.claude/plugins/codebase-wizard/ entirely."""
    installer.install(source_plugin_dir, "global")
    installer.uninstall("global")
    dest = tmp_path / "home" / ".claude" / "plugins" / "codebase-wizard"
    assert not dest.exists(), f"Expected directory to be removed: {dest}"


def test_project_uninstall_removes_directory(installer, source_plugin_dir, tmp_path):
    """uninstall('project') removes ./plugins/codebase-wizard/."""
    installer.install(source_plugin_dir, "project")
    installer.uninstall("project")
    dest = tmp_path / "cwd" / "plugins" / "codebase-wizard"
    assert not dest.exists(), f"Expected directory to be removed: {dest}"


def test_uninstall_when_not_installed_is_noop(installer):
    """uninstall('global') when nothing is installed does not raise."""
    installer.uninstall("global")  # must not raise


def test_status_after_global_install(installer, source_plugin_dir, tmp_path):
    """status() returns installed=True with correct location and version after global install."""
    installer.install(source_plugin_dir, "global")
    result = installer.status()
    expected_location = str(tmp_path / "home" / ".claude" / "plugins" / "codebase-wizard")
    assert result["installed"] is True
    assert result["location"] == expected_location
    assert result["version"] == "1.0.0"


def test_status_before_install(installer):
    """status() returns installed=False with None fields before any install."""
    result = installer.status()
    assert result == {"installed": False, "location": None, "version": None}


def test_install_raises_runtime_error_on_bad_source(installer):
    """install() raises RuntimeError with a human-readable message for missing source."""
    with pytest.raises(RuntimeError, match="not found"):
        installer.install(Path("/nonexistent/path/does/not/exist"), "global")
