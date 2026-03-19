# Architecture

**Analysis Date:** 2026-03-19

## Pattern Overview

**Overall:** Agent Skill Pattern - a modular, phase-driven conversational system designed as a Claude agent "skill" (prompt specification).

**Key Characteristics:**
- Phase-based flow: Agent behavior changes based on conversation context
- Lazy-loaded reference modules: Each phase loads its own behavioral spec only when needed
- Session state management: Maintains conversation history with navigation capabilities
- Conversational UI: Designed for natural language interaction with code guidance

## Layers

**Phase-1 - Repo Scanning:**
- Purpose: Initial repository exploration and understanding
- Location: `plugin/SKILL.md` (lines 50-92), `plugin/references/scan-patterns.md`
- Contains: Language-specific entry point detection, folder role identification, auth/DB pattern matching
- Depends on: File system inspection heuristics, language-specific naming patterns
- Used by: Agent initialization when user shares a repository

**Phase-2 - Question Handling:**
- Purpose: Answer "how does X work?" questions by finding and explaining code
- Location: `plugin/SKILL.md` (lines 96-157)
- Contains: Code search logic, snippet extraction, plain-English explanation, follow-up prediction
- Depends on: Code location tracking, session history management
- Used by: Core conversational loop - every user question triggers this

**Phase-3 - Navigation & Session State:**
- Purpose: Enable users to rewind, jump, and browse conversation history
- Location: `plugin/SKILL.md` (lines 160-197), `plugin/references/navigation-commands.md`
- Contains: Session stack operations, command parsing (rewind, jump, bookmark), fuzzy matching
- Depends on: Session history maintained in working memory
- Used by: User navigation commands like "rewind", "go back to auth", "what were we talking about?"

**Phase-4 - Tutorial Mode:**
- Purpose: Guide users through structured step-by-step learning experiences
- Location: `plugin/SKILL.md` (lines 201-233), `plugin/references/tutorial-mode.md`
- Contains: Document parsing (chunk by heading), step progression tracking, interrupt handling, simulation prompts
- Depends on: README/docs files or synthesized tutorials from code
- Used by: When README exists or user says "teach me" or "walk me through"

**Phase-5 - Persistence & Session Save:**
- Purpose: Save and resume conversation sessions
- Location: `plugin/SKILL.md` (lines 237-272), `plugin/references/persistence.md`
- Contains: Session export (markdown and JSON), transcript formatting, session resume logic
- Depends on: File system write access, session state snapshot
- Used by: User save/load commands and natural session end detection

**Cross-Layer - Chat Feel & Tone:**
- Purpose: Governance of conversational style across all phases
- Location: `plugin/references/chat-feel.md`
- Contains: Approved phrases, banned openers, message length rules, code formatting standards, recovery patterns
- Depends on: Nothing (always in context)
- Used by: Every response generation in all phases

## Data Flow

**User Input → Phase Detection → Reference Load → Action → Session Update:**

1. **User input:** User types a message (question, command, code paste, etc.)
2. **Phase detection:** Agent determines which phase is active:
   - First message = Phase 1 (Repo Scan)
   - Question about code = Phase 2 (Question Handling)
   - "rewind"/"jump" = Phase 3 (Navigation)
   - "tutorial"/"teach me" = Phase 4 (Tutorial Mode)
   - "save"/"export" = Phase 5 (Persistence)
3. **Reference load:** Load the relevant reference file (lazy-loaded, not all at once)
4. **Action:** Execute phase logic:
   - Phase 1: Scan repo, build tour map, greet with concrete offer
   - Phase 2: Find code, show snippet, explain, predict next
   - Phase 3: Resolve navigation command, update session.current, acknowledge
   - Phase 4: Parse/advance tutorial step, show code, handle interrupts
   - Phase 5: Serialize session to markdown/JSON, save, offer resume
5. **Session update:** Push to history stack (max 20 entries), increment current position
6. **Response:** Return formatted message + follow-up options

**State Management:**

Session state lives in working memory (agent context):
```json
{
  "repo": "repository-name",
  "history": [
    { "topic": "what we looked at", "file": "path/to/file.js", "line": 14 },
    { "topic": "next thing", "file": "path/to/other.js", "line": 22 }
  ],
  "current": 1,
  "tutorial_step": null,
  "bookmarks": []
}
```

- **Capacity:** Max 20 history entries; oldest are dropped when full
- **Persistence:** Saved to markdown (`[topic]-[YYYY-MM-DD].md`) and JSON (`.json` companion)
- **Resume:** On next session, if `.json` exists, offer to pick up from last position

## Key Abstractions

**Tour Map:**
- Purpose: Organizes discovered code into meaningful categories for user navigation
- Examples: Entry point, Auth system, Data layer, Documentation
- Pattern: Built during Phase 1 scan, surfaced in initial greeting, used as navigation reference in Phase 3

**Code Snippet:**
- Purpose: Focused excerpt from a source file, anchored with context
- Examples: `src/routes/auth.js: line 14` with surrounding function
- Pattern: Always includes file path + line number, kept to 15-25 lines, inline comment on key lines

