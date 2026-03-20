"""Abstract base class for all ai-codebase-mentor runtime converters.

Contract:
- install() raises RuntimeError with a human-readable message on failure.
- uninstall() is always safe to call — no-op if not installed (never raises).
- install() is idempotent: calling it when already installed updates in place.
- status() always returns a dict with keys: installed, location, version.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import json


class RuntimeInstaller(ABC):
    """Base class for all runtime-specific plugin installers.

    Each runtime (Claude Code, OpenCode, Codex, Gemini) subclasses this and
    implements install(), uninstall(), and status() for its own install paths
    and file format conventions.

    Error contract:
        install() raises RuntimeError on failure with a human-readable message.
        uninstall() is a no-op if not installed — never raises.
        All install() implementations must be idempotent.

    Status return shape:
        {"installed": bool, "location": str | None, "version": str | None}
    """

    @property
    def plugin_source(self) -> Path:
        """Return path to the bundled plugin directory.

        Resolves to ai_codebase_mentor/plugin/ relative to this file's location.
        Subclasses can override if they use a different bundle path.
        """
        return Path(__file__).parent.parent / "plugin"

    @abstractmethod
    def install(self, source: Path, target: str = "global") -> None:
        """Install the plugin from the bundled source directory.

        Args:
            source: Path to the bundled plugin directory
                    (ai_codebase_mentor/plugin/).
            target: "global" installs to ~/.{runtime}/plugins/codebase-wizard/
                    "project" installs to ./plugins/codebase-wizard/

        Raises:
            RuntimeError: If install fails for any reason. Message must be
                          human-readable (shown directly to the user).
        """

    @abstractmethod
    def uninstall(self, target: str = "global") -> None:
        """Remove all files written by install().

        Args:
            target: Same scope as install() — "global" or "project".

        Never raises. If the plugin is not installed, this is a no-op.
        """

    @abstractmethod
    def status(self) -> dict:
        """Report the current install state.

        Returns:
            {
                "installed": bool,
                "location": str | None,  # absolute path to install dir, or None
                "version": str | None,   # version string from plugin.json, or None
            }
        """


def _read_version(plugin_dir: Path) -> str | None:
    """Read the version field from a plugin directory's plugin.json.

    Args:
        plugin_dir: Root of the plugin directory (contains .claude-plugin/).

    Returns:
        Version string if found, None if the file is missing or key is absent.
        Never raises.
    """
    try:
        manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        with manifest.open() as f:
            data = json.load(f)
        return data.get("version")
    except Exception:
        return None
