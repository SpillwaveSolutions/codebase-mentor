# Codebase Wizard — Plan 2: Capture + Synthesis

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the capture + synthesis pipeline — auto-capture Q&A to raw JSON via Agent Rulez hooks, plus the `/codebase-wizard-export` command that synthesizes raw sessions into SESSION-TRANSCRIPT.md, CODEBASE.md, TOUR.md, or FILE-NOTES.md.

**Architecture:** Four new files added to the plugin. The `agent-rulez-sample.yaml` is a template deployed by `setup.sh`, which resolves storage, installs Agent Rulez, substitutes the path, registers the hook, and writes `settings.local.json`. The export command synthesizes raw session JSON into structured docs. The setup command runs once during onboarding without `context: fork` so it has permission to write `settings.local.json` and install Agent Rulez.

**Tech Stack:** YAML hook config, bash script, markdown command files, Claude Code skill conventions

**Spec:** `docs/superpowers/specs/2026-03-19-codebase-wizard-design.md` (Sections 3 and 5)

**Scope note — deferred to later plans:**
- `plugin/agents/codebase-wizard-agent.md` → Plan 3 (Permission Agents)
- `plugin/commands/codebase-wizard.md` → Plan 3 (Commands)
- Multi-platform support (OpenCode, Gemini, Codex) → Plan 4 (Multi-Platform)

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Create | `plugin/setup/agent-rulez-sample.yaml` | PostToolUse + Stop hook config template; `{resolved_storage}` placeholder substituted by setup.sh |
| Create | `plugin/setup/setup.sh` | Storage resolution, Agent Rulez install, hook registration, settings.local.json writer |
| Create | `plugin/commands/codebase-wizard-export.md` | `/export` command — reads config.json, reads session JSON, synthesizes output docs |
| Create | `plugin/commands/codebase-wizard-setup.md` | `/setup` command — runs setup.sh; no `context: fork`; one-time onboarding |

---

## Task 1: Write agent-rulez-sample.yaml

The hook config template. `setup.sh` substitutes `{resolved_storage}` with the actual path when deploying. The sample itself lives in `plugin/setup/` and is never deployed directly.

**Files:**
- Create: `plugin/setup/agent-rulez-sample.yaml`

- [ ] **Step 1: Define verification criteria before writing**

```bash
cat > /tmp/agent-rulez-criteria.txt << 'EOF'
CHECK-1: PostToolUse hook appends to sessions/{date}-{repo}.json
CHECK-2: {date} and {repo} documented as Agent Rulez native interpolation variables
CHECK-3: on_error: warn present on PostToolUse hook
CHECK-4: Stop hook sends notify action with export reminder message
CHECK-5: {resolved_storage} placeholder (not a real path) in target field
CHECK-6: Header comment explains file is a template and is deployed by setup.sh
EOF
```

- [ ] **Step 2: Create plugin/setup/agent-rulez-sample.yaml**

Create `plugin/setup/agent-rulez-sample.yaml`:

```yaml
# agent-rulez-sample.yaml
# TEMPLATE — do not deploy directly.
# Deployed to: {resolved_storage}/agent-rulez.yaml by /codebase-wizard-setup
# setup.sh substitutes {resolved_storage} with the actual resolved storage path.
#
# Variable reference (Agent Rulez native interpolation):
#   {date} → YYYY-MM-DD at hook invocation time
#   {repo} → basename of the current working directory
#
# If Agent Rulez does not support {date}/{repo} natively, setup.sh
# pre-computes them and writes static values into the deployed YAML.

hooks:
  - event: PostToolUse
    action: append
    target: "{resolved_storage}/sessions/{date}-{repo}.json"
    format: json
    on_error: warn
    # on_error: warn — capture failures notify the user but do not abort
    # the session. The wizard maintains an in-memory buffer and offers to
    # flush it at session end if hooks failed.

  - event: Stop
    action: notify
    message: "Session ended. Run /codebase-wizard-export to generate docs."
```

- [ ] **Step 3: Verify agent-rulez-sample.yaml against criteria**

```bash
cat /tmp/agent-rulez-criteria.txt
```

Check each criterion manually:
- [ ] CHECK-1: PostToolUse target = `sessions/{date}-{repo}.json` ✓
- [ ] CHECK-2: `{date}` and `{repo}` documented in comments ✓
- [ ] CHECK-3: `on_error: warn` present ✓
- [ ] CHECK-4: Stop hook action is `notify` with export message ✓
- [ ] CHECK-5: `{resolved_storage}` placeholder in target (not a real path) ✓
- [ ] CHECK-6: Header comment explains template nature ✓

- [ ] **Step 4: Commit**

