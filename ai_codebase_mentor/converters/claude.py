"""Claude Code runtime installer for ai-codebase-mentor.

Installs the Codebase Wizard plugin to the Claude Code plugin directories:
  Global:  ~/.claude/plugins/codebase-wizard/
  Project: ./plugins/codebase-wizard/
"""

import shutil
from pathlib import Path

from .base import RuntimeInstaller, _read_version


class ClaudeInstaller(RuntimeInstaller):
    """Installs the Codebase Wizard plugin for Claude Code.

    Supports global install (~/.claude/plugins/) and per-project install
    (./plugins/). Both are idempotent — calling install twice updates in place.
    """

    def install(self, source: Path, target: str = "global") -> None:
        """Copy the plugin tree to the Claude Code plugin directory.

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

    def uninstall(self, target: str = "global") -> None:
        """Remove the installed plugin directory.

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
