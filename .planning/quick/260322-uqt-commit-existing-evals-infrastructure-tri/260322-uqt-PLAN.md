---
phase: quick
plan: 260322-uqt
type: execute
wave: 1
depends_on: []
files_modified:
  - evals/evals.json
  - evals/run_evals.py
  - evals/serve_review.py
  - evals/trigger_review.html
autonomous: true
requirements: []

must_haves:
  truths:
    - "evals/ directory is tracked in git with all 4 files committed"
    - "evals.json contains 20 labeled queries and baseline_run results (100% pass rate)"
    - "git log shows a single clean commit adding the eval infrastructure"
  artifacts:
    - path: "evals/evals.json"
      provides: "20 trigger/no-trigger labeled queries + baseline_run metrics"
    - path: "evals/run_evals.py"
      provides: "CLI eval runner — sends queries to Claude Haiku, reports pass_rate/duration/tokens"
    - path: "evals/serve_review.py"
      provides: "HTTP server bridging trigger_review.html to evals.json on disk"
    - path: "evals/trigger_review.html"
      provides: "Browser UI for reviewing and correcting query labels"
  key_links:
    - from: "evals/trigger_review.html"
      to: "evals/serve_review.py"
      via: "fetch to localhost:8765 (save/load endpoints)"
    - from: "evals/run_evals.py"
      to: "evals/evals.json"
      via: "reads queries, writes baseline_run results"
---

<objective>
Commit the existing evals infrastructure for the codebase-wizard skill trigger tuning.

Purpose: The eval tooling (20 labeled queries, runner, review UI, HTTP bridge) was built and the baseline run completed (100% pass rate). These files are untracked — they need to be committed so the infrastructure is preserved in version control and available for future trigger tuning iterations.

Output: A single git commit adding evals/ with all 4 files intact and no modifications.
</objective>

<execution_context>
@/Users/richardhightower/.claude/get-shit-done/workflows/execute-plan.md
@/Users/richardhightower/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Verify evals files are complete and commit</name>
  <files>evals/evals.json, evals/run_evals.py, evals/serve_review.py, evals/trigger_review.html</files>
  <action>
Verify the 4 files exist and evals.json contains the expected data, then commit.

Verification checks (run before committing):
1. All 4 files present: `ls evals/`
2. evals.json has 20 queries and baseline_run data:
   `python3 -c "import json; d=json.load(open('evals/evals.json')); print(len(d['queries']), 'queries;', d['baseline_run']['pass_rate']['mean'], '% pass rate')"`
3. Expected output: `20 queries; 100.0 % pass rate`

If all checks pass, stage and commit:
```
git add evals/evals.json evals/run_evals.py evals/serve_review.py evals/trigger_review.html
git commit -m "feat(evals): add codebase-wizard trigger tuning infrastructure

- evals/evals.json — 20 labeled queries (10 trigger, 10 no-trigger) + baseline run (100% pass rate, ~700ms, ~405 tokens/query)
- evals/run_evals.py — CLI runner using Claude Haiku; reports pass_rate, duration_ms, total_tokens
- evals/trigger_review.html — browser UI for reviewing and correcting query labels
- evals/serve_review.py — HTTP bridge (port 8765) connecting HTML UI to evals.json on disk

Baseline: 100% pass rate on Claude Haiku (2026-03-22)"
```
  </action>
  <verify>
    <automated>git log --oneline -1 && git show --stat HEAD | grep "evals/" | wc -l</automated>
  </verify>
  <done>git log shows the commit; `git show --stat HEAD` lists all 4 evals/ files; `git status` shows evals/ is no longer untracked</done>
</task>

</tasks>

<verification>
After commit:
- `git status` — no untracked files under evals/
- `git show --stat HEAD` — shows 4 files added: evals/evals.json, run_evals.py, serve_review.py, trigger_review.html
- `git log --oneline -3` — commit message starts with "feat(evals):"
</verification>

<success_criteria>
Single clean commit adds evals/ infrastructure. All 4 files committed. evals.json baseline_run confirms 100% pass rate. No other files modified.
</success_criteria>

<output>
After completion, create `.planning/quick/260322-uqt-commit-existing-evals-infrastructure-tri/260322-uqt-SUMMARY.md` with:
- What was committed (file list)
- Baseline metrics from evals.json (pass_rate, duration_ms, total_tokens)
- Commit SHA
</output>
