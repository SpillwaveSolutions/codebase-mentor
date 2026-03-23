---
name: configuring-codebase-wizard
description: >
  One-time setup for the Codebase Wizard. Use when the user runs
  /codebase-wizard-setup, says "set up the wizard", "install wizard", or
  "configure codebase wizard". Installs Agent Rulez hooks, creates storage
  directories, writes config.json, and sets scoped write permissions.
version: 1.0.0
---

# Configuring Codebase Wizard

One-time onboarding skill. Installs the Codebase Wizard infrastructure:
Agent Rulez hooks, storage directory, and scoped write permissions.

**Run this once before the first /codebase-wizard session.**

---

## Step 1 — Resolve Storage

Ask the user to choose a storage location:

> "Where should wizard sessions and docs be stored?"
> 1. `.code-wizard/` — top-level (visible in repo root)
> 2. `.claude/code-wizard/` — inside .claude/ (hidden from most tools)

Create the chosen directory with subdirectories:
```
{resolved_storage}/
  sessions/
  docs/
```

---

## Step 2 — Write config.json

Save the resolved storage path so all other commands can find it:

```json
{
  "resolved_storage": "{chosen_path}"
}
```

Write to `{resolved_storage}/config.json`.

---

## Step 3 — Install Agent Rulez

Run the setup script to install Agent Rulez and register the hook config:

```bash
bash scripts/setup.sh {runtime}
```

Where `{runtime}` is `claude` (default), `opencode`, `gemini`, `codex`, or `all`.

The script handles:
- Running `rulez install` to ensure the hook runner is available
- Deploying `scripts/agent-rulez-sample.yaml` to `{resolved_storage}/agent-rulez.yaml`
  with `{resolved_storage}` substituted with the actual path
- Running `rulez hook add --config {resolved_storage}/agent-rulez.yaml`
- Writing `settings.local.json` with scoped permissions for wizard storage dirs

If runtime is `codex`: prints manual export instructions and exits 77 (no hook
installation attempted — Codex does not support hooks).

---

## Step 4 — Confirm Setup

After the script completes:

> "Wizard configured. Storage at {resolved_storage}. Hooks registered."
> "Run /codebase-wizard to start your first session."
> "After any session, run /codebase-wizard-export to generate docs."

---

## What Gets Written

| File | Purpose |
|------|---------|
| `{resolved_storage}/config.json` | Storage path record for all wizard commands |
| `{resolved_storage}/agent-rulez.yaml` | Deployed hook config for session capture |
| `.claude/settings.local.json` | Scoped write permissions for wizard storage dirs |

---

## Script Reference

`scripts/setup.sh` — platform-aware install script.

Usage: `bash scripts/setup.sh [claude|opencode|gemini|codex|all]`

- Default: `claude`
- `all`: installs for claude, opencode, and gemini; skips codex (exit 77 caught)
- `codex`: prints manual export notice and exits 77 (not an error)
