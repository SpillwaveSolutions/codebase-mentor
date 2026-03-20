# Tutorial Mode Reference

Handles Phase 4 tutorial parsing, step progression, interrupts, and
simulation prompts. Read this when docs exist or user asks for a walkthrough.

---

## Activation Triggers

Tutorial mode activates when:
- README.md or `/docs/*.md` contains tutorial/guide content
- User says: "walk me through", "tutorial", "teach me", "from the start",
  "step by step", "show me how to set this up"
- User is on step N and says "next" or "continue"

---

## Parsing the Tutorial Document

### Chunk by heading

Split on `##` or `###` headings. Each heading = one step candidate.

Example:
```markdown
## Step 1: Install dependencies    <- Step 1
## Step 2: Set up environment      <- Step 2
## Step 3: Run the dev server      <- Step 3
```

### Chunk by natural break (no headings)

If the doc has no headings, split on:
- Blank lines before a numbered list item (`1.`, `2.`)
- Transition phrases: "Now", "Next", "Then", "Finally"
- Code blocks (treat each code block + surrounding text as a unit)

### Build step list

```json
{
  "total_steps": 5,
  "steps": [
    { "index": 0, "title": "Install dependencies",  "content": "...", "has_code": true,  "has_command": true  },
    { "index": 1, "title": "Set up env vars",       "content": "...", "has_code": true,  "has_command": false },
    { "index": 2, "title": "Run the dev server",    "content": "...", "has_code": false, "has_command": true  }
  ]
}
```

---

## Presenting Each Step

Format every step the same way:

```
**Step [N] of [total]: [Title]**

[Code snippet if present]

[Plain-English explanation - 2-4 sentences max]

Run it? Or skip to step [N+1]?
```

Example:
```
**Step 2 of 5: Set up env vars**

// .env
DATABASE_URL=postgres://localhost:5432/myapp
JWT_SECRET=supersecret

Copy this into a `.env` file at the root. The app reads these at startup
via `dotenv`-`process.env.DATABASE_URL` becomes your DB connection string.

Run it? Or skip to step 3?
```

---

## Step Progression

Track `tutorial_step` in session state (index into step list).

| User says | Action |
|-----------|--------|
| "next" / "continue" / "step 3" | Advance to next step or named step |
| "skip" / "skip this" | Advance without explanation |
| "run it" / "done" | Confirm, advance, note in history |
| "back" / "previous step" | Decrement tutorial_step |
| "where am I?" | "You're on step [N] of [total]: [title]" |
| "show all steps" | List all step titles with current marked |

---

## Mid-Tutorial Interrupts

When user goes off-script mid-tutorial (asks a question, rewinds, etc.):

1. **Pause** the tutorial: "Hold on - let me answer that."
2. **Answer** the question fully (Phase 2 flow).
3. **Offer resume**: "Okay - back to step [N], or want to keep digging here?"
4. On resume, re-state what step we're on:
   > "Back to step 3 - we were setting up the DB connection."

Do NOT just barrel through the tutorial ignoring questions.

---

## "Hold On" Interrupt Pattern

When user says "hold on", "wait", "pause", "what is [X]?", or "explain that":

Response format:
```
Hold on - good catch.

[Code snippet of the thing they asked about]

[Explanation]

Okay - back to step [N]? Or keep pulling on this thread?
```

---

## Simulation Prompts

When a tutorial step involves a network request or command:

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

### Shell command simulation
If step says "run `npm install`":
> "Running that would install these key packages: express, jsonwebtoken,
> bcrypt, dotenv. Want to see what each one does? Or skip to the next step."

---

## Synthesized Tutorial (No Docs Fallback)

When no tutorial docs exist, offer to build one:
> "No tutorial here - but I can build one from the code. I'll trace the
> main flow and walk you through it step by step. Want to start with login?"

Build steps from code, not from docs:
1. Find the most natural starting point (entry or login)
2. Trace the happy path through the app
3. Present each function/route as a "step"
4. Number them and track progress the same way as doc-based tutorials

Synthesized step format:
```
**Step [N]: [What this code does in plain English]**

// [file]: line [N]
[code snippet]

[Explanation]

Want to keep going? Or jump somewhere specific?
```

---

## Tutorial State in Session

```json
{
  "tutorial_active": true,
  "tutorial_source": "README.md",
  "tutorial_step": 2,
  "tutorial_total": 5,
  "tutorial_paused": false,
  "synthesized": false
}
```

On session save, include tutorial progress so it can be resumed.
