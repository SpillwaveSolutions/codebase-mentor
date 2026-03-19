# Codebase Structure

**Analysis Date:** 2026-03-19

## Directory Layout

```
codebase-mentor/
├── CLAUDE.md                      # Context guide for Claude Code (this repo's docs)
├── firebase-debug.log             # Firebase runtime logs (generated)
└── plugin/                        # Agent skill definition and references
    ├── SKILL.md                   # Main skill spec: triggers, phases, core flow
    └── references/                # Phase-specific behavioral specs
        ├── chat-feel.md           # Tone, warmth, formatting rules (loaded always)
        ├── scan-patterns.md       # Language/framework detection heuristics (Phase 1)
        ├── navigation-commands.md # Session navigation & history (Phase 3)
        ├── tutorial-mode.md       # Tutorial parsing & step tracking (Phase 4)
        └── persistence.md         # Session save/export/resume (Phase 5)
```

## Directory Purposes

**`plugin/`:**
- Purpose: Contains the complete agent skill specification
- Contains: SKILL.md (entry point) + 5 reference modules
- Key files: `SKILL.md` defines activation triggers and phase flow; reference files are loaded on-demand by each phase

**`plugin/references/`:**
- Purpose: Modular behavioral specifications loaded lazily by each phase
- Contains: 5 markdown files covering tone, scanning, navigation, tutorials, persistence
- Key files: All files are referenced in `SKILL.md` and loaded during their respective phase activation

## Key File Locations

**Entry Points:**

- `plugin/SKILL.md`: The main agent skill specification. Frontmatter (lines 1-13) defines activation triggers. Lines 22-300 define the 5 phases and their responsibilities.

**Configuration:**

- `plugin/references/chat-feel.md`: Centralized tone, formatting, and recovery patterns. Governs all responses across all phases.

**Core Logic:**

- `plugin/SKILL.md` (Phase 1, lines 50-92): Repo scanning entry point; delegates to `scan-patterns.md`
- `plugin/SKILL.md` (Phase 2, lines 96-157): Question answering core loop
- `plugin/SKILL.md` (Phase 3, lines 160-197): Navigation handler; delegates to `navigation-commands.md`
- `plugin/SKILL.md` (Phase 4, lines 201-233): Tutorial mode entry; delegates to `tutorial-mode.md`
- `plugin/SKILL.md` (Phase 5, lines 237-272): Session save entry; delegates to `persistence.md`

**Reference & Behavioral:**

- `plugin/references/scan-patterns.md`: Language-specific heuristics for detecting entry points, folder roles, auth systems, DB patterns (loaded in Phase 1)
- `plugin/references/navigation-commands.md`: Session stack operations, command parsing, fuzzy matching rules (loaded in Phase 3)
- `plugin/references/tutorial-mode.md`: Document chunk parsing, step progression, interrupt handling, simulation prompts (loaded in Phase 4)
- `plugin/references/persistence.md`: Session export formats (markdown and JSON), auto-save prompts, resume logic (loaded in Phase 5)
- `plugin/references/chat-feel.md`: Approved phrases, banned openers, message length rules, code formatting, recovery patterns (always loaded)

**Testing:**

- No test files. This is a prompt specification (agent skill), not executable code.

## Naming Conventions

