# Testing Patterns

**Analysis Date:** 2026-03-19

## Overview

The codebase-mentor project is a **markdown-based Claude skill**, not a traditional software project with a test suite. There are no unit tests, integration tests, or automated test runners (no Jest, Vitest, pytest, etc.). Instead, the project uses **manual validation patterns**, **simulation prompts**, and **conversational testing** embedded in the reference files and skill logic.

Testing happens through:
1. **Behavioral specification** in markdown (what the skill does)
2. **Example walkthroughs** in reference files (how it should behave)
3. **Edge case handling** (explicit case tables)
4. **Simulation patterns** for HTTP and shell commands
5. **User conversation simulation** for tutorial mode

---

## Testing Philosophy

**No Test Framework**

This skill has no testing infrastructure (no test runners, fixtures, or CI test jobs). The skill's correctness is validated by:
- Adherence to markdown specification
- Proper example format in code blocks
- Correct session state structure (JSON)
- Handling of edge cases listed in tables
- Simulation prompts for interactive features

**Testing by Specification**

Each reference file acts as a specification:
- `chat-feel.md` specifies tone and recovery patterns
- `scan-patterns.md` specifies entry point detection heuristics
- `navigation-commands.md` specifies session stack operations
- `tutorial-mode.md` specifies step parsing and progression
- `persistence.md` specifies file format and resume logic

**Manual Validation Approach**

When Claude uses this skill, validation happens through:
- User feedback ("that makes sense" vs "that's confusing")
- Tracing through the logic yourself to verify correctness
- Testing recovery patterns by intentionally asking vague questions
- Simulating navigation commands (rewind, jump, bookmark)
- Walking through tutorial mode step progression

---

## Specification-Driven Testing

### Test Case Structure

Instead of unit tests, the skill defines test scenarios as **tables and examples** in markdown.

**Example: Chat Feel Recovery Patterns**

Location: `references/chat-feel.md`

```markdown
## Handling Natural Speech

Users will not always ask clean questions. Handle gracefully:

| Input | Interpretation | Response |
|-------|---------------|----------|
| "uh" / "um" / "hmm" | Thinking out loud | "Take your time - what were you going to ask?" |
| "that thing with the..." | Incomplete reference | "The thing with the token? Or the DB call?" |
| "wait what" | Confusion | "Let me back up. [Re-explain simpler.]" |
```

**How to test:** When a user says "uh" or "um", verify the skill responds with "Take your time..." rather than continuing.

---

### Entry Point Detection Specification

Location: `references/scan-patterns.md: 7-40`

