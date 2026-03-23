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

3. **Agent Rulez is a policy enforcement engine, not a session recorder.** It can block commands,
   inject text into prompts, or run scripts — but it cannot append JSON turn data to files. Using
   Agent Rulez for session capture is the wrong tool. The session capture requirement cannot be
   satisfied by any Agent Rulez action type.

4. **Session capture must be done by the wizard skill itself.** After each answer turn, the wizard
   should call the Write tool to append the turn to the session file. No external hook is needed.
   This is already within the scope of the skill's existing Write tool access. The Write tool call
   should happen as the final step of the Answer Loop, after generating next-options.

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

### 3. Add session capture to the wizard skill

In `plugin/SKILL.md` (Answer Loop section), add an explicit instruction after the answer step:

> After writing each answer, call the Write tool to append the turn to
> `.code-wizard/sessions/{session_id}.json`.
>
> Turn schema:
> ```json
> {
>   "turn": 1,
>   "question": "How does login work?",
>   "anchor": "routes/auth.js:14",
>   "code_shown": "...",
>   "explanation": "...",
>   "connections": ["middleware/auth.js", "models/user.js"],
>   "next_options": ["How does token refresh work?", "Show me the logout flow"]
> }
> ```
>
> Session ID is derived from repo name + ISO date at session start, e.g.
> `book_generator-2026-03-23`. Write mode is append (read existing JSON, push new turn, write
> back). If the file does not exist, create it with:
> ```json
> { "version": "1.0", "session_id": "...", "repo": "...", "mode": "explore", "turns": [] }
> ```

This does not require any hook infrastructure. The Write tool is already available to the skill.

## Files to Change

- `plugin/setup/agent-rulez-sample.yaml` — full rewrite with correct schema (rules:, not hooks:)
- `plugin/setup/setup.sh` — remove `rulez hook add` line, replace with `rulez install`
- `plugin/SKILL.md` — add session Write instruction to Answer Loop
