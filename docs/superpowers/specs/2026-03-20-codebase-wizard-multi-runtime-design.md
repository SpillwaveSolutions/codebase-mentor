# Codebase Wizard — Multi-Runtime Design Spec

**Date:** 2026-03-20
**Status:** Draft
**Supersedes:** `2026-03-19-codebase-wizard-design.md` (Claude Code only)
**Project:** codebase-mentor / ai-codebase-mentor

---

## Overview

The Codebase Wizard is a universal explainer skill and multi-runtime AI plugin. It accepts any artifact — codebase, markdown spec, design doc, milestone plan — and explains it through a wizard-style Q&A conversation. Every answer is anchored to actual code or document content shown inline. All conversations are auto-captured and exportable as structured documentation.

**Core value:** A developer runs one command and walks away with a documented, navigable understanding of what they're looking at — without clicking "Approve" repeatedly or writing documentation by hand.

**Runtime strategy (Approach A — Monorepo with Converters):** The Claude Code plugin format is the canonical source. A Python package (`ai-codebase-mentor`) bundles the plugin and ships per-runtime converters that read the Claude format and generate each target runtime's native config files on install. No runtime-specific artifacts are committed to the repo — they are generated on the fly.

Approach A was chosen over two alternatives:
- **Approach B (Per-runtime plugin directories):** Rejected — skill content would be duplicated 4x; a fix to one SKILL.md requires updating all copies.
- **Approach C (Shared core + runtime wrappers):** Rejected — requires refactoring the existing `plugins/codebase-wizard/` structure; Approach A is additive.

---

## Section 1: Repository Structure

```
plugins/codebase-wizard/               ← canonical source (Claude Code format)
  .claude-plugin/
    plugin.json                        ← Claude Code manifest
  skills/
    explaining-codebase/
      SKILL.md                         ← main wizard logic (5-phase conversational flow)
      references/
        chat-feel.md
        scan-patterns.md
        navigation-commands.md
        tutorial-mode.md
        persistence.md
        describe-questions.md
        explore-questions.md
        codex-tools.md
    configuring-codebase-wizard/
      SKILL.md                         ← setup skill
      scripts/
        setup.sh
        agent-rulez-sample.yaml
    exporting-conversation/
      SKILL.md                         ← export/synthesis skill
  agents/
    codebase-wizard-agent.md           ← session policy island (read + scoped write)
    codebase-wizard-setup-agent.md     ← setup policy island (settings.local.json write)
  commands/
    codebase-wizard.md                 ← context:fork → codebase-wizard-agent
    codebase-wizard-export.md          ← context:fork → codebase-wizard-agent
    codebase-wizard-setup.md           ← context:fork → codebase-wizard-setup-agent

ai_codebase_mentor/                    ← Python package source
  plugin/                              ← bundled copy of plugins/codebase-wizard/
  converters/
    base.py                            ← RuntimeInstaller base class + shared utilities
    claude.py                          ← v1.0: install/uninstall to ~/.claude/plugins/
    opencode.py                        ← v1.2: convert to OpenCode format
    codex.py                           ← v1.3: convert to TOML subagent format
    gemini.py                          ← v1.4: convert to Gemini format
  cli.py                               ← click entry point
  __init__.py

pyproject.toml
.github/
  workflows/
    test-installer.yml                 ← v1.0: run install + uninstall on push
    publish-pypi.yml                   ← v1.2: publish on tag
```

**Note on "phases" terminology:** `SKILL.md` defines a 5-phase *conversational* flow (Repo Scan → Question Handling → Navigation → Tutorial Mode → Persistence). This is distinct from the GSD *planning* phases (01–07) that track development milestones. The two uses of "phase" do not conflict.

---

## Section 2: Python Package

### CLI Interface

```bash
ai-codebase-mentor install --for claude              # global (~/.claude/plugins/)
ai-codebase-mentor install --for claude --project    # per-project (./plugins/)
ai-codebase-mentor install --for opencode            # v1.2
ai-codebase-mentor install --for codex               # v1.3 (always per-project)
ai-codebase-mentor install --for gemini              # v1.4
ai-codebase-mentor install --for all                 # all supported runtimes

ai-codebase-mentor uninstall --for claude
ai-codebase-mentor uninstall --for all

ai-codebase-mentor version
ai-codebase-mentor status                            # what's installed, where, version
```

### Converter Interface

Each converter in `converters/` implements the `RuntimeInstaller` base class:

```python
class RuntimeInstaller:
    def install(self, source: Path, target: str = "global") -> None:
        """
        source: path to bundled plugin dir (ai_codebase_mentor/plugin/)
        target: "global" (~/.{runtime}/plugins/) or "project" (./plugins/)
        Raises: RuntimeError if install fails.
        Idempotent: calling install when already installed updates in place.
        """

    def uninstall(self, target: str = "global") -> None:
        """
        Removes all files written by install().
        No-op if not installed (does not raise).
        """

    def status(self) -> dict:
        """
        Returns: {"installed": bool, "location": str | None, "version": str | None}
        """
```

