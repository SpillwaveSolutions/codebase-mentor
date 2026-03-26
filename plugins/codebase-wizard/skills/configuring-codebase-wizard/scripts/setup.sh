#!/usr/bin/env bash
# setup.sh — Codebase Wizard one-time setup
# Run via /codebase-wizard-setup. Do not run manually unless debugging.
# Usage: ./setup.sh [claude|opencode|gemini|codex|all]
#   Default runtime is "claude" if no argument is provided.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_YAML="$SCRIPT_DIR/agent-rulez-sample.yaml"

RUNTIME="${1:-claude}"

# ─────────────────────────────────────────────
# Shared: Resolve storage
# Called by all install functions that need wizard storage.
# ─────────────────────────────────────────────
resolve_storage() {
  if [ -d ".code-wizard" ]; then
    RESOLVED_STORAGE=".code-wizard"
  elif [ -d ".claude/code-wizard" ]; then
    RESOLVED_STORAGE=".claude/code-wizard"
  else
    echo "No wizard storage directory found."
    echo "Where should Codebase Wizard store sessions and docs?"
    echo "  1) .code-wizard/           (recommended)"
    echo "  2) .claude/code-wizard/"
    read -r -p "Choice [1/2]: " choice
    case "$choice" in
      2) RESOLVED_STORAGE=".claude/code-wizard" ;;
      *) RESOLVED_STORAGE=".code-wizard" ;;
    esac
    mkdir -p "$RESOLVED_STORAGE/sessions" "$RESOLVED_STORAGE/docs"
  fi

  echo "Using storage: $RESOLVED_STORAGE"
}

# ─────────────────────────────────────────────
# Shared: Write config.json
# ─────────────────────────────────────────────
write_config() {
  CONFIG_FILE="$RESOLVED_STORAGE/config.json"
  CREATED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  cat > "$CONFIG_FILE" << EOF
{
  "version": 1,
  "resolved_storage": "$RESOLVED_STORAGE",
  "created": "$CREATED_AT"
}
EOF

  echo "Wrote $CONFIG_FILE"
}

# ─────────────────────────────────────────────
# Shared: Deploy Agent Rulez hooks
# Used by claude, opencode, and gemini installs.
# $1 = runtime: "claude" | "opencode" | "gemini" (default: claude)
# ─────────────────────────────────────────────
deploy_hooks() {
  local runtime="${1:-claude}"
  echo "Installing Agent Rulez security rules and session capture..."

  # Deploy the rules YAML (security enforcement + session capture)
  DEPLOYED_YAML="$RESOLVED_STORAGE/agent-rulez.yaml"
  cp "$SAMPLE_YAML" "$DEPLOYED_YAML"
  echo "Deployed rules config: $DEPLOYED_YAML"

  # Deploy capture-session.sh to .code-wizard/scripts/
  CAPTURE_SCRIPT="$SCRIPT_DIR/capture-session.sh"
  mkdir -p "$RESOLVED_STORAGE/scripts"
  cp "$CAPTURE_SCRIPT" "$RESOLVED_STORAGE/scripts/capture-session.sh"
  chmod +x "$RESOLVED_STORAGE/scripts/capture-session.sh"
  echo "Deployed capture script: $RESOLVED_STORAGE/scripts/capture-session.sh"

  # Copy rules to .claude/hooks.yaml — this is where rulez reads rules at hook-fire time
  mkdir -p .claude
  cp "$DEPLOYED_YAML" .claude/hooks.yaml
  echo "Wrote rules to .claude/hooks.yaml"

  # Register rulez hook in the runtime's settings file
  case "$runtime" in
    opencode)
      rulez opencode install
      echo "Agent Rulez installed for OpenCode — security rules and session capture active"
      ;;
    *)
      rulez install
      echo "Agent Rulez installed — security rules and session capture active"
      ;;
  esac
}

# ─────────────────────────────────────────────
# install_claude — Claude Code (default)
# ─────────────────────────────────────────────
install_claude() {
  echo "Installing for Claude Code..."

  resolve_storage
  write_config
  deploy_hooks

  cat > settings.local.json << EOF
{
  "permissions": {
    "allow": [
      "Bash(rulez*)",
      "Bash(node .claude/plugins/codebase-wizard/**)",
      "Write(.code-wizard/**)",
      "Write(.claude/code-wizard/**)"
    ]
  }
}
EOF

  echo "Wrote settings.local.json with scoped permissions"
  echo ""
  echo "Setup complete. Run /codebase-wizard to start your first session."
}