**JavaScript/TypeScript heuristics:**
```markdown
### JavaScript / TypeScript
- Primary: `index.js`, `index.ts`, `server.js`, `server.ts`, `app.js`, `app.ts`
- Framework-specific:
  - Express/Fastify: look for `app.listen(` or `server.listen(`
  - Next.js: `pages/_app.tsx`, `app/layout.tsx`
  - NestJS: `main.ts` with `NestFactory.create(`
- Fallback: `"main"` field in `package.json`
```

**How to test:**
1. Scan a repo with Express.js
2. Verify the skill looks for `app.listen(` in `index.js`, `app.js`, or `server.js`
3. Verify it offers the correct entry point in the greeting

---

### Auth System Detection Specification

Location: `references/scan-patterns.md: 62-86`

**JWT detection:**
```markdown
### JWT
- `jwt.sign(`, `jwt.verify(`, `jsonwebtoken`, `jose`, `PyJWT`
- Note the secret source: `process.env.JWT_SECRET`, `settings.SECRET_KEY`
```

**How to test:**
1. Scan a repo with `const token = jwt.sign(...)`
2. Verify the skill identifies JWT-based auth
3. Verify it traces the secret from environment

---

## Session State Testing

### Session Stack Structure Validation

Location: `references/navigation-commands.md: 7-25`

**Expected structure:**
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
  "bookmarks": []
}
```

**What to validate:**
- `history` is an array of objects with `index`, `topic`, `file`, `line`
- `current` is an integer (0 ≤ current < history.length)
- Max 20 history entries enforced
- `tutorial_step` is null or integer

**How to test:**
1. After 3 Q&A answers, verify history has 3 entries
2. Verify `current` tracks position correctly
3. Verify `index` field matches position in array
4. Add 25 entries and verify oldest 5 are dropped

---

## Navigation Command Testing

### Rewind Command Specification

Location: `references/navigation-commands.md: 31-38`

**Specification:**
```markdown
### "rewind" / "go back" / "back up"

- Decrement `current` by 1
- Load the topic at new `current`
- Acknowledge:
  > "Back to [topic] - we were on line [line] of `[file]`..."
- If already at 0:
  > "We're at the beginning - that's where we started with [first topic]."
```

**How to test:**
1. Build a history of 3 entries, set `current = 2`
2. User says "rewind"
3. Verify `current` becomes 1
4. Verify acknowledgment includes correct topic/file/line
5. Test edge case: `current = 0`, user says "rewind"
6. Verify response says "We're at the beginning..."

### Fuzzy Matching Specification

Location: `references/navigation-commands.md: 106-118`

**Specification:**
```markdown
## Fuzzy Matching Rules

When user says "jump to auth" and you have these history entries:
- "login endpoint" (routes/auth.js)
- "token verification" (middleware/auth.js)
- "profile controller"

Match strategy:
1. Exact topic name match
2. File name contains keyword ("auth" matches both above)
3. If multiple matches: "I see a few auth-related spots - did you mean login or token verification?"
```

**How to test:**
1. Create history with auth-related entries
2. User says "jump to auth"
3. Verify skill detects 2 matches
4. Verify skill asks for clarification (does NOT silently pick one)
5. Test exact match: user says "jump to login endpoint"
6. Verify skill navigates directly without asking

---

## Tutorial Mode Testing

### Step Parsing Specification

Location: `references/tutorial-mode.md: 18-49`

**Chunk by heading:**
```markdown
### Chunk by heading

Split on `##` or `###` headings. Each heading = one step candidate.

Example:
## Step 1: Install dependencies    <- Step 1
## Step 2: Set up environment      <- Step 2
## Step 3: Run the dev server      <- Step 3
```

**How to test:**
1. Create a README with 5 sections separated by `##` headings
2. User says "tutorial mode"
3. Verify skill parses 5 steps (or presents "Step 1 of 5")
4. Verify step numbering starts at 1
5. Test with no headings: use blank lines + numbered lists
6. Verify correct chunking without heading anchors

### Step Presentation Format Specification

Location: `references/tutorial-mode.md: 53-80`

**Required format:**
```
**Step [N] of [total]: [Title]**

[Code snippet if present]

[Plain-English explanation - 2-4 sentences max]

Run it? Or skip to step [N+1]?
```

**How to test:**
1. Activate tutorial mode
2. Verify first step shows: "**Step 1 of 5: [title]**"
3. Verify code block has file path + line number
4. Verify explanation is 2-4 sentences
5. Verify prompt offers "Run it? Or skip to step 2?"
6. Verify skipping advances to next step
7. Verify "run it" confirms and advances

### Mid-Tutorial Interrupt Specification

Location: `references/tutorial-mode.md: 98-126`

**Specification for "Hold On" pattern:**
```markdown
## "Hold On" Interrupt Pattern

When user says "hold on", "wait", "pause", "what is [X]?", or "explain that":

Response format:
```
Hold on - good catch.

[Code snippet of the thing they asked about]

[Explanation]

Okay - back to step [N]? Or keep pulling on this thread?
```

**How to test:**
1. During step 3 of tutorial, user says "what is JWT?"
2. Verify skill pauses tutorial
3. Verify skill shows code and explanation
4. Verify skill offers: "back to step 3? Or keep digging?"
5. User says "back to step 3"
6. Verify skill resumes at step 3 (does not skip ahead)

---

## Simulation Prompts Testing

### HTTP Request Simulation Specification

Location: `references/tutorial-mode.md: 129-149`

**Specification:**
```markdown
### HTTP request simulation
If step says "hit the `/login` endpoint":
> "Want me to simulate that request? I'll show you what goes in and what
> comes back."

Show simulated request + expected response:
```
POST /login
Content-Type: application/json

{ "email": "test@example.com", "password": "secret" }

---

Expected response:
{ "token": "eyJhbGci..." }
```

**How to test:**
1. Create tutorial with step: "POST to /login with email and password"
2. Verify skill detects network step and offers simulation
3. User says "yes" or "simulate"
4. Verify skill shows: request method, headers, body, expected response
5. Verify response is realistic (not made-up)

### Shell Command Simulation Specification

Location: `references/tutorial-mode.md: 151-154`

**Specification:**
```markdown
### Shell command simulation
If step says "run `npm install`":
> "Running that would install these key packages: express, jsonwebtoken,
> bcrypt, dotenv. Want to see what each one does? Or skip to the next step."
```

**How to test:**
1. Create tutorial with step: "Run npm install"
2. Verify skill offers simulation
3. Verify skill lists actual packages from package.json (if present)
4. Verify skill explains what each package does
5. Verify skill offers follow-up options

---

## Persistence Testing

### File Naming Convention Validation

Location: `references/persistence.md: 22-34`

**Expected format:**
```
[primary-topic]-[YYYY-MM-DD].md
```

**Examples:**
- `auth-flow-2026-03-18.md`
- `login-walkthrough-2026-03-18.md`

**How to test:**
1. User says "save this as auth flow"
2. Verify file is named: `auth-flow-2026-03-19.md` (today's date)
3. User says "save as my-tutorial"
4. Verify file is named: `my-tutorial.md` (user-provided name)
5. Verify both formats include `.md` extension

### Transcript Export Format Validation

Location: `references/persistence.md: 41-87`

**Required sections:**
```markdown
# [Topic] - [Date]

**Repo:** [repo name]
**Session date:** [YYYY-MM-DD]
**Topics covered:** [comma-separated list from history stack]

---

## [Topic from history]

**You asked:** [question or context]

**Code:**
```[language]
// [file]: line [N]
[code snippet]
```

**Explanation:** [explanation from conversation]

---

*Saved by Codebase Mentor*
```

**How to test:**
1. Conduct 3-answer conversation
2. User says "save this"
3. Verify exported file has all required sections
4. Verify "Topics covered" lists all 3 topics from history
5. Verify code blocks have file paths + line numbers
6. Verify explanations match what was said
7. Verify file ends with "*Saved by Codebase Mentor*"

### Session Resume Validation

Location: `references/persistence.md: 156-184`

**State snapshot format:**
```json
{
  "version": "1.0",
  "saved_at": "2026-03-18T14:32:00Z",
  "repo": "my-app",
  "primary_topic": "auth-flow",
  "history": [
    { "index": 0, "topic": "login endpoint",     "file": "routes/auth.js",         "line": 14 },
    { "index": 1, "topic": "token verification",  "file": "middleware/auth.js",      "line": 8  }
  ],
  "current": 1,
  "tutorial_step": null
}
```

**How to test:**
1. Save a session (generates `.md` + `.json`)
2. Verify `.json` has all required fields
3. Close skill and restart
4. Load same repo
5. Verify skill offers: "I see we left off on **token verification**..."
6. User says "pick up"
7. Verify history is restored
8. Verify `current` is set to 1
9. Verify skill shows last topic's code + explanation

---

## Edge Case Validation

### Repo Scanning Edge Cases

Location: `references/skill.md: 276-287`

**Test scenarios:**

| Situation | Validation |
|-----------|-----------|
| Huge repo (100+ files) | Verify skill offers to focus on specific folder, not summarize all |
| No entry point found | Verify skill asks user to point at main file |
| Ambiguous identifier | Verify skill shows all occurrences and asks for clarification |
| Code not found | Verify skill asks for paste or suggests alternative |
| Vague question | Verify skill asks for interpretation options |
| User says "uh" / "um" | Verify skill waits patiently, doesn't barrel ahead |
| User pastes raw code | Verify skill treats as micro-repo, scans it |
| No docs exist | Verify skill synthesizes tour from code structure |

**How to test each:**
1. Huge repo → offer "want to focus on auth folder?"
2. No entry → ask "can you point me at the main file?"
3. Ambiguous → list all matches, ask which one
4. Not found → ask for paste
5. Vague → ask for interpretation
6. Natural hesitation → "Take your time - what were you going to ask?"
7. Code paste → treat as mini-repo, greet with what you found
8. No docs → "I can build one from the code. Start with login?"

---

## Manual Testing Checklist

Use this checklist to validate the skill before deployment:

**Phase 1 - Repo Scan:**
- [ ] Correctly identifies entry point for 5+ different project types
- [ ] Detects and names auth system (JWT, session, OAuth)
- [ ] Identifies DB/data layer
- [ ] Finds README or tutorial docs
- [ ] Greets with concrete offer, not generic help message

**Phase 2 - Question Handling:**
- [ ] Shows code with file path + line number
- [ ] Explains in 1 short paragraph (4-6 sentences)
- [ ] Ends with 3 smart follow-up options
- [ ] Pushes to session history
- [ ] Never invents file paths

**Phase 3 - Navigation:**
- [ ] Rewind decrements `current`
- [ ] Jump/fuzzy matching surfaces ambiguity
- [ ] Bookmarks save and load
- [ ] History recap shows last 5 topics
- [ ] All navigation commands acknowledge with file + line

**Phase 4 - Tutorial Mode:**
- [ ] Steps parse correctly from headings or breaks
- [ ] Each step shows as "Step N of Total"
- [ ] Explains 2-4 sentences per step
- [ ] Handles interrupts (pause, answer, resume)
- [ ] Simulation prompts for HTTP/shell commands

**Phase 5 - Persistence:**
- [ ] Session saves with correct filename format
- [ ] Exported markdown has all topics from history
- [ ] Code blocks have file paths + line numbers
- [ ] Resume restores history correctly
- [ ] JSON snapshot includes all state fields

**Tone & Recovery:**
- [ ] Uses approved warmth phrases
- [ ] Never uses banned openers
- [ ] Handles vague input gracefully
- [ ] Defines jargon on first use
- [ ] Recovery patterns match spec

---

## What Is NOT Tested

This markdown skill does not have:
- Unit tests for functions (there are no functions)
- Integration tests (no external APIs to test with)
- Automated test runs (no CI pipeline)
- Code coverage reports
- Performance benchmarks
- Load testing
- Memory profiling

Instead, validation happens through careful adherence to the markdown specification and manual walkthrough testing.

---

*Testing analysis: 2026-03-19*