**Error contract:** `install()` raises `RuntimeError` with a human-readable message on failure. `uninstall()` is always safe to call — no-op if not installed. All converters are idempotent for install.

### Converter Responsibilities

| Converter | Input | Output |
|-----------|-------|--------|
| `claude.py` | `plugin/` dir | Copy to `~/.claude/plugins/codebase-wizard/` or `./plugins/codebase-wizard/` |
| `opencode.py` | `plugin/agents/*.md`, `plugin/commands/*.md` | OpenCode-format plugin with lowercase tool names |
| `codex.py` | `plugin/agents/codebase-wizard-agent.md` (`allowed_tools`) | `.codex/config.toml`, `.codex/agents/explorer.toml`, `.codex/agents/worker.toml`, `AGENTS.md` |
| `gemini.py` | `plugin/agents/*.md`, `plugin/commands/*.md` | Gemini plugin format with snake_case tool names |

### Codex Converter Detail (v1.3)

Codex subagents reached GA on March 16, 2026. The converter maps Claude's `allowed_tools` onto Codex's TOML subagent model:

- Read-only tools (`Read`, `Glob`, `Grep`, read Bash) → `explorer.toml` with `sandbox_mode = "read-only"`
- Write-scoped tools → `worker.toml` with `sandbox_mode = "read-write"`, scoped to `.code-wizard/**`
- `config.toml`: `max_threads = 3`, `max_depth = 1`
- `AGENTS.md`: documents manual export requirement (Codex has no hook support)
- Codex install is always per-project (no global path)

---

## Section 3: Milestones

### Milestone 1 — v1.0: Claude Code

GSD planning phases 1–3 are complete. Remaining:

| GSD Phase | Goal |
|-----------|------|
| 04 | Claude Code marketplace manifest — `marketplace.json`, finalize plugin metadata |
| 05 | Claude Code install/uninstall — `claude.py`, global + project, clean uninstall |
| 06 | Python package — `pyproject.toml`, package structure, `cli.py`, Claude-only |
| 07 | GitHub Actions — installer test workflow on push (no PyPI publish) |

**Release gate (all must pass):**
- `ai-codebase-mentor install --for claude` copies plugin to `~/.claude/plugins/codebase-wizard/`
- `ai-codebase-mentor install --for claude --project` copies to `./plugins/codebase-wizard/`
- `ai-codebase-mentor uninstall --for claude` removes all installed files cleanly
- `ai-codebase-mentor status` reports correct install state
- GitHub Actions test workflow passes on push
- PyPI publish is explicitly excluded from this milestone

### Milestone 2 — v1.2: OpenCode + PyPI

| GSD Phase | Goal |
|-----------|------|
| 01 | OpenCode converter — `opencode.py`, converts agents/commands to OpenCode format |
| 02 | PyPI publish — finalize `pyproject.toml`, publish-on-tag GitHub Actions workflow |

**Release gate:**
- `pip install ai-codebase-mentor` installs from PyPI
- `ai-codebase-mentor install --for opencode` generates correct OpenCode plugin format
- OpenCode install and uninstall are clean
- Publish workflow fires on semver tag, not on every push

### Milestone 3 — v1.3: Codex (subagent-aware)

| GSD Phase | Goal |
|-----------|------|
| 01 | Codex converter — `codex.py`, TOML explorer/worker, `AGENTS.md`, per-project install |

**Release gate:**
- `ai-codebase-mentor install --for codex` generates `.codex/config.toml` and both agent TOML files
- Explorer TOML has `sandbox_mode = "read-only"`, worker has `sandbox_mode = "read-write"`
- `AGENTS.md` documents manual export step
- No hook installation attempted (Codex has no hook support)

### Milestone 4 — v1.4: Gemini

| GSD Phase | Goal |
|-----------|------|
| 01 | Gemini converter — `gemini.py`, snake_case tool names, Gemini plugin format |

**Release gate:**
- `ai-codebase-mentor install --for gemini` generates correct Gemini plugin format
- Tool names converted to snake_case
- Install and uninstall are clean

### Milestone 5 — v1.5: LangChain DeepAgent Standalone App

| GSD Phase | Goal |
|-----------|------|
| 01 | Standalone application — LangChain DeepAgent CLI app, own PyPI package, own installer |

**Design note:** LangChain DeepAgents uses the standard skill format (SKILL.md + agents + commands) and supports MCP — equivalent in plugin model to Claude Code, OpenCode, and Gemini CLI. The standalone app is architecturally independent from `ai-codebase-mentor`. How it shares `plugins/codebase-wizard/` artifacts is an open question (see Open Questions).

**Release gate:** Defined when Milestone 5 is planned.

---

## Section 4: The Explainer

### Answer Loop (Every Response)