```bash
git add plugin/setup/agent-rulez-sample.yaml
git commit -m "feat: add agent-rulez-sample.yaml hook config template"
```

---

## Task 2: Write setup.sh

The one-time installer. Resolves storage, installs Agent Rulez, deploys the hook config with substituted path, registers the hook, and writes `settings.local.json` with scoped write permissions.

**Files:**
- Create: `plugin/setup/setup.sh`

- [ ] **Step 1: Define verification criteria before writing**

```bash
cat > /tmp/setup-criteria.txt << 'EOF'
CHECK-1: Storage resolution checks .code-wizard/ first, then .claude/code-wizard/
CHECK-2: If neither exists, asks user once then creates chosen directory
CHECK-3: Writes config.json with version, resolved_storage, and created timestamp
CHECK-4: Runs "rulez install" to install Agent Rulez
CHECK-5: Copies agent-rulez-sample.yaml → {resolved_storage}/agent-rulez.yaml
          with {resolved_storage} substituted to the actual path
CHECK-6: Registers hook: rulez hook add --config {resolved_storage}/agent-rulez.yaml
CHECK-7: Writes settings.local.json with scoped Write permissions
CHECK-8: Script is executable (chmod +x applied)
EOF
```

- [ ] **Step 2: Create plugin/setup/setup.sh**

Create `plugin/setup/setup.sh`:

```bash
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
```

- [ ] **Step 3: Make setup.sh executable**

```bash
chmod +x plugin/setup/setup.sh
```

- [ ] **Step 4: Verify setup.sh against criteria**

```bash
cat /tmp/setup-criteria.txt
```

Check each criterion manually:
- [ ] CHECK-1: Storage resolution checks `.code-wizard/` first ✓
- [ ] CHECK-2: Prompts user if neither directory exists, creates chosen dir ✓
- [ ] CHECK-3: Writes `config.json` with `version`, `resolved_storage`, `created` ✓
- [ ] CHECK-4: `rulez install` call present ✓
- [ ] CHECK-5: `sed` substitutes `{resolved_storage}` in deployed YAML ✓
- [ ] CHECK-6: `rulez hook add --config` registration present ✓
- [ ] CHECK-7: `settings.local.json` written with scoped Write permissions ✓
- [ ] CHECK-8: `chmod +x` applied ✓

- [ ] **Step 5: Commit**

```bash
git add plugin/setup/setup.sh
git commit -m "feat: add setup.sh — storage resolution, Agent Rulez install, hook registration"
```

---

## Task 3: Write /codebase-wizard-export Command

The export command reads `config.json` to find `resolved_storage`, reads one or more raw session JSON files, and synthesizes structured output documents.

**Files:**
- Create: `plugin/commands/codebase-wizard-export.md`

- [ ] **Step 1: Define verification criteria before writing**

```bash
cat > /tmp/export-criteria.txt << 'EOF'
CHECK-1: context: fork and agent: codebase-wizard-agent in frontmatter
CHECK-2: Reads config.json to find resolved_storage (not hardcoded)
CHECK-3: --latest selects most recent file in sessions/
CHECK-4: --session <filename> selects a specific session file
CHECK-5: --all processes every session file independently (no merging)
CHECK-6: Output always goes to {resolved_storage}/docs/{session_id}/
CHECK-7: SESSION-TRANSCRIPT.md always generated for every mode
CHECK-8: CODEBASE.md generated for describe mode sessions
CHECK-9: TOUR.md generated for explore mode sessions
CHECK-10: FILE-NOTES.md generated for file mode sessions
CHECK-11: Synthesis logic: each turn → question + anchor + code block + explanation
EOF
```

- [ ] **Step 2: Create plugin/commands/codebase-wizard-export.md**

Create `plugin/commands/codebase-wizard-export.md`:

```markdown
---
context: fork
agent: codebase-wizard-agent
---

# /codebase-wizard-export

Synthesizes one or more raw session JSON files into structured documentation.

## Args

`--latest` (default) | `--session <filename>` | `--all`

- `--latest` — synthesize the most recent session file in `{resolved_storage}/sessions/`
- `--session <filename>` — synthesize a specific session file by name
- `--all` — synthesize every session file independently; each gets its own output directory

## Step 1 — Read config.json

Find config.json by checking both storage locations in order:
1. `.code-wizard/config.json`
2. `.claude/code-wizard/config.json`

Read `resolved_storage` from the config. If neither file exists, tell the user:
> "No wizard storage found. Run /codebase-wizard-setup first."

## Step 2 — Select Session File(s)

- `--latest`: list files in `{resolved_storage}/sessions/`, sort by name (ISO date prefix),
  take the most recent.
- `--session <filename>`: read `{resolved_storage}/sessions/<filename>` directly.
- `--all`: collect all `.json` files in `{resolved_storage}/sessions/`.

If no session files exist:
> "No sessions found in {resolved_storage}/sessions/. Run /codebase-wizard to
>  start a session first."

## Step 3 — Read and Validate Session JSON

For each selected session file, read and parse the JSON. Expected schema:

```json
{
  "version": 1,
  "session_id": "YYYY-MM-DD-{repo}",
  "repo": "...",
  "artifact": "...",
  "mode": "describe | explore | file",
  "created": "...",
  "turns": [
    {
      "ts": "...",
      "question": "...",
      "anchor": "...",
      "code_shown": "...",
      "explanation": "...",
      "connections": { "calls": [], "called_by": [] },
      "next_options": []
    }
  ]
}
```

If `version` field is missing or higher than 1, warn:
> "Session file uses an unrecognized version. Attempting synthesis anyway — some
>  fields may be missing."

## Step 4 — Synthesize Output Documents

Output directory: `{resolved_storage}/docs/{session_id}/`

Create the directory if it does not exist.

### SESSION-TRANSCRIPT.md (always generated — every mode)

Format each turn as:

```markdown
## Q: {question}

*{ts}*

// {anchor}
```{code_shown}```

{explanation}

→ calls:     {connections.calls joined with newlines}
→ called by: {connections.called_by joined with newlines}

**Next options explored:**
- {next_options[0]}
- {next_options[1]}
- {next_options[2]}

---
```

Omit connections block if both `calls` and `called_by` are empty arrays.
Omit next options block if `next_options` is empty.

### CODEBASE.md (describe mode sessions: `mode == "describe"`)

```markdown
# Codebase: {repo}

## Overview
[Synthesize from early turns: what it does, who uses it, tech stack]

## Entry Points
[Extract from turns covering entry point questions]

## Auth
[Extract from turns covering auth questions. Include code block with anchor.]

## Data Layer
[Extract from turns covering data/ORM questions]

## Key Concepts
[Extract domain term definitions from Q5-style turns]

## Traced Call Chains
[Extract traced call sequences with anchors]

## Constraints
[Extract from turns covering off-limits areas, fragile code, dead code]

## Open Questions
[Collect any `next_options` not followed up on, or questions marked unresolved]
```

### TOUR.md (explore mode sessions: `mode == "explore"`)

Format as a re-readable learning guide:

```markdown
# Tour: {repo}

*Generated from explore session on {created}*

## What the App Does
[Extract from Step 1 turn]

## Entry Point
[Extract from Step 2 turn with anchor]

## Auth Flow
[Extract from Step 3 turn with anchor]

## Data Flow
[Extract from Step 4 turn with anchor]

## Where to Start
[Extract from Step 5 turn with anchor]

## Q&A Detours
[Any off-topic turns answered during the tour]
```

### FILE-NOTES.md (file mode sessions: `mode == "file"`)

```markdown
# File Notes: {artifact}

*Generated from file session on {created}*

[For each turn, in order:]
## {question}

// {anchor}
```{code_shown}```

{explanation}

[Follow-up Q&A captured under this section if any]

---
```

## Step 5 — Report Completion

After writing all files:
> "Export complete. Files written to {resolved_storage}/docs/{session_id}/:"
> - SESSION-TRANSCRIPT.md
> - CODEBASE.md (if describe mode)
> - TOUR.md (if explore mode)
> - FILE-NOTES.md (if file mode)
```

- [ ] **Step 3: Verify export command against criteria**

```bash
cat /tmp/export-criteria.txt
```

Check each criterion manually:
- [ ] CHECK-1: `context: fork` and `agent: codebase-wizard-agent` in frontmatter ✓
- [ ] CHECK-2: Reads `config.json` to find `resolved_storage` ✓
- [ ] CHECK-3: `--latest` selects most recent file by ISO date sort ✓
- [ ] CHECK-4: `--session <filename>` selects specific file ✓
- [ ] CHECK-5: `--all` processes each file independently with its own output dir ✓
- [ ] CHECK-6: Output path = `{resolved_storage}/docs/{session_id}/` ✓
- [ ] CHECK-7: SESSION-TRANSCRIPT.md generated for every mode ✓
- [ ] CHECK-8: CODEBASE.md for describe mode ✓
- [ ] CHECK-9: TOUR.md for explore mode ✓
- [ ] CHECK-10: FILE-NOTES.md for file mode ✓
- [ ] CHECK-11: Turn synthesis loop formats question + anchor + code block + explanation ✓

- [ ] **Step 4: Commit**

```bash
git add plugin/commands/codebase-wizard-export.md
git commit -m "feat: add /codebase-wizard-export command with session synthesis"
```

---