**Files:**
- Reference files are `[phase-name].md` in kebab-case: `scan-patterns.md`, `navigation-commands.md`, `tutorial-mode.md`, `persistence.md`, `chat-feel.md`
- Main skill file: `SKILL.md` (all caps)
- Context file: `CLAUDE.md` (all caps, specific to this repository's documentation)

**Sections within files:**
- Sections use markdown headings (`##`, `###`) to denote logical chunks
- Code examples use language-tagged fences (e.g., ` ```json`, ` ```markdown`, ` ```javascript`)
- Tables use GitHub-flavored markdown syntax

**Session saved files:**
- Format: `[primary-topic]-[YYYY-MM-DD].md` for transcript/tutorial
- Format: `[primary-topic]-[YYYY-MM-DD].json` for session state snapshot
- Examples: `auth-flow-2026-03-18.md`, `login-walkthrough-2026-03-18.json`

## Where to Add New Code

**New Phase or Feature:**
- Add phase number and name to `SKILL.md` phases list (around line 24)
- Create reference file: `plugin/references/[phase-name].md`
- Add Phase to main flow in `SKILL.md` with trigger conditions and step-by-step instructions
- Load the reference file only when the phase is active (lazy loading)

**New Tone / Behavioral Rule:**
- Add to `plugin/references/chat-feel.md` sections (e.g., new "Approved phrases" entry, new recovery pattern)
- All phases will inherit the change automatically since `chat-feel.md` is always loaded

**New Language Detection Pattern:**
- Add to `plugin/references/scan-patterns.md` under "Entry Point Detection by Language" or "Folder Role Identification"
- Phase 1 (repo scanning) will use the new pattern on next repo load

**New Navigation Command:**
- Add command + handler to table in `plugin/references/navigation-commands.md` (lines 29-103)
- Phase 3 will recognize the command on next user input

**New Tutorial Feature:**
- Add new capability (e.g., new step progression option, new simulation type) to `plugin/references/tutorial-mode.md`
- Update step presentation format if needed (currently lines 57-79)

## Special Directories

**`plugin/`:**
- Purpose: Agent skill enclosure. Contains everything needed for the skill to function.
- Generated: No (manually authored spec files)
- Committed: Yes (entire directory is versioned)

**`.planning/`:**
- Purpose: GSD planning and analysis outputs (created separately)
- Generated: Yes (by GSD mapping/planning commands)
- Committed: No (`.gitignore` excludes this)

**`firebase-debug.log`:**
- Purpose: Firebase emulator debug output
- Generated: Yes (runtime artifact)
- Committed: No (should be `.gitignore`'d)

## Reference Files Load Order by Phase

| Phase | Trigger | Reference files loaded |
|-------|---------|----------------------|
| Always | Every interaction | `plugin/references/chat-feel.md` |
| 1 - Scan | User shares repo / pastes files | `plugin/references/scan-patterns.md` |
| 2 - Questions | User asks "how does X work?" | (none - uses SKILL.md core logic) |
| 3 - Navigation | User says "rewind", "jump to", etc. | `plugin/references/navigation-commands.md` |
| 4 - Tutorial | README found or user says "teach me" | `plugin/references/tutorial-mode.md` |
| 5 - Persistence | User says "save", "export", "load" | `plugin/references/persistence.md` |

## Code Examples by Pattern

**Session Stack Entry (used in Phase 3 navigation):**

Located in `plugin/references/navigation-commands.md` lines 10-24:
```json
{
  "repo": "my-app",
  "history": [
    { "index": 0, "topic": "app entry point",     "file": "index.js",                "line": 1  },
    { "index": 1, "topic": "login endpoint",       "file": "routes/auth.js",          "line": 14 },
    { "index": 2, "topic": "token verification",   "file": "middleware/auth.js",       "line": 8  },
    { "index": 3, "topic": "profile controller",   "file": "controllers/profile.js",  "line": 22 }
  ],
  "current": 3,
  "tutorial_step": null,
  "bookmarks": []
}
```

**Code Snippet Format (used in Phase 2 question answering):**

Located in `plugin/references/chat-feel.md` lines 64-85:
```javascript
// src/middleware/auth.js: line 8
const verifyToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(403).json({ error: 'No token' });
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;  // <-- this is the key line: attaches user to request
    next();
  } catch (err) {
    res.status(401).json({ error: 'Bad token' });
  }
};
```

**Follow-Up Options Format (end of every Phase 2 response):**

Located in `plugin/references/chat-feel.md` lines 90-108:
```
**Next - want to:**
- **Trace back**: where does this token get created?
- **Forward**: what happens when `req.user` hits the controller?
- **Jump**: show me the DB save on signup
```

**Tutorial Step Format (Phase 4):**

Located in `plugin/references/tutorial-mode.md` lines 56-79:
```
**Step 2 of 5: Set up env vars**

// .env
DATABASE_URL=postgres://localhost:5432/myapp
JWT_SECRET=supersecret

Copy this into a `.env` file at the root. The app reads these at startup
via `dotenv`—`process.env.DATABASE_URL` becomes your DB connection string.

Run it? Or skip to step 3?
```

**Session Export as Tutorial (Phase 5):**

Located in `plugin/references/persistence.md` lines 95-129. Format includes:
- Title + date + repo name
- Numbered steps with code snippets
- "What's happening" explanation per step
- "What to notice" callout per step
- Summary of topics covered
- Suggestions for next exploration

---

*Structure analysis: 2026-03-19*
