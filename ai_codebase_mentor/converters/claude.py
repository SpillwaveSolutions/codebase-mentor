"""Claude Code runtime installer for ai-codebase-mentor.

Installs the Codebase Wizard plugin to the Claude Code plugin directories and
registers it in all three Claude Code plugin registry files:
  - known_marketplaces.json  (registers "codebase-mentor" as a git marketplace)
  - installed_plugins.json   (registers the plugin under "codebase-wizard@codebase-mentor")
  - settings.json            (enables the plugin via enabledPlugins)

Install destinations:
  Global:  ~/.claude/plugins/codebase-wizard/
  Project: ./plugins/codebase-wizard/
"""

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from .base import RuntimeInstaller, _read_version


# Registry key used in installed_plugins.json and settings.json.
# Format: "pluginname@marketplaceid" where marketplaceid is the key in known_marketplaces.json.
PLUGIN_REGISTRY_KEY = "codebase-wizard@codebase-mentor"
MARKETPLACE_ID = "codebase-mentor"
MARKETPLACE_GIT_URL = "https://github.com/SpillwaveSolutions/codebase-mentor.git"


class ClaudeInstaller(RuntimeInstaller):
    """Installs the Codebase Wizard plugin for Claude Code.

    Copies the plugin tree and registers it in all three Claude Code registry
    files so the plugin is discoverable without a marketplace server.

    Supports global install (~/.claude/plugins/) and per-project install
    (./plugins/). Both are idempotent — calling install twice updates in place.
    """

    def install(self, source: Path, target: str = "global") -> None:
        """Copy the plugin tree and register it with Claude Code.

        Writes three registry files so Claude Code loads the plugin:
          1. known_marketplaces.json — registers "codebase-mentor" git marketplace
          2. installed_plugins.json  — registers codebase-wizard@codebase-mentor
          3. settings.json           — enables the plugin

        Args:
            source: Path to the bundled plugin directory (contains .claude-plugin/).
            target: "global" → ~/.claude/plugins/codebase-wizard/
                    "project" → ./plugins/codebase-wizard/

        Raises:
            RuntimeError: If source does not exist or copy fails.
        """
        if not source.exists():
            raise RuntimeError(f"Plugin source directory not found: {source}")

        destination = self._resolve_dest(target)

        try:
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source, destination)
        except OSError as e:
            raise RuntimeError(f"Failed to install to {destination}: {e}") from e

        if target == "global":
            version = _read_version(destination) or "1.0.0"
            self._register_plugin(destination, version)

    def uninstall(self, target: str = "global") -> None:
        """Remove the installed plugin directory and unregister it.

        Args:
            target: "global" or "project" — same scope as install().

        Never raises. No-op if the plugin is not installed.
        """
        destination = self._resolve_dest(target)
        if not destination.exists():
            return
        try:
            shutil.rmtree(destination)
        except OSError as e:
            raise RuntimeError(f"Failed to uninstall from {destination}: {e}") from e

        if target == "global":
            self._unregister_plugin()

    def status(self) -> dict:
        """Report current install state for both global and project installs.

        Checks global location first, then project. Returns the first found.

        Returns:
            {"installed": bool, "location": str | None, "version": str | None}
        """
        global_dest = Path.home() / ".claude" / "plugins" / "codebase-wizard"
        if global_dest.exists():
            return {
                "installed": True,
                "location": str(global_dest),
                "version": _read_version(global_dest),
            }

        project_dest = Path.cwd() / "plugins" / "codebase-wizard"
        if project_dest.exists():
            return {
                "installed": True,
                "location": str(project_dest.resolve()),
                "version": _read_version(project_dest),
            }

        return {"installed": False, "location": None, "version": None}

    def _resolve_dest(self, target: str) -> Path:
        """Resolve the install destination based on target scope."""
        if target == "global":
            return Path.home() / ".claude" / "plugins" / "codebase-wizard"
        return Path.cwd() / "plugins" / "codebase-wizard"

    # ------------------------------------------------------------------ #
    # Registry helpers                                                     #
    # ------------------------------------------------------------------ #

    def _register_plugin(self, install_path: Path, version: str) -> None:
        """Register the plugin in all three Claude Code registry files."""
        self._register_marketplace()
        self._register_installed_plugin(install_path, version)
        self._enable_plugin()

    def _register_marketplace(self) -> None:
        """Add codebase-mentor git marketplace to known_marketplaces.json if absent."""
        path = Path.home() / ".claude" / "plugins" / "known_marketplaces.json"
        data: dict = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"Warning: Could not read {path}: {e}. "
                    "Skipping marketplace registration.",
                    file=sys.stderr,
                )
                return

        if MARKETPLACE_ID not in data:
            data[MARKETPLACE_ID] = {
                "source": {"source": "git", "url": MARKETPLACE_GIT_URL},
                "installLocation": str(
                    Path.home() / ".claude" / "plugins" / "marketplaces" / MARKETPLACE_ID
                ),
                "lastUpdated": datetime.now(timezone.utc).isoformat(),
            }
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=4) + "\n", encoding="utf-8")

    def _register_installed_plugin(self, install_path: Path, version: str) -> None:
        """Write or update the plugin entry in installed_plugins.json."""
        path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
        data: dict = {"version": 2, "plugins": {}}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"Warning: Could not read {path}: {e}. "
                    "Skipping plugin registration.",
                    file=sys.stderr,
                )
                return

        now = datetime.now(timezone.utc).isoformat()
        existing = data.get("plugins", {}).get(PLUGIN_REGISTRY_KEY, [{}])
        installed_at = existing[0].get("installedAt", now) if existing else now

        if "plugins" not in data:
            data["plugins"] = {}
        data["plugins"][PLUGIN_REGISTRY_KEY] = [
            {
                "scope": "user",
                "installPath": str(install_path),
                "version": version,
                "installedAt": installed_at,
                "lastUpdated": now,
                "gitCommitSha": "",
            }
        ]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _enable_plugin(self) -> None:
        """Set enabledPlugins[codebase-wizard@codebase-mentor] = true in settings.json."""
        path = Path.home() / ".claude" / "settings.json"
        data: dict = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"Warning: Could not read {path}: {e}. "
                    "Skipping plugin enable.",
                    file=sys.stderr,
                )
                return

        if "enabledPlugins" not in data:
            data["enabledPlugins"] = {}
        data["enabledPlugins"][PLUGIN_REGISTRY_KEY] = True
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _unregister_plugin(self) -> None:
        """Remove the plugin entry from installed_plugins.json and settings.json."""
        # Remove from installed_plugins.json
        installed_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
        if installed_path.exists():
            try:
                data = json.loads(installed_path.read_text(encoding="utf-8"))
                data.get("plugins", {}).pop(PLUGIN_REGISTRY_KEY, None)
                installed_path.write_text(
                    json.dumps(data, indent=2) + "\n", encoding="utf-8"
                )
            except (json.JSONDecodeError, OSError):
                pass

        # Remove from settings.json enabledPlugins
        settings_path = Path.home() / ".claude" / "settings.json"
        if settings_path.exists():
            try:
                data = json.loads(settings_path.read_text(encoding="utf-8"))
                data.get("enabledPlugins", {}).pop(PLUGIN_REGISTRY_KEY, None)
                settings_path.write_text(
                    json.dumps(data, indent=2) + "\n", encoding="utf-8"
                )
            except (json.JSONDecodeError, OSError):
                pass