```
1. Find the relevant artifact (code, section, passage)
2. Show it as a code block with full anchor:
      // src/auth/middleware.ts → AuthMiddleware → validate() → L14-31
3. Explain in plain English (1 short paragraph, no undefined jargon)
4. Show connections (code mode only):
      → calls:     src/services/token.ts → TokenService → verify()
      → called by: src/routes/api.ts → router.use() → L8
5. Predict next (2-3 follow-up options)
```

### 5-Phase Conversational Flow

The skill's internal execution model — distinct from GSD planning phases:

| Phase | Trigger | Reference loaded |
|-------|---------|-----------------|
| 1 — Repo Scan | User shares repo / pastes files | `scan-patterns.md` |
| 2 — Question Handling | User asks "how does X work?" | *(none extra)* |
| 3 — Navigation | "rewind", "jump to", "go back" | `navigation-commands.md` |
| 4 — Tutorial Mode | README found, or "teach me" | `tutorial-mode.md` |
| 5 — Persistence | "save", "export", "load session" | `persistence.md` |

### Modes

| Mode | Arg | Reference | Output |
|------|-----|-----------|--------|
| Describe | `--describe` | `describe-questions.md` | `CODEBASE.md` |
| Explore | `--explore` | `explore-questions.md` | `TOUR.md` |
| File | `--file <path>` | *(markdown parse)* | `FILE-NOTES.md` |
| Ask | *(no args)* | After user selects | Same as above |

---

## Section 5: Permission Model

### Session Agent (`codebase-wizard-agent`)

- `Read`, `Glob`, `Grep` — unrestricted (wizard reads any file it explains)
- `Write/Edit(.code-wizard/**)`, `Write/Edit(.claude/code-wizard/**)` — scoped storage writes only
- `Bash(node*|grep*|find*|cat*|ls*|rulez*)` — safe, read-oriented shell ops
- `WebSearch`, `WebFetch` — pre-authorized; availability-probed before use

### Setup Agent (`codebase-wizard-setup-agent`)

Superset of session agent. Additional for one-time onboarding:
- `Write/Edit(.claude/settings.local.json)` — write scoped permissions
- `Write/Edit(AGENTS.md)` — Codex platform support
- `Bash(bash*|mkdir*|cp*|chmod*)` — setup filesystem operations

The dedicated setup agent is what enables `context: fork` on the setup command. The original design ran setup in main context because no agent had write permission to `settings.local.json`. That is now resolved.

---

## Section 6: Capture + Synthesis

### Agent Rulez Hook Config

`skills/configuring-codebase-wizard/scripts/agent-rulez-sample.yaml` is a template. `{resolved_storage}` is substituted with the actual path when deploying during setup.

### Session JSON Format

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

---

## Non-Goals

- Defining or owning the plugin format specification — this spec uses the existing Claude Code plugin convention
- Managing runtime version compatibility (e.g., handling OpenCode v2 format changes) — out of scope for v1.x
- Backward compatibility with the old `plugin/` directory structure — superseded by `plugins/codebase-wizard/`
- Real-time collaboration or multi-user sessions
- Cloud sync of captured sessions (local-only storage)
- Automatic git commits of generated docs
- Merging sessions from different dates into a single output document
- `--format pdf` export (deferred to post-v1.5)
- The LangChain DeepAgent standalone app architecture (defined when Milestone 5 is planned)

---

## Changes from Previous Spec

| Area | v1 (2026-03-19) | v2 (2026-03-20) |
|------|----------------|----------------|
| Platform | Claude Code only | Multi-runtime via Python converters |
| File layout | `plugin/` (flat) | `plugins/codebase-wizard/` with skill subdirs |
| Commands | Logic inline in command files | Thin wrappers; logic in SKILL.md files |
| Setup command | No `context:fork` (main context) | `context:fork` + `codebase-wizard-setup-agent` |
| Installer | `setup.sh` shell script only | Python package with per-runtime converter classes |
| Codex | AGENTS.md only, no subagent support | TOML explorer/worker subagents (Codex GA March 16, 2026) |
| Milestones | Single milestone, no runtime split | v1.0 → v1.2 → v1.3 → v1.4 → v1.5 by runtime |
| Standalone app | Not planned | v1.5 LangChain DeepAgent (defined at Milestone 5 planning) |

---

## Open Questions

| Question | Impact | Milestone |
|----------|--------|-----------|
| Does Agent Rulez support `{date}` and `{repo}` native interpolation? | Whether setup.sh pre-computes static paths | v1.0 |
| OpenCode plugin format — same schema as `.claude-plugin/plugin.json`? | Converter complexity for `opencode.py` | v1.2 |
| Gemini CLI plugin format — TOML or JSON? | Converter design for `gemini.py` | v1.4 |
| LangChain DeepAgent standalone app: how does it share `plugins/codebase-wizard/`? Shared data dependency, separate copy, or monorepo reference? | Package architecture for v1.5 | v1.5 |
| LangChain DeepAgent PyPI package name? | Naming for v1.5 | v1.5 |
