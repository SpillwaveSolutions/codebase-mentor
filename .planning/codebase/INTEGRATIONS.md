# External Integrations

**Analysis Date:** 2026-03-19

## APIs & External Services

**Claude API (Native Platform):**
- Service: Claude conversational AI
- Purpose: Entire agent runtime and reasoning
- Implementation: Skill activates as response to user queries within Claude agent environment
- No explicit SDK — runs natively within Claude platform

**No third-party API integrations.**

## Data Storage

**Databases:**
- Not applicable — skill operates on in-memory session state only

**File Storage:**
- **Target Repository**: Read-only scanning of user-provided codebase
  - No modification, only introspection
  - Language-specific heuristics for entry point and structure detection
  - See `plugin/references/scan-patterns.md` for supported languages: JavaScript/TypeScript, Python, Go, Java/Kotlin, Ruby

- **Session Persistence**: Local file system (within target repo or current directory)
  - Format: Markdown (`.md`) + JSON (`.json`)
  - Location: `/docs/agent/` (attempted) or current directory (fallback)
  - Naming: `[topic]-[YYYY-MM-DD].md` and companion `.json`

**Caching:**
- None — stateless between messages within single session

## Authentication & Identity

**Auth Provider:**
- Not applicable — no user authentication required
- Skill inherits Claude API authentication from platform
- No OAuth, API keys, or session tokens

## Monitoring & Observability

**Error Tracking:**
- None — errors handled inline with recovery patterns
- See `plugin/references/chat-feel.md` for recovery responses

**Logs:**
- No external logging service
- Session history maintained in-memory and optionally saved as markdown transcript
- File: `plugin/references/persistence.md` documents session save format

**Session Awareness:**
- History stack tracked in working memory (max 20 entries)
- Bookmarks supported for user-defined navigation points
- Full transcript exportable as markdown or JSON

## CI/CD & Deployment

**Hosting:**
- Claude agent platform (Anthropic)
- Distribution: Agent skill marketplace
- No self-hosted deployment required

**Version Control:**
- Git repository at `/Users/richardhightower/clients/spillwave/src/codebase-mentor/`
- No automated CI/CD pipeline defined
- Manual registration with agent platform on changes

**Skill Registration:**
- Activated by agent platform based on metadata in `plugin/SKILL.md`
- Trigger keywords: "explain this code", "walk me through", "teach me", "how does auth work?", etc.
- No deployment artifacts or build step

## Environment Configuration

**Required configuration:**
- None — skill is self-contained

**Optional configuration:**
- Language detection: Auto-detected from file extensions and heuristics
- Framework detection: Inferred from patterns (see `plugin/references/scan-patterns.md`)
- Tutorial source: Scanned for README.md or `/docs/` on first load

**No .env files or secrets required.**

## Webhooks & Callbacks

**Incoming:**
- None — skill operates in request/response conversational model only

**Outgoing:**
- None — no callbacks or asynchronous notifications
- File saves are synchronous (when user explicitly requests "save")

## Communication Patterns

**User-to-Skill:**
- Natural language queries scanned for phase triggers
- Supported commands documented in `plugin/references/navigation-commands.md`
- Examples: "rewind", "jump to X", "save this", "load session"

**Skill-to-User:**
- Conversational responses with code snippets
- Follow-up predictions for navigation
- Session state maintained across messages (single conversation)

## Data Flow

**Phase 1 - Repo Scan:**
1. User provides repo path or file tree
2. Skill scans directory structure and key files
3. Heuristics applied per `plugin/references/scan-patterns.md`
4. Tour map constructed (entry points, auth, data layer, docs)
5. Tour offered to user

**Phase 2 - Question Handling:**
1. User asks about code functionality
2. Skill searches provided repo for matching file/function/identifier
3. Code snippet extracted with file path + line number
4. Plain-English explanation generated
5. Follow-up options predicted

**Phase 3 - Navigation:**
1. User commands: rewind, jump, bookmark, etc.
2. Session stack queried/updated
3. History entry retrieved and re-shown
4. Context restored for next Q&A

**Phase 4 - Tutorial Mode:**
1. README.md or `/docs/` parsed into steps
2. Steps presented sequentially
3. User interrupts handled (pause → answer → resume)
4. Simulation prompts offered for network requests
5. Progress tracked in session state

**Phase 5 - Persistence:**
1. User requests save/export
2. Skill generates markdown transcript or tutorial format
3. Saved to local filesystem with timestamped name
4. Optional: JSON companion file for programmatic resume
5. On future load, session offer restoration

## Session State Format

```json
{
  "repo": "repository-name",
  "history": [
    { "index": 0, "topic": "topic-name", "file": "file/path", "line": 123 }
  ],
  "current": 0,
  "tutorial_active": false,
  "tutorial_step": null,
  "tutorial_total": null,
  "bookmarks": [
    { "label": "bookmark-name", "file": "file/path", "line": 123 }
  ]
}
```

**Lifecycle:**
- Created on first message of session
- Updated after each Q&A or navigation
- Persisted to disk on user request only (not auto-saved)
- Restored on next session if user loads saved file

## No Integration Points

The skill deliberately avoids external dependencies:

- No database connections
- No API calls to third-party services
- No authentication providers
- No message queues or event streaming
- No observability services (Sentry, DataDog, etc.)
- No analytics or tracking

This design maximizes reliability, latency predictability, and privacy.

---

*Integration audit: 2026-03-19*
