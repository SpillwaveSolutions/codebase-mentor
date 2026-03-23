---
description: "One-time setup: install Agent Rulez hooks and write session-agent permissions."
context: fork
agent: codebase-wizard-setup-agent
---

# /codebase-wizard-setup

One-time onboarding command. Forks into `codebase-wizard-setup-agent`, which
has the scoped permissions needed to write `settings.local.json` and run
Agent Rulez install — without touching anything outside the wizard's own files.

**Run this once before your first /codebase-wizard session.**

All setup behavior is governed by the `configuring-codebase-wizard` skill.
This command is the entry point only.
