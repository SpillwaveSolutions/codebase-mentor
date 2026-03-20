---
# No context: fork — setup runs in the main context intentionally.
# Reason: setup needs to write settings.local.json and install Agent Rulez,
# which requires permissions outside the scoped codebase-wizard-agent.
# This command runs ONCE during onboarding. It is not used in regular sessions.
---

# /codebase-wizard-setup

One-time onboarding command. Installs the Codebase Wizard infrastructure:
Agent Rulez hooks, storage directory, and scoped write permissions.

**Run this once before your first /codebase-wizard session.**
Do not run again unless you need to re-initialize (e.g., after moving storage).

## Steps

Run `plugin/setup/setup.sh`, which performs these steps in order:

1. **Resolve storage** — ask user to choose `.code-wizard/` or `.claude/code-wizard/`,
   then create the chosen directory with `sessions/` and `docs/` subdirectories.

2. **Write config.json** — save `resolved_storage` path to
   `{resolved_storage}/config.json` so all other commands can find it.

3. **Install Agent Rulez** — run `rulez install` to ensure the hook runner
   is available for automatic session capture.

4. **Deploy hook config** — copy `plugin/setup/agent-rulez-sample.yaml`
   to `{resolved_storage}/agent-rulez.yaml`, substituting `{resolved_storage}`
   with the actual path resolved in Step 1.

5. **Register hook** — run `rulez hook add --config {resolved_storage}/agent-rulez.yaml`
   so PostToolUse and Stop events are captured during wizard sessions.

6. **Write settings.local.json** — write scoped write permissions so the wizard
   can save sessions and docs without approval prompts during sessions.

## What Gets Written

- `{resolved_storage}/config.json` — storage path record
- `{resolved_storage}/agent-rulez.yaml` — deployed hook config
- `settings.local.json` — scoped permissions for wizard storage dirs

## After Setup

Run `/codebase-wizard` to start your first session.
Sessions are automatically captured to `{resolved_storage}/sessions/`.
After any session, run `/codebase-wizard-export` to generate docs.
