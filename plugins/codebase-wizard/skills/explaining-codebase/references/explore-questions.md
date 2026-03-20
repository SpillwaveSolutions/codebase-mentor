# Explore Mode — Tour Structure

Load this file when `--explore` mode activates. Contains the
learning-order tour steps and follow-up logic for Explore mode.

## When to Load

Load after repo scan completes. Do not load during Describe or
File mode.

## Opening

After scan, greet with what you found — framed for a newcomer:

> "Okay — let me walk you through this like you've never seen it
>  before. I'll go in the order that makes sense to learn it, not
>  the order the files happen to be in. Say 'next' to advance,
>  or ask anything at any point."

## Tour Steps (Learning Order)

Work through these in order. At each step: apply the full Answer
Loop (show code block with anchor first, then explain, then show
connections, then predict next).

### Step 1: What the App Does

Show the README intro or the main entry point comment/docstring
with anchor. Explain in 3 sentences: what it does, who uses it,
what problem it solves.

### Step 2: Entry Point

Show the main entry file with anchor. Trace the first 10-20 lines.
Explain: how the app boots, what gets registered, startup sequence.
Show connections: what does the entry file call first?

### Step 3: Auth Flow

Find the auth entry point (from scan-patterns.md auth detection).
Show the login/token verification handler with anchor. Trace one
auth request from entry to response.

If no auth found:
> "I don't see an auth layer — this might be a public API or an
>  internal tool. Want to skip to how data flows? (Step 4)"

### Step 4: Data Flow

Find the main data access pattern (ORM, raw SQL, API calls).
Show one representative data fetch with anchor. Trace:
request → handler → data layer → response.

### Step 5: Where to Make a First Change

Find the simplest, most self-contained feature area (typically:
one route + handler + model). Show it with anchor. Explain what a
good first PR would look like here.

> "If I were new to this repo and had to make my first change,
>  I'd start in [file] — here's why..."

## Navigation During Tour

The navigation commands from navigation-commands.md work throughout:
- `"rewind"` / `"go back"` → return to previous step
- `"skip"` → jump to next step
- `"jump to [topic]"` → skip to specific step or topic
- `"hold on — what's X?"` → pause tour, answer question fully,
  then offer: "Back to Step [N]? Or keep exploring here?"

## Mid-Tour Interrupts

If user asks an off-topic question mid-tour:
1. Answer it fully (apply the full Answer Loop)
2. Offer: "Back to Step [N] ([step name])? Or want to keep
   exploring this area?"

## Output

After completing tour or when user says "done", offer:
> "Want me to save this as TOUR.md? It'll read like a guide a
>  new developer can follow on their own."

On confirmation, generate these files in `{resolved_storage}/docs/{session_id}/`:

**TOUR.md:**
Each step with its code block anchor, explanation, and any
follow-up Q&A. Formatted as a re-readable learning guide.

**SESSION-TRANSCRIPT.md:**
Full conversational flow in order with all code blocks.
Always generated alongside TOUR.md.
