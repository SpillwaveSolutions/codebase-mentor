# Persistence Reference

Handles Phase 5: saving sessions, exporting transcripts, converting to
tutorials, and resuming past sessions. Read this when user says "save",
"export", "load session", or at natural session end.

---

## Save Triggers

| User says | Action |
|-----------|--------|
| "save this" / "save the chat" | Export full transcript as markdown |
| "export as tutorial" / "save as tutorial" | Convert to structured tutorial format |
| "make this a doc" | Same as "save this" |
| "save as [name]" | Use user-provided name for the file |
| "load [session name]" | Restore a previous session |
| "what sessions do I have?" | List available saved sessions |

---

## File Naming Convention

Default name format:
```
[primary-topic]-[YYYY-MM-DD].md
```

Examples:
- `auth-flow-2026-03-18.md`
- `login-walkthrough-2026-03-18.md`
- `onboarding-tutorial-2026-03-18.md`

If user provides a name: use it verbatim + `.md` extension.

Save location: `/docs/agent/` inside the repo (if writable), otherwise
offer as a download / output to current directory.

---

## Transcript Export Format

Full session save (conversational format):

```markdown
# [Topic] - [Date]

**Repo:** [repo name]
**Session date:** [YYYY-MM-DD]
**Topics covered:** [comma-separated list from history stack]

---

## Auth Flow

**You asked:** How does auth work?

**Code:**
```[language]
// src/routes/auth.js: line 14
app.post('/login', async (req, res) => {
  ...
});
```

**Explanation:** Email + password come in, we look up the user in the DB,
bcrypt checks the password, then we sign a JWT with the user ID.

---

## Token Verification

**You asked:** Trace the token check.

**Code:**
```[language]
// src/middleware/auth.js: line 8
const verifyToken = (req, res, next) => { ... };
```

**Explanation:** Pulls the Bearer token, verifies it against the secret,
attaches decoded payload to req.user.

---

*Saved by Codebase Mentor*
```

---

## Tutorial Export Format

When user says "save as tutorial" - strip conversation, add structure:

```markdown
# [Topic] Tutorial

**Generated from:** [repo name]
**Date:** [YYYY-MM-DD]

---

## Step 1: [Topic from first history entry]

```[language]
// [file]: line [N]
[code snippet]
```

**What's happening:** [Plain-English explanation]

**What to notice:** [Key insight or gotcha]

---

## Step 2: [Topic from second history entry]

...

---

## Summary

You've traced through:
- [topic 1] - how [one-line summary]
- [topic 2] - how [one-line summary]

**Next steps:** [suggestions for what to explore next]
```

---

## Session State Snapshot (JSON)

For programmatic resume, also save a `.json` companion file:

```json
{
  "version": "1.0",
  "saved_at": "2026-03-18T14:32:00Z",
  "repo": "my-app",
  "primary_topic": "auth-flow",
  "history": [
    { "index": 0, "topic": "login endpoint",     "file": "routes/auth.js",         "line": 14 },
    { "index": 1, "topic": "token verification",  "file": "middleware/auth.js",      "line": 8  },
    { "index": 2, "topic": "profile controller",  "file": "controllers/profile.js", "line": 22 }
  ],
  "current": 2,
  "tutorial_step": null,
  "bookmarks": []
}
```

---

## Session Resume Logic

### On next load

When the skill activates and a `.json` session file exists for this repo:

> "Hey - I see we left off on **token verification** in `middleware/auth.js`.
> Want to pick up from there? Or start fresh?"

If user says "pick up" / "continue" / "yes":
- Restore history stack from JSON
- Set `current` to saved value
- Re-show the last topic's code + explanation
- Offer next predictions based on restored context

If user says "start fresh" / "no":
- Ignore saved session
- Run Phase 1 scan as normal

### "load [session name]" command

1. Look for `[session-name].json` in `/docs/agent/`
2. If found: restore and confirm:
   > "Loaded `auth-flow-2026-03-18`. We were on profile controller.
   > Want to jump back in?"
3. If not found:
   > "I don't see a session called '[name]' - do you have the file somewhere?
   > Or did you mean [closest match]?"

---

## Auto-Save Prompt

Offer auto-save at natural session end (when user says "thanks", "done",
"that's all", or goes quiet after a long session):

> "Want me to save this session? I'll call it `auth-flow-2026-03-18.md`.
> Or say 'save as tutorial' to get a cleaner step-by-step version."

Do not auto-save without asking. Always confirm file name before writing.
