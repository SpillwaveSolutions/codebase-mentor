"""Static structural tests for the codebase-wizard plugin.

These tests verify that command files exist with correct frontmatter fields.
They do not make LLM API calls and run in the fast suite.

Why these tests exist:
  The integration tests (tests/integration/test_agent_rulez_e2e.py) use natural
  language prompts rather than /codebase-wizard and /codebase-wizard-export slash
  commands. This is because `context: fork` commands cannot be invoked in
  claude -p mode. These static tests fill that gap by verifying command file
  structure — that the commands are registered, have correct frontmatter, and
  reference the right agent.
"""

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent / "ai_codebase_mentor" / "plugin"


def _read_frontmatter_fields(md_path: Path) -> dict:
    """Extract YAML frontmatter fields from a markdown file.

    Returns a dict of key: value pairs from the --- block.
    Only handles simple scalar values (no nested YAML).
    """
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm_text = text[3:end].strip()
    fields = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields


class TestCommandFiles:
    """Verify command files exist and have required frontmatter fields."""

    def test_codebase_wizard_command_exists(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard.md"
        assert path.exists(), f"Command file missing: {path}"

    def test_codebase_wizard_has_description(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard.md"
        fm = _read_frontmatter_fields(path)
        assert "description" in fm, "codebase-wizard.md missing 'description' frontmatter"
        assert len(fm["description"]) > 10, "codebase-wizard.md description too short"

    def test_codebase_wizard_has_context_fork(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard.md"
        fm = _read_frontmatter_fields(path)
        assert fm.get("context") == "fork", (
            "codebase-wizard.md must have 'context: fork' to spawn codebase-wizard-agent.\n"
            f"Found: context={fm.get('context')!r}"
        )

    def test_codebase_wizard_has_agent(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard.md"
        fm = _read_frontmatter_fields(path)
        assert fm.get("agent") == "codebase-wizard-agent", (
            "codebase-wizard.md must reference 'agent: codebase-wizard-agent'.\n"
            f"Found: agent={fm.get('agent')!r}"
        )

    def test_codebase_wizard_export_command_exists(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard-export.md"
        assert path.exists(), f"Command file missing: {path}"

    def test_codebase_wizard_export_has_description(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard-export.md"
        fm = _read_frontmatter_fields(path)
        assert "description" in fm, "codebase-wizard-export.md missing 'description' frontmatter"

    def test_codebase_wizard_export_has_context_fork(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard-export.md"
        fm = _read_frontmatter_fields(path)
        assert fm.get("context") == "fork", (
            "codebase-wizard-export.md must have 'context: fork'.\n"
            f"Found: context={fm.get('context')!r}"
        )

    def test_codebase_wizard_setup_command_exists(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard-setup.md"
        assert path.exists(), f"Command file missing: {path}"

    def test_setup_command_has_description(self):
        path = PLUGIN_ROOT / "commands" / "codebase-wizard-setup.md"
        fm = _read_frontmatter_fields(path)
        assert "description" in fm, "codebase-wizard-setup.md missing 'description' frontmatter"


class TestSkillFiles:
    """Verify skill files exist with required frontmatter fields."""

    def test_explaining_codebase_skill_exists(self):
        path = PLUGIN_ROOT / "skills" / "explaining-codebase" / "SKILL.md"
        assert path.exists(), f"Skill file missing: {path}"

    def test_exporting_conversation_skill_exists(self):
        path = PLUGIN_ROOT / "skills" / "exporting-conversation" / "SKILL.md"
        assert path.exists(), f"Skill file missing: {path}"

    def test_configuring_codebase_wizard_skill_exists(self):
        path = PLUGIN_ROOT / "skills" / "configuring-codebase-wizard" / "SKILL.md"
        assert path.exists(), f"Skill file missing: {path}"

    def test_setup_sh_has_rulez_install(self):
        """setup.sh must call rulez install (not a stub or outdated command)."""
        setup_sh = (
            PLUGIN_ROOT / "skills" / "configuring-codebase-wizard"
            / "scripts" / "setup.sh"
        )
        assert setup_sh.exists(), f"setup.sh missing: {setup_sh}"
        content = setup_sh.read_text(encoding="utf-8")
        assert "rulez install" in content, (
            "setup.sh does not contain 'rulez install' — Agent Rulez hook registration missing"
        )
        assert "rulez opencode install" in content, (
            "setup.sh does not contain 'rulez opencode install' — OpenCode hook registration missing"
        )

    def test_setup_sh_copies_hooks_yaml(self):
        """setup.sh must copy deployed YAML to .claude/hooks.yaml before rulez install."""
        setup_sh = (
            PLUGIN_ROOT / "skills" / "configuring-codebase-wizard"
            / "scripts" / "setup.sh"
        )
        content = setup_sh.read_text(encoding="utf-8")
        assert ".claude/hooks.yaml" in content, (
            "setup.sh does not copy rules to .claude/hooks.yaml.\n"
            "rulez reads .claude/hooks.yaml at hook-fire time — it must be written by setup."
        )

    def test_capture_session_sh_exists(self):
        capture_sh = (
            PLUGIN_ROOT / "skills" / "configuring-codebase-wizard"
            / "scripts" / "capture-session.sh"
        )
        assert capture_sh.exists(), f"capture-session.sh missing: {capture_sh}"
