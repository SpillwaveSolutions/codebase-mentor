#!/usr/bin/env bash
# setup.sh — Codebase Wizard one-time setup
# Run via /codebase-wizard-setup. Do not run manually unless debugging.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_YAML="$SCRIPT_DIR/agent-rulez-sample.yaml"

# ─────────────────────────────────────────────
# Step 1: Resolve storage
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# Step 2: Write config.json
# ─────────────────────────────────────────────
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

# ─────────────────────────────────────────────
# Step 3: Install Agent Rulez
# ─────────────────────────────────────────────
echo "Installing Agent Rulez..."
rulez install

# ─────────────────────────────────────────────
# Step 4: Deploy agent-rulez.yaml with substituted path
# ─────────────────────────────────────────────
DEPLOYED_YAML="$RESOLVED_STORAGE/agent-rulez.yaml"
sed "s|{resolved_storage}|$RESOLVED_STORAGE|g" "$SAMPLE_YAML" > "$DEPLOYED_YAML"
echo "Deployed hook config: $DEPLOYED_YAML"

# ─────────────────────────────────────────────
# Step 5: Register hook with Agent Rulez
# ─────────────────────────────────────────────
rulez hook add --config "$DEPLOYED_YAML"
echo "Registered Agent Rulez hooks from $DEPLOYED_YAML"

# ─────────────────────────────────────────────
# Step 6: Write settings.local.json
# ─────────────────────────────────────────────
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
