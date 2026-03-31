"""Gemini CLI runtime installer for ai-codebase-mentor.

Installs the Codebase Wizard plugin to Gemini CLI configuration directories:
  Global:  ~/.gemini/codebase-wizard/
  Project: ./.gemini/codebase-wizard/

Agent frontmatter is converted from Claude Code format (allowed_tools: array)
to Gemini format (tools: YAML array with snake_case names). Command files are
converted from Markdown+YAML to TOML format (.toml extension).
"""

import json
import os
import re
import shutil
from pathlib import Path

from .base import RuntimeInstaller, _read_version


# Claude Code tool name -> Gemini CLI tool name
GEMINI_TOOL_MAP = {
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "replace",
    "Bash": "run_shell_command",
    "Glob": "glob",
    "Grep": "search_file_content",
    "WebSearch": "google_web_search",
    "WebFetch": "web_fetch",
    "TodoWrite": "write_todos",
    "AskUserQuestion": "ask_user",
}

# Path rewrites applied to all output content.
# Longer match listed first to avoid partial replacements.
PATH_REWRITES_GEMINI = [
    ("$HOME/.claude", "$HOME/.gemini"),
    ("~/.claude", "~/.gemini"),
]


def _convert_gemini_tool_name(tool: str) -> str | None:
    """Convert a Claude Code tool name to its Gemini CLI equivalent.

    Strips path scope annotations (e.g. "Write(.code-wizard/**)" -> "Write"),
    returns None for excluded tools (Task, Agent, mcp__*),
    maps known tools via GEMINI_TOOL_MAP, and lowercases unknown tools.

    Args:
        tool: Raw tool name string from Claude Code allowed_tools list.

    Returns:
        Gemini tool name string, or None if the tool should be excluded.
    """
    base = tool.split("(")[0]
    if base.startswith("mcp__"):
        return None
    if base in ("Task", "Agent"):
        return None
    return GEMINI_TOOL_MAP.get(base, base.lower())


def _rewrite_paths(content: str) -> str:
    """Apply content path rewrites to replace Claude paths with Gemini paths.

    Applies PATH_REWRITES_GEMINI in order (longer matches first).

    Args:
        content: File content string.

    Returns:
        Content with ~/.claude references replaced with ~/.gemini.
    """
    for old, new in PATH_REWRITES_GEMINI:
        content = content.replace(old, new)
    return content


def _escape_template_vars(content: str) -> str:
    """Convert ${VAR} patterns to $VAR to avoid Gemini templateString() conflicts.

    Args:
        content: File content string.

    Returns:
        Content with ${VAR} replaced by $VAR.
    """
    return re.sub(r'\$\{(\w+)\}', r'$\1', content)


def _strip_sub_tags(content: str) -> str:
    """Convert <sub>text</sub> HTML tags to *(text)* for terminal rendering.

    Args:
        content: File content string.

    Returns:
        Content with <sub> tags converted to italic format.
    """
    return re.sub(r'<sub>(.*?)</sub>', r'*(\1)*', content)


def _convert_agent_frontmatter(content: str) -> str:
    """Convert Claude Code agent frontmatter to Gemini format.

    Transformations applied:
    - allowed_tools: array -> tools: YAML array with snake_case names
    - color: field stripped entirely (Gemini validator rejects unknown fields)
    - skills: field stripped entirely (Gemini validator rejects unknown fields)
    - name: field KEPT (unlike OpenCode which strips it)
    - Content transforms (_escape_template_vars, _strip_sub_tags, _rewrite_paths)
      applied to BODY only, not frontmatter

    Args:
        content: Full agent file content (frontmatter + body).

    Returns:
        Converted file content with Gemini-compatible frontmatter.
    """
    if not content.startswith("---"):
        return _apply_body_transforms(content)

    # Find the closing --- of the frontmatter block
    rest = content[3:]  # strip leading ---
    close_idx = re.search(r'\n---(\n|$)', rest)
    if not close_idx:
        return _apply_body_transforms(content)

    frontmatter = rest[:close_idx.start()]
    body = rest[close_idx.end():]  # everything after the closing ---

    # --- Parse YAML frontmatter line by line ---
    tool_names: list[str] = []
    in_allowed_tools = False
    in_block_scalar = False
    new_fm_lines: list[str] = []

    for line in frontmatter.splitlines():
        # Detect top-level YAML key (0-indent, starts with a word char)
        is_top_level_key = bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*:', line))

        if is_top_level_key:
            in_block_scalar = False
            in_allowed_tools = False

        if in_block_scalar:
            # Inside a multi-line block scalar (e.g. description: >)
            # These lines are part of the scalar value, not YAML keys
            continue

        if in_allowed_tools:
            # Inside the allowed_tools: list
            tool_match = re.match(r'\s+-\s+"([^"]+)"', line)
            if tool_match:
                raw_tool = tool_match.group(1)
                converted = _convert_gemini_tool_name(raw_tool)
                if converted is not None and converted not in tool_names:
                    tool_names.append(converted)
            # Skip all lines in this block (list items and comments)
            continue

        if is_top_level_key:
            # Check if this key starts a block scalar (value ends with > or |)
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*:\s*[>|]', line):
                in_block_scalar = True
                new_fm_lines.append(line)
                continue

            # Strip color: field entirely (Gemini rejects unknown fields)
            if re.match(r'^color:', line):
                continue

            # Strip skills: field entirely (Gemini rejects unknown fields)
            if re.match(r'^skills:', line):
                continue

            # Start of allowed_tools: block
            if re.match(r'^allowed_tools:', line):
                in_allowed_tools = True
                continue

        new_fm_lines.append(line)

    # Build new tools: block as YAML array format
    tools_block_lines: list[str] = []
    if tool_names:
        tools_block_lines.append("tools:")
        for tool in tool_names:
            tools_block_lines.append(f"  - {tool}")

    # Insert tools block before other frontmatter fields
    final_fm_lines = tools_block_lines + new_fm_lines

    # Apply content transforms to body only (not frontmatter)
    body = _apply_body_transforms(body)

    # Reassemble the file
    new_frontmatter = "\n".join(final_fm_lines)
    return f"---\n{new_frontmatter}\n---\n{body}"


