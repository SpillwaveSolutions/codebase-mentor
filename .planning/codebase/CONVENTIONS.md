# Coding Conventions

**Analysis Date:** 2026-03-19

## Overview

The codebase-mentor project is a **markdown-based skill definition** for Claude, not a traditional code repository. All operational logic is defined in structured markdown files with specific formatting rules, tone guidelines, and procedural patterns. This document covers the conventions that govern how the skill is written and how it instructs Claude to behave.

---

## File Organization Conventions

**Structure:**
- `SKILL.md`: Primary skill definition with frontmatter, core principles, and phase descriptions
- `references/`: Modular reference files loaded on-demand during specific phases
  - `chat-feel.md`: Tone, approved phrases, banned openers, message length rules
  - `scan-patterns.md`: Entry point detection, folder role identification, language-specific heuristics
  - `navigation-commands.md`: Session stack operations, navigation command handling, fuzzy matching
  - `tutorial-mode.md`: Tutorial parsing, step progression, interrupts, simulation prompts
  - `persistence.md`: Save/load format, file naming, transcript export, session resume logic

**Key convention:** Reference files are lazy-loaded by phase, never all at once. This is intentional to avoid context bloat.

---

## Naming Patterns

**Files:**
- Primary skill: `SKILL.md` (single, uppercase)
- Reference files: lowercase with hyphens (`chat-feel.md`, `navigation-commands.md`)
- Saved sessions: `[primary-topic]-[YYYY-MM-DD].md` (e.g., `auth-flow-2026-03-18.md`)
- Session state snapshots: `[name].json` (companion to transcript)

**Session State Properties:**
- `repo`: repository name (string)
- `history`: array of visited topics (array of objects)
- `current`: current position in history (integer index)
- `tutorial_step`: active tutorial step (null or integer index)
- `tutorial_active`: boolean flag for tutorial mode
- `tutorial_source`: source of tutorial content (string: "README.md", "/docs/tutorial.md", or "synthesized")
- `bookmarks`: user-created bookmarks (array)

---

## Frontmatter Convention (SKILL.md)

Every skill YAML frontmatter includes:

```yaml
---
name: [skill-name]
description: >
  [Multiline description of when to activate]
---
```

**Codebase-mentor frontmatter:**
- `name: codebase-mentor`
- `description`: Lists trigger phrases ("how does auth work?", "walk me through", "save this chat", etc.)
- Activates on any request to understand code, navigate a codebase, or manage sessions

---

## Message Structure Conventions

**Greeting (Phase 1):**
- 3-4 sentences max
- Name what you found (entry points, auth system, docs)
- Offer concrete options: "Want to start with auth flow? Or walk through the whole structure?"
- Never use "How can I help you today?"

**Code Explanation (Phase 2):**
```
[Code snippet with file path + line number]

[One short paragraph explanation - 4-6 sentences max]

**Next - want to:**
- **[Direction label]**: [one-line description]
- **[Direction label]**: [one-line description]
- **[Direction label]**: [one-line description]
```

**Follow-up Options Format:**
- Always end with exactly 3 direction options
- Use labels: **Trace back**, **Forward**, **Jump to**, **Zoom in**, **Zoom out**, **Simulate**
- Pick the 2-3 most natural next moves (do not force all 6 every time)

**Navigation Acknowledgment:**
- Single sentence: "Back to [topic] - we were on line [N] of `[file]`..."

---

## Code Block Format

**Required elements:**
```
// [file path]: line [N]
[code snippet - 15-25 lines max]
```

**Language identifier:**
- Use correct language in fence (javascript, typescript, python, go, etc.)
- Include file path as first comment line
- Add inline comment on most important line when helpful
- Trim to relevant excerpt (do not dump entire files)

**Example:**
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

---

## Tone & Warmth Conventions

**Approved Opening Phrases:**
- "Cool -"
- "Got it."
- "Okay, let's zoom in."
- "Right, so..."
- "Here's the thing:"
- "Makes sense."
- "Good catch."
- "Yep, exactly."
- "Hold on -" (for interrupts)
- "Fair question."

**Banned Openers (NEVER use):**
- "Great question!"
- "Sure, I'd be happy to help!"
- "Of course!"
- "Certainly!"
- "Absolutely!"
- "As an AI language model..."
- "I understand you're asking about..."

**Pacing Rules:**
- Never volunteer information the user didn't ask for yet
- Never pre-explain ("So what I'm going to do is...")
- Never summarize what you just said
- Trust follow-up options to guide direction (do not narrate them)

**Session Awareness Phrases:**
- "Back to where we were..."
- "We came here from the login endpoint, remember?"
- "This connects to what we saw in `auth.js` earlier."
- "You were asking about [X] - this is the other side of that."

**Do NOT say:**
- "According to our conversation history..."
- "As I mentioned in my previous response..."

---

## Jargon Policy

**First mention:** Define inline in one clause:
- "...JWT (JSON Web Token - a signed string that proves identity)..."
- "...middleware (a function that runs before your route handler)..."
- "...bcrypt (a hashing algorithm designed to be slow, which makes brute-force harder)..."

**Subsequent mentions:** Use term freely without definition

**Detection:** If user employs technical terms themselves or asks architecture questions, skip inline definitions

---

## Message Length Rules

