---
created: 2026-03-23T21:58:27.953Z
title: Fix Agent Rulez config and add session capture hook
area: general
files:
  - plugin/setup/agent-rulez-sample.yaml
  - plugin/setup/setup.sh
  - plugin/SKILL.md
---

## Confirmed Findings

First-run testing of codebase-wizard on the book_generator project confirmed four root causes.
These are facts, not guesses. No further investigation needed before implementing the fixes.

1. **`agent-rulez-sample.yaml` uses the wrong schema.** The file uses a `hooks:` top-level key —
   the correct top-level key is `rules:`. The actions `action: append` and `action: notify` do not
   exist in Agent Rulez. Valid actions are `block`, `inject`, and `run`. The file must be rewritten
   from scratch using the correct schema (see Corrected Solution below).

2. **`rulez hook add --config` does not exist.** Running `rulez --help` on the installed CLI shows
   these subcommands: `init`, `install`, `uninstall`, `debug`, `repl`, `validate`, `logs`,
   `explain`. There is no `hook` subcommand. Any reference to `rulez hook add` in `setup.sh` or
   `SKILL.md` will fail with "unrecognized subcommand 'hook'". The correct install command is
   `rulez install`, which reads `.claude/hooks.yaml`.

3. **Agent Rulez CAN capture JSON via the `run:` action.** Confirmed via `rulez debug`: every
   PostToolUse event passes full event JSON (`hook_event_name`, `tool_name`, `tool_input`,
   `session_id`, `timestamp`) via stdin to the script. A `run:` rule with a shell script that
   reads stdin and appends to a JSON file IS the correct session capture mechanism in Agent Rulez.
   The earlier assessment ("cannot capture JSON") was wrong — Agent Rulez was designed for this.

4. **Session capture via Agent Rulez `run:` script OR wizard Write tool — both are valid.**
   Option A: Agent Rulez `run:` rule with a capture script (`capture-session.sh`) that reads
   PostToolUse events from stdin and appends to `.code-wizard/sessions/{session_id}.json`.
   Option B (simpler): Wizard skill calls Write tool after each answer turn. No hook infrastructure
   needed; runs inside the conversation context.
   **Recommended**: Agent Rulez approach (Option A) for full capture including tool calls Claude
   makes during exploration; Write tool approach (Option B) as a fallback if Agent Rulez isn't
   installed.

## Corrected Solution

Three discrete changes. Each can be implemented independently.

### 1. Replace `plugin/setup/agent-rulez-sample.yaml` — full rewrite with correct schema

The file currently has wrong top-level keys and non-existent action types. Replace it entirely.
Use a real security policy that demonstrates what Agent Rulez actually does: block dangerous
shell commands. This makes the file genuinely useful, not just a placeholder.

Correct schema (confirmed from `book_generator/.claude/hooks.yaml` after `rulez install`):

```yaml
version: "1.0"
settings:
  debug_logs: false
  log_level: info
  fail_open: true
  script_timeout: 5
rules:
  - name: block-force-push
    description: Prevent force-pushing to main or master branches
    matchers:
      tools: [Bash]
      command_match: "git push.*(--force|-f).*(main|master)"
    actions:
      block: true
    metadata:
      priority: 100
      enabled: true
  - name: block-recursive-delete
    description: Prevent rm -rf on non-temporary directories
    matchers:
      tools: [Bash]
      command_match: "rm\\s+-rf?\\s+(?!\\/tmp|\\.code-wizard\\/tmp)"
    actions:
      block: true
    metadata:
      priority: 90
      enabled: true
```

### 2. Fix `plugin/setup/setup.sh` — remove the `rulez hook add` line

Find and remove any line that calls `rulez hook add --config` or any variant. Replace with:

```bash
rulez install
```

Update the surrounding comment to say: "installs Agent Rulez policy rules (security enforcement,
not session capture)". The `rulez install` command reads `.claude/hooks.yaml` and is the correct
way to activate the policy file.

### 3. Add Agent Rulez `run:` rule for session capture + Write fallback

**Preferred approach:** Add a `run:` rule to `agent-rulez-sample.yaml` that captures PostToolUse
events. The script reads JSON from stdin and appends tool call records to the session file.

Add to `agent-rulez-sample.yaml` after the block rules:

```yaml
  - name: capture-session
    description: Capture tool call events to session JSON for /codebase-wizard-export
    matchers:
      tools: [Read, Grep, Glob, Write]
    actions:
      run: "bash .code-wizard/scripts/capture-session.sh"
    metadata:
      priority: 10
      enabled: true
```

Create `plugin/scripts/capture-session.sh` (deployed to `.code-wizard/scripts/` by setup.sh):

```bash
#!/bin/bash
# Reads PostToolUse event JSON from stdin, appends to session file.
# Event schema: {"hook_event_name","tool_name","tool_input","session_id","timestamp"}
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")
SESSION_FILE=".code-wizard/sessions/${SESSION_ID}.json"
mkdir -p .code-wizard/sessions
if [ ! -f "$SESSION_FILE" ]; then
  echo '{"version":"1.0","session_id":"'"$SESSION_ID"'","turns":[]}' > "$SESSION_FILE"
fi
python3 -c "
import sys, json
data = json.loads(open('$SESSION_FILE').read())
event = json.loads('''$INPUT''')
data['turns'].append(event)
open('$SESSION_FILE', 'w').write(json.dumps(data, indent=2))
" 2>/dev/null || true
```

**Fallback approach:** In `plugin/SKILL.md` (Answer Loop section), also add Write tool instruction
as fallback when Agent Rulez is not installed:

> After each answer, call the Write tool to append the Q&A turn to
> `.code-wizard/sessions/{session_id}.json` (session_id = repo-name + date).
> Turn schema: `{"turn": N, "question": "...", "anchor": "file:line", "explanation": "...",
> "next_options": ["...", "..."]}`.

## Files to Change

- `plugin/setup/agent-rulez-sample.yaml` — full rewrite with correct schema (rules:, not hooks:); add capture-session run: rule
- `plugin/setup/setup.sh` — remove `rulez hook add` line, replace with `rulez install`; deploy capture-session.sh to .code-wizard/scripts/
- `plugin/scripts/capture-session.sh` — NEW: reads PostToolUse JSON from stdin, appends to session file
- `plugin/SKILL.md` — add session Write fallback instruction to Answer Loop
