# Navigation Commands Reference

Handles Phase 3 session navigation. Read this when a user rewinds, jumps,
or asks about history.

---

## Session Stack Operations

The session stack lives in working context. Format:

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

---

## Command Handling

### "rewind" / "go back" / "back up"

- Decrement `current` by 1
- Load the topic at new `current`
- Acknowledge:
  > "Back to [topic] - we were on line [line] of `[file]`..."
- If already at 0:
  > "We're at the beginning - that's where we started with [first topic]."

### "go back two" / "back two steps" / "two back"

- Decrement `current` by 2
- Handle underflow (clamp to 0)
- Acknowledge:
  > "Rewinding two steps - back to [topic]."

### "go back [N]"

- Parse N, decrement by N, clamp to 0
- If N is very large: "That would take us before the start - going back to the beginning."

### "what were we talking about?" / "history" / "recap"

- Return last 5 topics from history (or all if < 5), most recent first:
  > "Here's where we've been:
  > 1. Profile controller (most recent)
  > 2. Token verification
  > 3. Login endpoint
  > 4. App entry point"
- Then ask: "Want to jump back to any of these?"

### "where are we?" / "what are we looking at?"

- State current position:
  > "We're on [topic] - line [line] of `[file]`."

### "jump to [topic]" / "go to [topic]"

Resolution order:
1. Check `history` for fuzzy match on topic name
2. Check docs/tutorial for a section matching the topic
3. Check repo for a file or function matching the keyword
4. If no match: "I don't have [topic] in our history - is it somewhere in the repo? Or do you mean [closest match]?"

Acknowledge jump:
> "Jumping to [topic] - [file], line [line]."
> Update `current` to matched index (or push new entry if from repo).

### "skip to [topic]" / "fast-forward to [topic]"

- Like "jump to" but implies moving forward, not back
- Same resolution order as jump
- If in tutorial mode: advance `tutorial_step` to matching step

### "start over" / "reset" / "from the top"

- Clear history, reset `current` to -1
- Re-run Phase 1 greeting with tour map
- > "Starting fresh - let me re-scan what's here..."

### "bookmark this" / "mark this"

- Add current position to `bookmarks`:
  ```json
  { "label": "token verification", "file": "middleware/auth.js", "line": 8 }
  ```
- Confirm: "Bookmarked. Say 'go to my bookmarks' to come back."

### "show my bookmarks" / "go to my bookmarks"

- List bookmarks with labels
- Let user pick by name or number

---

## Fuzzy Matching Rules

When user says "jump to auth" and you have these history entries:
- "login endpoint" (routes/auth.js)
- "token verification" (middleware/auth.js)
- "profile controller"

Match strategy:
1. Exact topic name match
2. File name contains keyword ("auth" matches both above)
3. If multiple matches: "I see a few auth-related spots - did you mean login or token verification?"

Never silently pick one when ambiguous. Always surface the choice.

---

## Edge Cases

| Situation | Response |
|-----------|----------|
| User rewinds from position 0 | "We're already at the start - that's [first topic]." |
| User jumps to something not in history or repo | "I don't see [X] in our session or the repo. Want to search for it?" |
| History is empty | "We haven't looked at anything yet - want me to start with a tour?" |
| Tutorial step + nav command conflict | Pause tutorial, handle nav, then: "Want to go back to the tutorial, or keep exploring?" |
| User says "undo" | Treat as "rewind" |
| User says "nevermind" | Stay at current position, ask: "No worries - what do you want to look at instead?" |