# ─────────────────────────────────────────────
# install_opencode — OpenCode
# OpenCode uses lowercase tool names and flat command names.
# Tool names differ from Claude Code PascalCase — see references/codex-tools.md.
# ─────────────────────────────────────────────
install_opencode() {
  echo "Installing for OpenCode..."

  resolve_storage
  write_config
  deploy_hooks opencode

  echo ""
  echo "OpenCode setup complete."
  echo "Tool names use lowercase conventions (read, write, bash, grep, glob)."
  echo "See plugin/references/codex-tools.md for the full name mapping."
  echo "Run /codebase-wizard to start your first session."
}

# ─────────────────────────────────────────────
# install_gemini — Gemini CLI
# Gemini uses snake_case tool names and TOML command format.
# Tool names differ from Claude Code PascalCase — see references/codex-tools.md.
# ─────────────────────────────────────────────
install_gemini() {
  echo "Installing for Gemini CLI..."

  resolve_storage
  write_config
  deploy_hooks

  echo ""
  echo "Gemini CLI setup complete."
  echo "Tool names use snake_case conventions (read_file, write_file, run_shell_command)."
  echo "See plugin/references/codex-tools.md for the full name mapping."
  echo "Commands are configured via TOML format in ~/.gemini/."
  echo "Run the codebase-wizard TOML command to start your first session."
}

# ─────────────────────────────────────────────
# install_codex — Codex
# Codex has no hook mechanism. Hook setup is intentionally skipped.
# Exit code 77 signals "skip" (not an error) for unsupported hook installation.
# Users must run /codebase-wizard-export manually after each session.
# ─────────────────────────────────────────────
install_codex() {
  echo "Installing for Codex..."

  resolve_storage
  write_config

  cat > AGENTS.md << EOF
# Codebase Wizard — Codex Instructions

The Codebase Wizard is installed and ready to use.

## Starting a session

Run one of the following commands to start a wizard session:

    /codebase-wizard --describe   # Document your codebase
    /codebase-wizard --explore    # Tour as a new developer
    /codebase-wizard --file <path>  # Explain a specific file

## IMPORTANT: Manual export required

Codex does not support automatic session capture hooks. After each session,
you must manually export your session to generate documentation:

    /codebase-wizard-export --latest

This generates SESSION-TRANSCRIPT.md and the mode-specific doc
(CODEBASE.md, TOUR.md, or FILE-NOTES.md) in:

    ${RESOLVED_STORAGE}/docs/{session_id}/

Without running this command, your session content will not be saved to disk.

## Tool name mapping

Codex uses different tool names than Claude Code. See:
    plugin/references/codex-tools.md
EOF

  echo "Wrote AGENTS.md with Codex-specific instructions"
  echo ""
  echo "NOTE: Codex does not support hooks. Skipping Agent Rulez hook installation."
  echo "Users must run /codebase-wizard-export manually after each session."
  echo ""
  echo "Codex setup complete (hook installation skipped — exit 77)."
  exit 77
}

# ─────────────────────────────────────────────
# install_all — All platforms
# Runs claude, opencode, and gemini installs.
# Catches exit 77 from codex (skip signal) without failing the overall install.
# ─────────────────────────────────────────────
install_all() {
  echo "Installing for all platforms..."
  echo ""

  install_claude
  echo ""

  install_opencode
  echo ""

  install_gemini
  echo ""

  # Codex exits with code 77 (skip — no hook support).
  # Catch it here so install_all does not fail overall.
  install_codex || {
    exit_code=$?
    if [ "$exit_code" -eq 77 ]; then
      echo "Codex: hook installation skipped (exit 77 — no hook support). Continuing."
    else
      echo "Codex install failed with exit code $exit_code. Aborting."
      exit "$exit_code"
    fi
  }

  echo ""
  echo "All platforms installed successfully."
}

# ─────────────────────────────────────────────
# Platform dispatch
# ─────────────────────────────────────────────
case "$RUNTIME" in
  claude)   install_claude   ;;
  opencode) install_opencode ;;
  gemini)   install_gemini   ;;
  codex)    install_codex    ;;
  all)      install_all      ;;
  *)
    echo "Unknown runtime: $RUNTIME"
    echo "Usage: ./setup.sh [claude|opencode|gemini|codex|all]"
    exit 1
    ;;
esac
