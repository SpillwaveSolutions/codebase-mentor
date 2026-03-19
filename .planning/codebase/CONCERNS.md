# Codebase Concerns

**Analysis Date:** 2026-03-19

## Tech Debt

**Session State Consistency:**
- Issue: Session stack format defined in multiple reference files with potential inconsistencies
- Files: `plugin/SKILL.md`, `plugin/references/navigation-commands.md`, `plugin/references/persistence.md`
- Impact: Implementation of session management could diverge based on which reference file is read. The core definition in SKILL.md (line 167-176) includes `tutorial_step` and `current`, while navigation-commands.md (line 12-24) also adds `bookmarks` array not mentioned in main spec
- Fix approach: Consolidate session state schema into single canonical definition. Create a strict JSON schema file that all phases reference

**Reference File Load-on-Demand Model:**
- Issue: Five reference files are designed to load conditionally during runtime, but no validation mechanism ensures completeness
- Files: `plugin/SKILL.md`, all files in `plugin/references/`
- Impact: If a phase triggers but its corresponding reference file is missing/corrupt, the agent degrades gracefully but without explicit error handling. No fallback content exists
- Fix approach: Add validation step in SKILL.md that pre-checks reference file existence at skill activation. Include minimal inline guidance for each phase as fallback

**Jargon Definition Persistence:**
- Issue: `chat-feel.md` defines inline jargon definition rule (line 154-166) as "first use only", but no state tracking mechanism to remember which terms have been defined
- Files: `plugin/references/chat-feel.md`
- Impact: In long conversations or resume scenarios, terms might be re-explained unnecessarily or conversely skipped when they should be explained to a fresh audience
- Fix approach: Add guidance for detecting user expertise level and maintaining term definition state per session

## Known Issues

**Bookmarks Not Mentioned in Core Flow:**
- Problem: Bookmarks are defined in `navigation-commands.md` (line 91-102) but never mentioned in main SKILL.md or expected session format
- Files: `plugin/SKILL.md` (line 167-176), `plugin/references/navigation-commands.md` (line 23, 93-102)
- Trigger: User tries to bookmark content before learning the feature exists
- Workaround: None - feature is hidden from user. Bookmarks are implemented but not advertised

**Ambiguous Edge Case Handling:**
- Problem: Multiple edge cases defined across files with overlapping scenarios
- Files: `plugin/SKILL.md` (line 276-287), `plugin/references/navigation-commands.md` (line 122-132)
- Trigger: Same situation (e.g., user asks about something not in history) could match multiple edge case patterns
- Workaround: Patterns include "never silently pick one when ambiguous" but don't specify resolution order for conflicting rules

## Fragile Areas

**Tutorial Chunk Parsing Logic:**
- Files: `plugin/references/tutorial-mode.md` (line 18-48)
- Why fragile: Parsing depends on document structure heuristics - splitting on `##`/`###` headings, blank lines, numbered lists, or transition phrases. No formal grammar defined. A README with mixed formats could be mis-parsed
- Safe modification: Add explicit examples of well-formed tutorial documents. Consider requiring `##` heading convention rather than supporting ad-hoc parsing
- Test coverage: Logic is prescriptive but not testable in isolation

**Fuzzy Matching in Jump Commands:**
- Files: `plugin/references/navigation-commands.md` (line 106-118)
- Why fragile: Three-tier matching (exact match → filename contains keyword → file/function search) could produce false positives or require multiple clarification prompts
- Safe modification: Add examples of ambiguous scenarios and their resolution. Consider requiring explicit file paths in jump commands for long histories
- Test coverage: No examples of failure cases or conflicting matches

**Session Resume from Partial JSON:**
- Files: `plugin/references/persistence.md` (line 155-183)
- Why fragile: Session restore logic (line 156-169) does not validate saved JSON schema. Missing fields could cause undefined behavior. No validation of file paths or line numbers still being valid in repo
- Safe modification: Add JSON schema validation before restore. Document which fields are required vs optional
- Test coverage: No error recovery paths for corrupt/stale session files

**Message Length Enforcement:**
- Files: `plugin/references/chat-feel.md` (line 50-60)
- Why fragile: Length constraints ("3-4 sentences", "1 short paragraph", "15-25 lines max") are guidelines, not enforced. No mechanism to ensure compliance during generation
- Safe modification: Define measurable metrics (word count, sentence count, line count) instead of prose descriptions
- Test coverage: Cannot verify compliance without implementing counters

## Scaling Limits

**Session History Size:**
- Current capacity: Max 20 entries with oldest dropped when full
- Files: `plugin/SKILL.md` (line 179)
- Limit: Long exploratory sessions (>20 topics) will lose early context
- Scaling path: Implement hierarchical history (group related topics) or persistent history file alongside current session state

**Repository Size Threshold:**
- Current capacity: ~100 files before triggering "too big" response
- Files: `plugin/references/scan-patterns.md` (line 142-149)
- Limit: Between 50-200 files the experience degrades (unclear when to focus vs when to explore broadly)
- Scaling path: Implement heuristic folder ranking by activity/imports to suggest focus areas without arbitrary size limits