def _apply_body_transforms(body: str) -> str:
    """Apply all content transforms to an agent body or command content.

    Args:
        body: Content string (agent body or command body).

    Returns:
        Transformed content.
    """
    body = _escape_template_vars(body)
    body = _strip_sub_tags(body)
    body = _rewrite_paths(body)
    return body


def _convert_command_to_toml(content: str) -> str:
    """Convert Claude Code Markdown command to Gemini TOML format.

    Extracts description from YAML frontmatter, applies content transforms
    to the body, and outputs a two-field TOML file with description and prompt.

    Args:
        content: Full command file content (frontmatter + body).

    Returns:
        TOML-formatted string with description and prompt fields.
    """
    # Apply content transforms to the entire content first
    content = _rewrite_paths(content)
    content = _strip_sub_tags(content)
    content = _escape_template_vars(content)

    if not content.startswith("---"):
        return f"prompt = {json.dumps(content)}\n"

    # Extract frontmatter
    rest = content[3:]
    close_idx = re.search(r'\n---(\n|$)', rest)
    if not close_idx:
        return f"prompt = {json.dumps(content)}\n"

    frontmatter = rest[:close_idx.start()]
    body = rest[close_idx.end():].strip()

    # Extract description from frontmatter
    description = ""
    for line in frontmatter.splitlines():
        stripped = line.strip()
        if stripped.startswith("description:"):
            description = stripped[len("description:"):].strip().strip('"\'')
            break

    toml = ""
    if description:
        toml += f"description = {json.dumps(description)}\n"
    toml += f"prompt = {json.dumps(body)}\n"
    return toml


class GeminiInstaller(RuntimeInstaller):
    """Installs the Codebase Wizard plugin for Gemini CLI.

    Converts Claude Code plugin format to Gemini-native files:
    - Agent frontmatter: allowed_tools -> tools YAML array, color stripped, name kept
    - Commands: converted to TOML format (.toml extension) with description + prompt
    - Skills: copied verbatim (runtime-agnostic)

    Supports global install (~/.gemini/) and per-project install (./.gemini/).
    Both are idempotent -- calling install twice updates in place.
    """

    def _resolve_dest(self, target: str) -> Path:
        """Resolve the install destination based on target scope.

        Args:
            target: "global" or "project".

        Returns:
            Absolute path to the codebase-wizard install directory.
        """
        if target == "global":
            config_dir = os.environ.get("GEMINI_CONFIG_DIR")
            if config_dir:
                return Path(config_dir).expanduser() / "codebase-wizard"
            return Path.home() / ".gemini" / "codebase-wizard"
        return Path.cwd() / ".gemini" / "codebase-wizard"

    def install(self, source: Path, target: str = "global") -> None:
        """Convert and install the plugin to the Gemini configuration directory.

        Converts agent frontmatter, converts commands to TOML, copies skills
        verbatim, and copies .claude-plugin metadata.

        Args:
            source: Path to the bundled plugin directory (contains agents/, commands/, skills/).
            target: "global" -> ~/.gemini/codebase-wizard/
                    "project" -> ./.gemini/codebase-wizard/

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
                (agents_dst / agent_file.name).write_text(content, encoding="utf-8")

            # Convert commands to TOML format
            commands_src = source / "commands"
            command_dst = destination / "command"
            command_dst.mkdir(parents=True, exist_ok=True)
            for cmd_file in commands_src.glob("*.md"):
                content = cmd_file.read_text(encoding="utf-8")
                toml_content = _convert_command_to_toml(content)
                toml_name = cmd_file.stem + ".toml"
                (command_dst / toml_name).write_text(toml_content, encoding="utf-8")

            # Copy skills verbatim (runtime-agnostic)
            skills_src = source / "skills"
            if skills_src.exists():
                shutil.copytree(skills_src, destination / "skill")

            # Copy .claude-plugin directory (for version reading)
            claude_plugin_src = source / ".claude-plugin"
            if claude_plugin_src.exists():
                shutil.copytree(claude_plugin_src, destination / ".claude-plugin")

        except OSError as e:
            raise RuntimeError(f"Failed to install to {destination}: {e}") from e

    def uninstall(self, target: str = "global") -> None:
        """Remove the installed plugin directory.

        Args:
            target: "global" or "project" -- same scope as install().

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
        # Check global (with env var override)
        config_dir = os.environ.get("GEMINI_CONFIG_DIR")
        if config_dir:
            global_dest = Path(config_dir).expanduser() / "codebase-wizard"
        else:
            global_dest = Path.home() / ".gemini" / "codebase-wizard"

        if global_dest.exists():
            return {
                "installed": True,
                "location": str(global_dest),
                "version": _read_version(global_dest),
            }

        project_dest = Path.cwd() / ".gemini" / "codebase-wizard"
        if project_dest.exists():
            return {
                "installed": True,
                "location": str(project_dest),
                "version": _read_version(project_dest),
            }

        return {"installed": False, "location": None, "version": None}
