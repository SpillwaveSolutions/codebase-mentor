"""OpenCode runtime installer for ai-codebase-mentor.

Installs the Codebase Wizard plugin to the OpenCode configuration directories:
  Global:  ~/.config/opencode/codebase-wizard/
  Project: ./.opencode/codebase-wizard/

Agent frontmatter is converted from Claude Code format (allowed_tools: array)
to OpenCode format (tools: object with lowercase keys). OpenCode uses singular
directory names: agent/, command/, skill/ (not agents/, commands/, skills/).
"""

import json
import re
import shutil
import sys
from pathlib import Path

from .base import RuntimeInstaller, _read_version


# Special tool name mappings: Claude Code tool name -> OpenCode tool name
SPECIAL_MAPPINGS = {
    "AskUserQuestion": "question",
    "SkillTool": "skill",
    "TodoWrite": "todowrite",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
}

# Named color -> hex value conversion
COLOR_MAP = {
    "cyan": "#00FFFF", "red": "#FF0000", "green": "#00FF00",
    "blue": "#0000FF", "yellow": "#FFFF00", "magenta": "#FF00FF",
    "orange": "#FFA500", "purple": "#800080", "pink": "#FFC0CB",
    "white": "#FFFFFF", "black": "#000000", "gray": "#808080", "grey": "#808080",
}

# Path rewrites applied to all output files (agents and commands)
# Longer match listed first to avoid partial replacements
PATH_REWRITES = [
    ("~/.claude/plugins/", "~/.config/opencode/"),
    ("~/.claude", "~/.config/opencode"),
]


def _convert_tool_name(tool: str) -> str:
    """Convert a Claude Code tool name to its OpenCode equivalent.

    Strips path scope annotations (e.g. "Write(.code-wizard/**)" -> "Write"),
    applies special mappings (e.g. "AskUserQuestion" -> "question"),
    passes mcp__ names through unchanged, and lowercases all others.

    Args:
        tool: Raw tool name string from Claude Code allowed_tools list.

    Returns:
        OpenCode tool name string.
    """
    # Strip path scope annotation: "Write(.code-wizard/**)" -> "Write"
    base = tool.split("(")[0]
    if base in SPECIAL_MAPPINGS:
        return SPECIAL_MAPPINGS[base]
    if base.startswith("mcp__"):
        return base  # pass through unchanged
    return base.lower()


def _convert_agent_frontmatter(content: str) -> str:
    """Convert Claude Code agent frontmatter to OpenCode format.

    Transformations applied:
    - allowed_tools: array  ->  tools: object with {name}: true entries
    - name: field removed (OpenCode derives name from filename)
    - color: named value -> hex (e.g. cyan -> "#00FFFF")

    Args:
        content: Full agent file content (frontmatter + body).

    Returns:
        Converted file content with OpenCode-compatible frontmatter.
    """
    # Split on --- markers to isolate YAML frontmatter.
    # A valid markdown file with frontmatter looks like:
    #   ---\n[yaml]\n---\n[body]
    # We split on '\n---' to find the closing delimiter robustly.
    if not content.startswith("---"):
        return content

    # Find the closing --- of the frontmatter block
    # After the opening ---, find the next --- on its own line
    rest = content[3:]  # strip leading ---
    close_idx = re.search(r'\n---(\n|$)', rest)
    if not close_idx:
        return content

    frontmatter = rest[:close_idx.start()]
    body = rest[close_idx.start():]  # includes the closing ---

    # --- Parse YAML frontmatter line by line ---
    # We need to understand the YAML block structure to correctly identify
    # the allowed_tools: list vs. content inside a block scalar (e.g. description: >)
    #
    # YAML block scalar rules: a key followed by > or | introduces a block scalar.
    # All subsequent lines that are MORE indented than the key are part of the scalar.
    # The scalar ends when we hit a line with indentation <= the key's indentation.
    #
    # Top-level keys in our frontmatter have 0 indentation.
    # We track: are we inside a block scalar? If so, skip until indentation returns to 0.

    tool_names: list[str] = []
    in_allowed_tools = False
    in_block_scalar = False
    new_fm_lines: list[str] = []

    for line in frontmatter.splitlines():
        # Detect top-level YAML key (0-indent, starts with a word char or quoted string)
        is_top_level_key = bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*:', line))

        if is_top_level_key:
            # Leaving any block scalar or allowed_tools block
            in_block_scalar = False
            in_allowed_tools = False

        if in_block_scalar:
            # We're inside a multi-line block scalar (e.g. description: >)
            # Don't process this content — just skip it (it's not YAML keys)
            continue

        if in_allowed_tools:
            # We're in the allowed_tools: list
            # Tool entries are indented list items: '  - "ToolName"'
            tool_match = re.match(r'\s+-\s+"([^"]+)"', line)
            if tool_match:
                raw_tool = tool_match.group(1)
                converted = _convert_tool_name(raw_tool)
                if converted not in tool_names:
                    tool_names.append(converted)
            # Skip all lines (list items and comments) in this block
            continue

        if is_top_level_key:
            stripped = line.strip()

            # Check if this key starts a block scalar (value ends with > or |)
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*:\s*[>|]', line):
                in_block_scalar = True
                # Emit the key line (description: > etc.) — keep it
                new_fm_lines.append(line)
                continue

            # Skip name: field (OpenCode derives name from filename)
            if re.match(r'^name:', line):
                continue

            # Normalize subagent_type: "general-purpose" -> "general"
            if re.match(r'^subagent_type:', line):
                line = re.sub(r'"?general-purpose"?', '"general"', line)

            # Start of allowed_tools: block — skip the key line and enter block mode
            if re.match(r'^allowed_tools:', line):
                in_allowed_tools = True
                continue

            # Convert color: named -> hex
            color_match = re.match(r'^(color:\s*)(\S+)\s*$', line)
            if color_match:
                prefix = color_match.group(1)
                color_val = color_match.group(2).strip('"\'')
                if color_val in COLOR_MAP:
                    line = f'{prefix}"{COLOR_MAP[color_val]}"'

        new_fm_lines.append(line)

    # Build new tools: block
    tools_block_lines: list[str] = []
    if tool_names:
        tools_block_lines.append("tools:")
        for tool in tool_names:
            tools_block_lines.append(f"  {tool}: true")

    # Insert tools block before other frontmatter fields
    final_fm_lines = tools_block_lines + new_fm_lines

    # Reassemble the file
    new_frontmatter = "\n".join(final_fm_lines)
    return f"---\n{new_frontmatter}\n---{body}"