**Follow-Up Options Clarity:**
- Current capacity: 2-3 options per response, using 6 possible direction labels
- Files: `plugin/references/chat-feel.md` (line 100-108)
- Limit: Doesn't specify how to choose between options when all could be valid. 6 label types means some responses may force unnatural options
- Scaling path: Implement option scoring based on conversation context rather than picking arbitrary 2-3

## Missing Critical Features

**No Explicit Syntax Highlighting Language Detection:**
- Problem: Code blocks format includes language identifier (javascript, python) but scan-patterns.md doesn't specify how to detect it for unknown files
- Files: `plugin/references/scan-patterns.md`, `plugin/references/chat-feel.md` (line 72)
- Impact: Fallback language for ambiguous file types not documented
- Needed: Guidance on language inference when file extension is unavailable

**No Resume Conflict Handling:**
- Problem: If a user loads a saved session but the file has been moved/deleted since save, only a generic "not found" error exists
- Files: `plugin/references/persistence.md` (line 175-183)
- Impact: User loses context and must re-navigate from scratch
- Needed: Partial recovery strategy - search for file by pattern or suggest closest alternatives

**No Monorepo Package Selection Persistence:**
- Problem: In monorepo projects, user picks which package to explore in Phase 1, but this choice is not persisted in session state
- Files: `plugin/references/scan-patterns.md` (line 119-128), `plugin/SKILL.md` (line 167-176)
- Impact: If session resumes, which monorepo package should be active is ambiguous
- Needed: Add `selected_package` field to session state schema

**No Tutorial Step Bookmarking:**
- Problem: User can bookmark code locations but cannot bookmark tutorial progress
- Files: `plugin/references/persistence.md`, `plugin/references/tutorial-mode.md`
- Impact: Mid-tutorial sessions cannot be saved and resumed at the exact step
- Needed: Link session state `tutorial_step` with bookmark/resume functionality

## Performance Bottlenecks

**Scan Pattern Matching on Large Repos:**
- Problem: Scanning for entry points, folder roles, auth patterns, and DB patterns requires regex/keyword matching across potentially thousands of files
- Files: `plugin/references/scan-patterns.md` (line 7-104)
- Cause: No indexing or early termination strategies defined. Matching is greedy (check all files before deciding)
- Improvement path: Implement early exit on first match for common patterns. Use file extension filtering before content scanning

**Fuzzy Matching Latency:**
- Problem: Jump to topic requires searching history, then docs, then repo for matches
- Files: `plugin/references/navigation-commands.md` (line 68-77)
- Cause: Three sequential searches with potential string similarity operations on long history
- Improvement path: Pre-index history topics on session start. Use fast exact-match before fuzzy-match

## Security Considerations

**No Input Validation for Session File Names:**
- Risk: User-provided session file names (persistence.md line 34) passed directly to file system without sanitization
- Files: `plugin/references/persistence.md` (line 34)
- Current mitigation: Directory scoping to `/docs/agent/` provides some isolation, but path traversal (e.g., `../../../sensitive`) could be attempted
- Recommendations: Validate file names against whitelist pattern (alphanumeric + dash + date format). Strip special characters

**Env Var and Secret Patterns in Code Display:**
- Risk: Scan patterns explicitly look for auth secrets (JWT_SECRET, API_KEY values) and file paths may contain real values
- Files: `plugin/references/scan-patterns.md` (line 62-86)
- Current mitigation: Documentation does not specify filtering, so implementation may display secrets in code blocks
- Recommendations: Add explicit guidance to mask secret values in displayed code. Never show actual API keys or tokens in explanations

**No Transcript Sanitization on Export:**
- Risk: "Save as tutorial" exports entire conversation history which may contain accidentally pasted credentials, URLs with tokens, or sensitive debugging info
- Files: `plugin/references/persistence.md` (line 41-87)
- Current mitigation: User must confirm file name before save, but content not filtered
- Recommendations: Scan exported content for common secret patterns before writing. Warn user if credentials detected

## Test Coverage Gaps

**No Validation for Cyclic Navigation:**
- What's not tested: If user jumps between topics in circular patterns (A → B → C → A), session state stays consistent
- Files: `plugin/references/navigation-commands.md`, `plugin/SKILL.md`
- Risk: Long sessions with backtracking could have position errors if bookmarks or history pointers degrade
- Priority: Medium

**No Multi-File Import Chain Tracing:**
- What's not tested: How phase 1 scan handles complex import chains (A imports B imports C imports D)
- Files: `plugin/references/scan-patterns.md`
- Risk: Entry point detection may pick wrong file if import graph is not fully traversed
- Priority: Medium

**No Interrupted Tutorial Recovery:**
- What's not tested: Mid-tutorial interrupts that trigger phase jumps (user asks complex question, skill must restart) don't properly resume to step
- Files: `plugin/references/tutorial-mode.md` (line 98-109)
- Risk: User loses tutorial position if multiple interrupts occur in quick succession
- Priority: High

**No Edge Case Combination Testing:**
- What's not tested: How skill handles rare combinations (huge monorepo + no docs + ambiguous imports + mixed languages)
- Files: Multiple reference files
- Risk: Fallback responses may not handle stacked edge cases gracefully
- Priority: Low

---

*Concerns audit: 2026-03-19*
