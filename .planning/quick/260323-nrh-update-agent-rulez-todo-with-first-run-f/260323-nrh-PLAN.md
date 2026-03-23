---
type: quick
title: Update Agent Rulez todo with first-run findings
date: 2026-03-23
files_modified:
  - .planning/todos/pending/2026-03-23-fix-agent-rulez-config-and-add-session-capture-hook.md
autonomous: true
---

<objective>
Rewrite the pending todo file with concrete first-run findings so the next developer (or Claude
session) has exact diagnosis, not vague guesses. The original todo was written before live testing
and describes symptoms. Research has now confirmed the root causes and the correct solution path.

Purpose: Replace speculation with facts. The todo should be actionable — not a list of things to
investigate, but a list of things to fix with known correct answers.
Output: Updated todo file at .planning/todos/pending/2026-03-23-fix-agent-rulez-config-and-add-session-capture-hook.md
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Rewrite todo with confirmed findings and corrected solution</name>
  <files>.planning/todos/pending/2026-03-23-fix-agent-rulez-config-and-add-session-capture-hook.md</files>
  <action>
Overwrite the todo file completely. Keep the same frontmatter fields (created, title, area, files)
but update `files` to reflect the actual files that need changing based on the confirmed diagnosis.

The new body must have three sections:

**## Confirmed Findings**

List the four confirmed facts from first-run testing:

1. `agent-rulez-sample.yaml` uses wrong schema. It uses a `hooks:` top-level key — the correct key
   is `rules:`. Actions `action: append` and `action: notify` do not exist in Agent Rulez. Valid
   actions are `block`, `inject`, and `run`. The file must be rewritten from scratch using the
   correct schema.

2. `rulez hook add --config` does not exist. `rulez --help` shows: `init`, `install`, `uninstall`,
   `debug`, `repl`, `validate`, `logs`, `explain`. There is no `hook` subcommand. The setup.sh and
   SKILL.md references to `rulez hook add` will fail with "unrecognized subcommand 'hook'".

3. Agent Rulez is a policy enforcement engine, not a session recorder. It can block commands,
   inject text into prompts, or run scripts — but it cannot append JSON turn data to files. Using
   Agent Rulez for session capture is the wrong tool entirely.

4. Session capture must be done by the wizard skill itself. After each answer turn, the wizard
   should call the Write tool to append the turn to the session file. No external hook is needed.
   This is already within scope of the skill's existing Write tool access.

**## Corrected Solution**

Three discrete changes needed:

1. Replace `plugin/setup/agent-rulez-sample.yaml` with a real Agent Rulez policy config. Use the
   confirmed schema (version: "1.0", settings block, rules array with matchers/actions/metadata).
   Keep it useful: add a rule that blocks dangerous git operations (force-push to main/master) and
   a rule that blocks rm -rf on non-temp directories. This makes the file genuinely valuable as a
   security config, which is what Agent Rulez is actually for.

   Correct schema reference:
   ```yaml
   version: "1.0"
   settings:
     debug_logs: false
     log_level: info
     fail_open: true
     script_timeout: 5
   rules:
     - name: block-force-push
       matchers:
         tools: [Bash]
         command_match: "git push.*(--force|-f).*(main|master)"
       actions:
         block: true
       metadata:
         priority: 100
         enabled: true
   ```

2. Fix `plugin/setup/setup.sh`: remove the `rulez hook add --config` line entirely. Replace with
   `rulez install` (which is the correct install command that reads .claude/hooks.yaml). Update
   the comment to say "installs Agent Rulez policy rules (security enforcement, not session capture)".

3. Add session capture to the wizard skill. In `plugin/SKILL.md` (or the relevant reference file
   loaded during Phase 2 question handling), add an explicit instruction: after writing each answer,
   call the Write tool to append the turn to `.code-wizard/sessions/{session_id}.json`. The turn
   schema is: `{ "turn": N, "question": "...", "anchor": "file:line", "code_shown": "...",
   "explanation": "...", "connections": [...], "next_options": [...] }`. Session ID is derived
   from repo name + ISO date at session start.

**## Files to Change**

Update the frontmatter `files` list to:
- `plugin/setup/agent-rulez-sample.yaml` (full rewrite with correct schema)
- `plugin/setup/setup.sh` (remove rulez hook add line, fix install command)
- `plugin/SKILL.md` or `plugin/references/persistence.md` (add session write instruction)
  </action>
  <verify>Read the updated todo file and confirm it contains all three sections (Confirmed Findings, Corrected Solution, Files to Change) with the four findings and three solution items.</verify>
  <done>Todo file contains concrete findings (not vague problem statements), correct Agent Rulez schema example, and actionable solution steps that can be executed without further investigation.</done>
</task>

</tasks>

<success_criteria>
The updated todo reads like a bug report with known cause and known fix — not a ticket to investigate.
A Claude executor picking this up can implement all three changes without running any research commands.
</success_criteria>