def _rewrite_paths(content: str) -> str:
    """Apply content path rewrites to replace Claude paths with OpenCode paths.

    Applies PATH_REWRITES in order (longer matches first).

    Args:
        content: File content string.

    Returns:
        Content with ~/.claude references replaced with ~/.config/opencode.
    """
    for old, new in PATH_REWRITES:
        content = content.replace(old, new)
    return content


def _has_context_fork(content: str) -> bool:
    """Return True if markdown frontmatter contains 'context: fork'.

    Args:
        content: Full file content string (frontmatter + body).

    Returns:
        True if the YAML frontmatter has a top-level 'context: fork' field.
    """
    if not content.startswith("---"):
        return False
    rest = content[3:]
    close_idx = re.search(r'\n---(\n|$)', rest)
    if not close_idx:
        return False
    frontmatter = rest[:close_idx.start()]
    return bool(re.search(r'^context:\s*fork\s*$', frontmatter, re.MULTILINE))


class OpenCodeInstaller(RuntimeInstaller):
    """Installs the Codebase Wizard plugin for OpenCode.

    Converts Claude Code plugin format to OpenCode-native files:
    - Agent frontmatter: allowed_tools -> tools object, name removed, colors hex-encoded
    - Commands: copied to command/ (singular), paths rewritten
    - Skills: copied verbatim (runtime-agnostic)
    - opencode.json: permission pre-authorization written to parent directory

    Supports global install (~/.config/opencode/) and per-project install (./.opencode/).
    Both are idempotent — calling install twice updates in place.
    """

    def _resolve_dest(self, target: str) -> Path:
        """Resolve the install destination based on target scope.

        Args:
            target: "global" or "project".

        Returns:
            Absolute path to the codebase-wizard install directory.
        """
        if target == "global":
            return Path.home() / ".config" / "opencode" / "codebase-wizard"
        return Path.cwd() / ".opencode" / "codebase-wizard"

    def install(self, source: Path, target: str = "global") -> None:
        """Convert and install the plugin to the OpenCode configuration directory.

        Converts agent frontmatter, renames commands/ -> command/, agents/ -> agent/,
        skills/ -> skill/, and writes opencode.json permission pre-authorization.

        Args:
            source: Path to the bundled plugin directory (contains .claude-plugin/).
            target: "global" -> ~/.config/opencode/codebase-wizard/
                    "project" -> ./.opencode/codebase-wizard/

        Raises:
            RuntimeError: If source does not exist or install fails.
        """
        if not source.exists():
            raise RuntimeError(f"Plugin source directory not found: {source}")

        destination = self._resolve_dest(target)

        try:
            if destination.exists():
                shutil.rmtree(destination)
            destination.mkdir(parents=True, exist_ok=True)

            # Convert and copy agent files
            agents_src = source / "agents"
            agents_dst = destination / "agent"
            agents_dst.mkdir(parents=True, exist_ok=True)
            for agent_file in agents_src.glob("*.md"):
                content = agent_file.read_text(encoding="utf-8")
                content = _convert_agent_frontmatter(content)
                content = _rewrite_paths(content)
                (agents_dst / agent_file.name).write_text(content, encoding="utf-8")

            # Copy commands -> command/ (singular), with path rewriting
            # Detect context: fork in frontmatter and collect for subtask config
            commands_src = source / "commands"
            command_dst = destination / "command"
            command_dst.mkdir(parents=True, exist_ok=True)
            fork_commands = []
            for cmd_file in commands_src.glob("*.md"):
                content = cmd_file.read_text(encoding="utf-8")
                if _has_context_fork(content):
                    fork_commands.append(cmd_file.stem)
                content = _rewrite_paths(content)
                (command_dst / cmd_file.name).write_text(content, encoding="utf-8")

            # Copy skills verbatim (runtime-agnostic)
            skills_src = source / "skills"
            if skills_src.exists():
                shutil.copytree(skills_src, destination / "skill")

            # Copy .claude-plugin directory (for version reading)
            claude_plugin_src = source / ".claude-plugin"
            if claude_plugin_src.exists():
                shutil.copytree(claude_plugin_src, destination / ".claude-plugin")

            # Write opencode.json permission pre-authorization
            self._write_opencode_permissions(destination, target)

            # Write subtask entries for commands with context: fork
            if fork_commands:
                self._write_opencode_subtasks(destination, fork_commands)

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
        shutil.rmtree(destination)

    def status(self) -> dict:
        """Report current install state for both global and project installs.

        Checks global location first, then project. Returns the first found.

        Returns:
            {"installed": bool, "location": str | None, "version": str | None}
        """
        global_dest = Path.home() / ".config" / "opencode" / "codebase-wizard"
        if global_dest.exists():
            return {
                "installed": True,
                "location": str(global_dest),
                "version": _read_version(global_dest),
            }

        project_dest = Path.cwd() / ".opencode" / "codebase-wizard"
        if project_dest.exists():
            return {
                "installed": True,
                "location": str(project_dest),
                "version": _read_version(project_dest),
            }

        return {"installed": False, "location": None, "version": None}

    def _write_opencode_permissions(self, dest: Path, target: str) -> None:
        """Write or merge opencode.json permission pre-authorization.

        Writes to the parent directory of the install dir (e.g.,
        ~/.config/opencode/opencode.json for global installs).

        If opencode.json already exists with valid JSON, merges permission entries.
        If JSON parse fails, prints a warning to stderr and skips (does not abort).

        Args:
            dest: The codebase-wizard install directory.
            target: "global" or "project" — determines the permission path used.
        """
        json_path = dest.parent / "opencode.json"

        if target == "global":
            perm_path = "~/.config/opencode/codebase-wizard/*"
        else:
            perm_path = "./.opencode/codebase-wizard/*"

        new_perms = {
            "read": {perm_path: "allow"},
            "external_directory": {perm_path: "allow"},
        }

        data: dict = {}
        if json_path.exists():
            try:
                with json_path.open() as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"Warning: Could not parse {json_path}: {e}. "
                    "Skipping permission configuration.",
                    file=sys.stderr,
                )
                return

        # Merge permission entries
        if "permission" not in data:
            data["permission"] = {}

        for key, entries in new_perms.items():
            if key not in data["permission"]:
                data["permission"][key] = {}
            data["permission"][key].update(entries)

        # Ensure parent directory exists before writing
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with json_path.open("w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

    def _write_opencode_subtasks(self, dest: Path, fork_commands: list) -> None:
        """Write or merge command subtask entries into opencode.json.

        Writes to dest.parent / "opencode.json" (same file as permissions).
        Merges command entries — does not overwrite existing keys.

        Args:
            dest: The codebase-wizard install directory.
            fork_commands: List of command names (stems) that have context:fork.
        """
        json_path = dest.parent / "opencode.json"
        data: dict = {}
        if json_path.exists():
            try:
                with json_path.open() as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(
                    f"Warning: Could not parse {json_path}: {e}. "
                    "Skipping subtask configuration.",
                    file=sys.stderr,
                )
                return
        if "command" not in data:
            data["command"] = {}
        for cmd_name in fork_commands:
            data["command"][cmd_name] = {"subtask": True}
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with json_path.open("w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
