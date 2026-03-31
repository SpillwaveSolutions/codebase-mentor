"""Gemini CLI runtime installer for ai-codebase-mentor.

Installs the Codebase Wizard plugin to Gemini CLI configuration directories:
  Global:  ~/.gemini/codebase-wizard/
  Project: ./.gemini/codebase-wizard/

Agent frontmatter is converted from Claude Code format (allowed_tools: array)
to Gemini format (tools: YAML array with snake_case names). Command files are
converted from Markdown+YAML to TOML format (.toml extension).
"""

from .base import RuntimeInstaller


GEMINI_TOOL_MAP = {}


def _convert_gemini_tool_name(tool):
    raise NotImplementedError


class GeminiInstaller(RuntimeInstaller):
    def _resolve_dest(self, target):
        raise NotImplementedError

    def install(self, source, target="global"):
        raise NotImplementedError

    def uninstall(self, target="global"):
        raise NotImplementedError

    def status(self):
        raise NotImplementedError
