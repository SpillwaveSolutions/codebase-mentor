"""Claude Code runtime installer for ai-codebase-mentor.

Installs the Codebase Wizard plugin to the Claude Code plugin cache and
registers it in all three Claude Code plugin registry files:
  - known_marketplaces.json  (registers "codebase-mentor" as a git marketplace)
  - installed_plugins.json   (registers the plugin under "codebase-wizard@codebase-mentor")
  - settings.json            (enables the plugin via enabledPlugins)

Claude Code loads plugins from a versioned cache directory:
  ~/.claude/plugins/cache/{marketplace}/{plugin}/{version}/

Install destinations:
  Global:  ~/.claude/plugins/cache/codebase-mentor/codebase-wizard/{version}/
  Project: ./plugins/codebase-wizard/
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .base import RuntimeInstaller, _read_version


# Registry key used in installed_plugins.json and settings.json.
# Format: "pluginname@marketplaceid" where marketplaceid is the key in known_marketplaces.json.
PLUGIN_NAME = "codebase-wizard"
PLUGIN_REGISTRY_KEY = "codebase-wizard@codebase-mentor"
MARKETPLACE_ID = "codebase-mentor"
MARKETPLACE_GIT_URL = "https://github.com/SpillwaveSolutions/codebase-mentor.git"


def _git_sha() -> str:
    """Return current HEAD commit SHA, or empty string if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


class ClaudeInstaller(RuntimeInstaller):
    """Installs the Codebase Wizard plugin for Claude Code.

    Copies the plugin tree to the versioned Claude Code cache directory and
    registers it in all three Claude Code registry files so the plugin loads
    on next session start.

    Supports global install (~/.claude/plugins/cache/.../version/) and
    per-project install (./plugins/codebase-wizard/). Both are idempotent —
    calling install again replaces the current version in place.
    """

    def install(self, source: Path, target: str = "global") -> None:
        """Copy the plugin tree to the Claude Code cache and register it.

        Writes three registry files so Claude Code loads the plugin:
          1. known_marketplaces.json — registers "codebase-mentor" git marketplace
          2. installed_plugins.json  — registers codebase-wizard@codebase-mentor
          3. settings.json           — enables the plugin

        On update: removes old version directories from the cache before
        installing the new version (avoids version directory accumulation).

        Args:
            source: Path to the bundled plugin directory (contains .claude-plugin/).
            target: "global" → ~/.claude/plugins/cache/codebase-mentor/codebase-wizard/{version}/
                    "project" → ./plugins/codebase-wizard/

        Raises:
            RuntimeError: If source does not exist or copy fails.
        """
        if not source.exists():
            raise RuntimeError(f"Plugin source directory not found: {source}")

        version = _read_version(source) or "1.0.0"
        destination = self._resolve_dest(target, version)

        # Remove stale version directories before installing (handles updates).
        if target == "global":
            cache_plugin_dir = destination.parent
            if cache_plugin_dir.exists():
                for stale in cache_plugin_dir.iterdir():
                    if stale.is_dir() and stale != destination:
                        shutil.rmtree(stale, ignore_errors=True)

        try:
            if destination.exists():
                shutil.rmtree(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, destination)
        except OSError as e:
            raise RuntimeError(f"Failed to install to {destination}: {e}") from e

        if target == "global":
            self._register_plugin(destination, version, _git_sha())

    def uninstall(self, target: str = "global") -> None:
        """Remove the installed plugin and unregister it.

        For global installs, removes the entire plugin directory from the
        cache (all versions) and cleans up all three registry files.

        Args:
            target: "global" or "project" — same scope as install().

        Never raises. No-op if the plugin is not installed.
        """
        if target == "global":
            cache_plugin_dir = (
                Path.home()
                / ".claude"
                / "plugins"
                / "cache"
                / MARKETPLACE_ID
                / PLUGIN_NAME
            )
            if cache_plugin_dir.exists():
                try:
                    shutil.rmtree(cache_plugin_dir)
                except OSError as e:
                    raise RuntimeError(
                        f"Failed to uninstall from {cache_plugin_dir}: {e}"
                    ) from e
            self._unregister_plugin()
        else:
            destination = Path.cwd() / "plugins" / PLUGIN_NAME
            if not destination.exists():
                return
            try:
                shutil.rmtree(destination)
            except OSError as e:
                raise RuntimeError(f"Failed to uninstall from {destination}: {e}") from e

    def status(self) -> dict:
        """Report current install state for both global and project installs.

        For global installs, checks the cache directory for any installed version.
        Returns the first found.

        Returns:
            {"installed": bool, "location": str | None, "version": str | None}
        """
        cache_plugin_dir = (
            Path.home()
            / ".claude"
            / "plugins"
            / "cache"
            / MARKETPLACE_ID
            / PLUGIN_NAME
        )
        if cache_plugin_dir.exists():
            versions = sorted(d for d in cache_plugin_dir.iterdir() if d.is_dir())
            if versions:
                latest = versions[-1]
                return {
                    "installed": True,
                    "location": str(latest),
                    "version": _read_version(latest),
                }

        project_dest = Path.cwd() / "plugins" / PLUGIN_NAME
        if project_dest.exists():
            return {
                "installed": True,
                "location": str(project_dest.resolve()),
                "version": _read_version(project_dest),
            }

        return {"installed": False, "location": None, "version": None}

    def _resolve_dest(self, target: str, version: str = "1.0.0") -> Path:
        """Resolve the install destination based on target scope and version."""
        if target == "global":
            return (
                Path.home()
                / ".claude"
                / "plugins"
                / "cache"
                / MARKETPLACE_ID
                / PLUGIN_NAME
                / version
            )
        return Path.cwd() / "plugins" / PLUGIN_NAME

    # ------------------------------------------------------------------ #
    # Registry helpers                                                     #
    # ------------------------------------------------------------------ #

    def _register_plugin(
        self, install_path: Path, version: str, git_sha: str = ""
    ) -> None:
        """Register the plugin in all three Claude Code registry files."""
        self._register_marketplace()
        self._register_installed_plugin(install_path, version, git_sha)
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

    def _register_installed_plugin(
        self, install_path: Path, version: str, git_sha: str = ""
    ) -> None:
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
                "gitCommitSha": git_sha,
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