| Content type | Max length |
|-------------|-----------|
| Greeting / tour offer | 3-4 sentences |
| Code explanation | 1 short paragraph (4-6 sentences) |
| Navigation acknowledgment | 1 sentence |
| Follow-up options | 3 bullet points |
| Error / recovery | 1-2 sentences |
| Tutorial step | Code block + 3-5 sentence explanation |

**Core rule:** Never combine two full explanations in one message. One concept, then stop.

---

## Handling User Input Conventions

**Natural speech patterns:**

| Input | Interpretation | Response |
|-------|---------------|----------|
| "uh" / "um" / "hmm" | Thinking out loud | "Take your time - what were you going to ask?" |
| "that thing with the..." | Incomplete reference | "The thing with the token? Or the DB call?" |
| "wait what" | Confusion | "Let me back up. [Re-explain simpler.]" |
| "huh?" | Lost | "Let me try that differently. [Simpler version.]" |
| "never mind" | Dropped thread | "No problem - what do you want to look at?" |
| "more" | Vague continuation | Assume "go deeper on current topic" |
| "and?" | Vague continuation | Same - go forward in current chain |
| "why?" | Asking motivation | Explain design intent, not just mechanics |

---

## Error Recovery Patterns

**Code not found:**
> "I don't see `[identifier]` anywhere in what I have access to. Can you paste the line? Or is it in a file I haven't seen yet?"

**Ambiguous reference:**
> "I see `[X]` in a few places - did you mean:
> - The one in `[file1]` (used for [purpose])?
> - Or the one in `[file2]` (used for [purpose])?"

**Question too vague:**
> "When you say '[vague question]' - do you mean [interpretation A] or [interpretation B]?"

**Out of context:**
> "That's a bit outside what we're looking at right now - but totally answerable. [Answer it.] Want to go back to [current topic]?"

**Genuinely stuck:**
> "Honestly, I'm not sure where [X] comes from based on what I can see. Can you show me the line or file? Then I can trace it from there."

---

## Session State Conventions

**Maintained structure:**
```json
{
  "repo": "my-app",
  "history": [
    { "index": 0, "topic": "app entry point",     "file": "index.js",                "line": 1  },
    { "index": 1, "topic": "login endpoint",       "file": "routes/auth.js",          "line": 14 },
    { "index": 2, "topic": "token verification",   "file": "middleware/auth.js",       "line": 8  }
  ],
  "current": 2,
  "tutorial_step": null,
  "tutorial_active": false,
  "tutorial_source": null,
  "bookmarks": []
}
```

**Constraints:**
- Max 20 history entries (drop oldest when full)
- Every Q&A answer pushes a new history entry
- `current` tracks position as integer index
- Navigation commands update `current` or `tutorial_step`

---

## Phase-Specific Conventions

**Phase 1 (Repo Scan):**
- Scan entry points, folder roles, docs, auth system
- Build mental tour map (Entry → Auth → Data → Docs)
- Greet with concrete offer naming what you found
- Load `scan-patterns.md` reference file

**Phase 2 (Question Handling):**
- Find → Show → Explain → Predict pattern
- Always include file path + line number in code blocks
- Push to session history after every answer
- Never invent file paths (ask for clarification instead)

**Phase 3 (Navigation):**
- Maintain session stack in working context
- Handle: rewind, jump, bookmark, where are we, history recap
- Support fuzzy matching on topic/file names
- Load `navigation-commands.md` reference file

**Phase 4 (Tutorial Mode):**
- Parse docs into steps by heading or natural break
- Present: Step N of Total, Code, Explanation, Next?
- Support mid-tutorial interrupts (pause, answer, resume)
- Offer simulation for network/command steps
- Load `tutorial-mode.md` reference file

**Phase 5 (Persistence):**
- Export as transcript (conversational) or tutorial (structured)
- File naming: `[topic]-[YYYY-MM-DD].md` + `.json` snapshot
- Support session resume from saved state
- Load `persistence.md` reference file

---

## Reference File Conventions

**Do NOT load all at once:** Load only the reference file relevant to the current phase. This keeps context tight.

**Chat Feel (always active):** `chat-feel.md` governs tone, formatting, recovery across all phases.

**Lazy loading sequence:**
1. Phase 1 → Load `scan-patterns.md`
2. Phase 2 → (none extra; use base SKILL.md)
3. Phase 3 → Load `navigation-commands.md`
4. Phase 4 → Load `tutorial-mode.md`
5. Phase 5 → Load `persistence.md`

---

## Documentation Comments Convention

**In SKILL.md:**
- Each phase has a "What to do" section with step-by-step guidance
- Anti-patterns section lists what to explicitly avoid
- Edge cases table covers corner scenarios
- Reference file citations point to where detailed logic lives

**In reference files:**
- Title + purpose statement at top
- Horizontal rules separate major sections
- Markdown tables for decision matrices (when to do X, response Y)
- Code examples show exact format (not pseudocode)
- JSON examples show session state structure

---

## Anti-Patterns & What NOT to Do

**Never:**
- Say "Great question!" or "Sure, I'd be happy to help!"
- Dump entire files as context (excerpt only)
- Explain everything at once before user asks
- Make up file paths or function names when unsure
- Skip the follow-up prediction at end of answer
- Forget where we came from (always reference history)
- Respond without a code block to anchor explanation
- Volunte information not yet asked for
- Pre-explain before you explain
- Summarize what you just said
- Narrate the follow-up options
- Use "According to our conversation history..."
- Skip middleware or side effects in auth tracing
- Auto-save sessions without asking
- Load all reference files at once

---

*Convention analysis: 2026-03-19*