## Task 4: Write /codebase-wizard-setup Command

The one-time onboarding command. Runs `setup.sh` from main context (no `context: fork`) because it needs broader permissions to write `settings.local.json` and install Agent Rulez.

**Files:**
- Create: `plugin/commands/codebase-wizard-setup.md`

- [ ] **Step 1: Define verification criteria before writing**

```bash
cat > /tmp/setup-cmd-criteria.txt << 'EOF'
CHECK-1: NO context: fork in frontmatter (main context intentional)
CHECK-2: Comment in frontmatter explains why no context: fork
CHECK-3: Runs setup/setup.sh
CHECK-4: Documents 6-step flow matching spec Section 5
CHECK-5: Documents one-time use — not for regular sessions
CHECK-6: No agent: field (runs in main context with full permissions)
EOF
```

- [ ] **Step 2: Create plugin/commands/codebase-wizard-setup.md**

Create `plugin/commands/codebase-wizard-setup.md`:

```markdown
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
```

- [ ] **Step 3: Verify setup command against criteria**

```bash
cat /tmp/setup-cmd-criteria.txt
```

Check each criterion manually:
- [ ] CHECK-1: No `context: fork` in frontmatter ✓
- [ ] CHECK-2: Comment explains why no `context: fork` ✓
- [ ] CHECK-3: References `plugin/setup/setup.sh` ✓
- [ ] CHECK-4: All 6 steps listed matching spec Section 5 ✓
- [ ] CHECK-5: "Run this once" / "one-time" language present ✓
- [ ] CHECK-6: No `agent:` field in frontmatter ✓

- [ ] **Step 4: Commit**

```bash
git add plugin/commands/codebase-wizard-setup.md
git commit -m "feat: add /codebase-wizard-setup command — one-time onboarding"
```

---

## Task 5: End-to-End Verification

**Files:**
- No new files — verification only

- [ ] **Step 1: Verify agent-rulez-sample.yaml has PostToolUse + Stop hooks**

```bash
grep -n "event:" plugin/setup/agent-rulez-sample.yaml
```

Expected output:
```
  - event: PostToolUse
  - event: Stop
```

Both events must be present. If either is missing, the hook pipeline is incomplete.

- [ ] **Step 2: Verify setup.sh has all 5 operational steps**

```bash
grep -n "rulez\|config.json\|sed\|settings.local" plugin/setup/setup.sh
```

Expected hits:
- `config.json` write (Step 2)
- `rulez install` (Step 3)
- `sed` substitution into deployed YAML (Step 4)
- `rulez hook add` (Step 5)
- `settings.local.json` write (Step 6)

- [ ] **Step 3: Verify export command handles all 3 args and reads config.json**

```bash
grep -n "latest\|session\|--all\|config.json\|resolved_storage" plugin/commands/codebase-wizard-export.md | head -20
```

Expected: hits for all three arg modes and `config.json` / `resolved_storage`.

- [ ] **Step 4: Verify setup command has no context:fork**

```bash
grep -n "context" plugin/commands/codebase-wizard-setup.md
```

Expected: zero matches for `context: fork`. If `context: fork` appears, remove it — the setup command must run in main context.

- [ ] **Step 5: Verify SESSION-TRANSCRIPT.md referenced in export for all modes**

```bash
grep -n "SESSION-TRANSCRIPT" plugin/commands/codebase-wizard-export.md
```

Expected: at least one hit confirming it is always generated.

- [ ] **Step 6: Verify {resolved_storage} used consistently (no bare {storage})**

```bash
grep -rn '"{storage}' plugin/setup/ plugin/commands/
```

Expected: zero hits. All paths use `{resolved_storage}`.

---

## Plan 2 Completion Checklist

- [ ] `plugin/setup/agent-rulez-sample.yaml` exists with PostToolUse + Stop hooks
- [ ] `plugin/setup/setup.sh` exists and is executable (`chmod +x` applied)
- [ ] `plugin/setup/setup.sh` has all 5 operational steps: resolve → install → copy+substitute → register → settings.local.json
- [ ] `plugin/commands/codebase-wizard-export.md` handles `--latest`, `--session`, and `--all`
- [ ] `plugin/commands/codebase-wizard-export.md` reads `config.json` for `resolved_storage`
- [ ] `plugin/commands/codebase-wizard-export.md` generates SESSION-TRANSCRIPT.md for every mode
- [ ] `plugin/commands/codebase-wizard-setup.md` has no `context: fork`
- [ ] `plugin/commands/codebase-wizard-setup.md` documents all 6 setup steps

**Next:** Plan 3 — Permission Agents + Commands (`codebase-wizard-agent.md`, `codebase-wizard.md`, multi-platform stub)
