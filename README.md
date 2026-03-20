# Codebase Mentor

**Codebase Wizard** is a Claude Code plugin that explains any codebase, spec, or markdown artifact through a wizard-style conversational Q&A interface. Every answer is anchored to actual code shown inline. Sessions are auto-captured and synthesizable as structured documentation.

## What It Does

- **Describe mode** — walks a repo owner through Q&A and produces `CODEBASE.md`
- **Explore mode** — gives a new developer a learning-order tour and produces `TOUR.md`
- **File mode** — walks through any markdown file section-by-section
- **Auto-capture** — every session is captured to JSON via Agent Rulez hooks
- **Export** — synthesize raw session logs into structured docs on demand

## Install

```bash
pip install ai-codebase-mentor
ai-codebase-mentor install --for claude
```

This copies the Codebase Wizard plugin to `~/.claude/plugins/codebase-wizard/`.

For a per-project install:

```bash
ai-codebase-mentor install --for claude --project
```

## Usage

After installing, in any Claude Code session:

```
/codebase-wizard-setup    # one-time setup: installs hooks and writes permissions
/codebase-wizard          # start a wizard session
/codebase-wizard-export   # synthesize captured sessions into docs
```

## Uninstall

```bash
ai-codebase-mentor uninstall --for claude
```

## Status

```bash
ai-codebase-mentor status
```

## CLI Reference

```
ai-codebase-mentor install   --for [claude|all] [--project]
ai-codebase-mentor uninstall --for [claude|all] [--project]
ai-codebase-mentor status
ai-codebase-mentor version
```

## Commands

| Command | Description |
|---------|-------------|
| `/codebase-wizard` | Start a wizard session (Describe, Explore, or Ask mode) |
| `/codebase-wizard-setup` | One-time onboarding: install Agent Rulez hooks, write scoped permissions |
| `/codebase-wizard-export` | Synthesize captured session JSON into `CODEBASE.md`, `TOUR.md`, or `FILE-NOTES.md` |

## How It Works

The plugin follows a 5-phase conversational flow:

| Phase | Trigger | What loads |
|-------|---------|-----------|
| 1 — Repo Scan | User shares repo | `scan-patterns.md` |
| 2 — Question Handling | "how does X work?" | *(none extra)* |
| 3 — Navigation | "rewind", "jump to" | `navigation-commands.md` |
| 4 — Tutorial Mode | README found, or "teach me" | `tutorial-mode.md` |
| 5 — Persistence | "save", "export" | `persistence.md` |

Every answer follows the same loop:
1. Find the relevant code
2. Show it as a code block with a full anchor (`src/auth/middleware.ts → validate() → L14-31`)
3. Explain in plain English
4. Show connections (calls / called-by)
5. Predict 2–3 follow-up options

## Milestones

| Version | Runtime | Status |
|---------|---------|--------|
| v1.0 | Claude Code | Complete |
| v1.2 | OpenCode + PyPI publish | Planned |
| v1.3 | Codex (subagent-aware) | Planned |
| v1.4 | Gemini CLI | Planned |
| v1.5 | LangChain DeepAgent standalone | Planned |

## Development

```bash
git clone https://github.com/SpillwaveSolutions/codebase-mentor
cd codebase-mentor
pip install -e .
pytest tests/
```

## License

MIT — Spillwave Solutions
