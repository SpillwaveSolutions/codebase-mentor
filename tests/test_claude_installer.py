"""Tests for ClaudeInstaller — install, uninstall, status for Claude Code runtime."""

import json
import shutil
from pathlib import Path

import pytest

from ai_codebase_mentor.converters.claude import ClaudeInstaller, PLUGIN_REGISTRY_KEY

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


def test_install_registers_in_installed_plugins_json(installer, source_plugin_dir, tmp_path):
    """install() writes codebase-wizard@codebase-mentor entry to installed_plugins.json."""
    installer.install(source_plugin_dir, "global")
    registry_path = tmp_path / "home" / ".claude" / "plugins" / "installed_plugins.json"
    assert registry_path.exists(), "installed_plugins.json not created"
    data = json.loads(registry_path.read_text())
    assert PLUGIN_REGISTRY_KEY in data["plugins"], (
        f"'{PLUGIN_REGISTRY_KEY}' not found in installed_plugins.json"
    )
    entry = data["plugins"][PLUGIN_REGISTRY_KEY][0]
    assert entry["scope"] == "user"
    assert "installPath" in entry
    assert entry["version"] == "1.0.0"
    assert "installedAt" in entry
    assert "lastUpdated" in entry


def test_install_enables_plugin_in_settings_json(installer, source_plugin_dir, tmp_path):
    """install() sets enabledPlugins[codebase-wizard@codebase-mentor] = True in settings.json."""
    installer.install(source_plugin_dir, "global")
    settings_path = tmp_path / "home" / ".claude" / "settings.json"
    assert settings_path.exists(), "settings.json not created"
    data = json.loads(settings_path.read_text())
    assert data.get("enabledPlugins", {}).get(PLUGIN_REGISTRY_KEY) is True, (
        f"'{PLUGIN_REGISTRY_KEY}' not enabled in settings.json"
    )


def test_install_registers_codebase_mentor_marketplace(installer, source_plugin_dir, tmp_path):
    """install() adds 'codebase-mentor' git entry to known_marketplaces.json."""
    installer.install(source_plugin_dir, "global")
    mp_path = tmp_path / "home" / ".claude" / "plugins" / "known_marketplaces.json"
    assert mp_path.exists(), "known_marketplaces.json not created"
    data = json.loads(mp_path.read_text())
    assert "codebase-mentor" in data, "'codebase-mentor' marketplace not registered"
    entry = data["codebase-mentor"]
    assert entry["source"]["source"] == "git", "marketplace source should be 'git'"
    assert "url" in entry["source"], "marketplace source should have url"


def test_uninstall_removes_registration(installer, source_plugin_dir, tmp_path):
    """uninstall() removes codebase-wizard@codebase-mentor from installed_plugins.json and settings.json."""
    installer.install(source_plugin_dir, "global")
    installer.uninstall("global")
    registry_path = tmp_path / "home" / ".claude" / "plugins" / "installed_plugins.json"
    if registry_path.exists():
        data = json.loads(registry_path.read_text())
        assert PLUGIN_REGISTRY_KEY not in data.get("plugins", {}), (
            f"'{PLUGIN_REGISTRY_KEY}' still in installed_plugins.json after uninstall"
        )
    settings_path = tmp_path / "home" / ".claude" / "settings.json"
    if settings_path.exists():
        data = json.loads(settings_path.read_text())
        assert PLUGIN_REGISTRY_KEY not in data.get("enabledPlugins", {}), (
            f"'{PLUGIN_REGISTRY_KEY}' still in settings.json enabledPlugins after uninstall"
        )