**History Stack Entry:**
- Purpose: Records a single point in the conversation for later navigation
- Examples: `{ topic: "login endpoint", file: "routes/auth.js", line: 14 }`
- Pattern: One entry per question answered; used for rewind/jump/resume

**Follow-Up Options:**
- Purpose: Guides user toward next natural question
- Examples: "Trace back" (upstream), "Forward" (downstream), "Jump to" (related but non-adjacent)
- Pattern: Always 2-3 options, formatted as bullet list with labels and descriptions

**Synthesized Tutorial:**
- Purpose: When no docs exist, build a step-by-step guide from code structure
- Examples: Trace login flow as steps 1-5
- Pattern: Same format as doc-based tutorials (step N of total, code, explanation)

## Entry Points

**Agent Skill Activation:**
- Location: `plugin/SKILL.md` frontmatter (lines 1-13)
- Triggers: When user wants to understand code, asks "how does X work?", shares a repo, or says "teach me"
- Responsibilities: Define when the skill activates and describe core principles

**Phase-1 Repo Scan:**
- Location: `plugin/SKILL.md` (lines 50-92) + `plugin/references/scan-patterns.md`
- Triggers: User shares a repo, pastes files, or says "here's my codebase"
- Responsibilities: Detect entry points, identify folder roles, find auth/DB patterns, build tour map, greet with concrete offer

**Phase-2 Question Handler:**
- Location: `plugin/SKILL.md` (lines 96-157)
- Triggers: User asks how something works or where something is
- Responsibilities: Find code, show snippet, explain in plain English, predict next, push to history

**Phase-3 Navigation Loop:**
- Location: `plugin/SKILL.md` (lines 160-197) + `plugin/references/navigation-commands.md`
- Triggers: User says "rewind", "jump to", "back", "where are we?"
- Responsibilities: Parse command, resolve to history entry or repo search, update session.current, acknowledge transition

**Phase-4 Tutorial Entry:**
- Location: `plugin/SKILL.md` (lines 201-233) + `plugin/references/tutorial-mode.md`
- Triggers: README found, `/docs/` exists, or user says "tutorial"/"teach me"
- Responsibilities: Parse tutorial document into steps, present step N of total, handle mid-tutorial interrupts

**Phase-5 Session Save:**
- Location: `plugin/SKILL.md` (lines 237-272) + `plugin/references/persistence.md`
- Triggers: User says "save", "export", "load session", or at natural session end
- Responsibilities: Serialize history to markdown/JSON, offer auto-save, handle session resume

## Error Handling

**Strategy:** Graceful recovery with user clarification; never invent file paths or function names.

**Patterns:**

**Code Not Found:**
- Response: "I don't see `[identifier]` anywhere - can you paste the line? Or did you mean `[close-match]`?"
- Avoids: Making up paths; always asks for clarification
- Location: `plugin/references/chat-feel.md` (lines 131-134)

**Ambiguous Reference:**
- Response: "I see `[X]` in a few places - did you mean the one in `[file1]` or `[file2]`?"
- Avoids: Silently picking one when multiple matches exist
- Location: `plugin/references/chat-feel.md` (lines 135-138)

**Vague Question:**
- Response: "When you say '[vague question]' - do you mean [interpretation A] or [interpretation B]?"
- Avoids: Guessing what user meant
- Location: `plugin/references/chat-feel.md` (lines 140-142)

**Navigation at History Boundary:**
- Response: "We're already at the start - that's where we started with [first topic]."
- Pattern: Clamp navigation commands to valid index range
- Location: `plugin/references/navigation-commands.md` (lines 126-128)

**No Tutorial Docs:**
- Response: "No tutorial here - but I can build one from the code. I'll trace the login flow and walk you through it. Sound good?"
- Pattern: Synthesize a tutorial from code structure rather than failing
- Location: `plugin/SKILL.md` (lines 226-229)

## Cross-Cutting Concerns

**Logging:** No traditional logging. Session history is the audit trail; saved markdown/JSON files serve as persistent logs.

**Validation:** User input is interpreted via fuzzy matching (Phase 3 navigation commands) and natural language parsing (Phase 4 tutorial steps). Errors degrade gracefully with clarification requests.

**Authentication:** Not applicable - this is an agent skill, not a service with auth requirements. The skill authenticates implicitly via the Claude agent platform.

**Tone & Warmth:** Governed centrally in `plugin/references/chat-feel.md`. Every response should:
- Use approved phrases ("Cool -", "Got it", "Okay, let's zoom in")
- Avoid banned openers ("Great question!", "Sure, I'd be happy to help!")
- Keep messages short: 1 paragraph for explanations, 3 bullets for follow-up options
- Always include code snippets before plain-English explanation

**Context Management:** Each phase loads only its reference file, avoiding context bloat. `chat-feel.md` is always loaded (governs all responses). History is trimmed to 20 entries; oldest are dropped when full.

---

*Architecture analysis: 2026-03-19*
