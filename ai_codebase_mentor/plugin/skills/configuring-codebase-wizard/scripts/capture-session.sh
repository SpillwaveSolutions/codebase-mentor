#!/usr/bin/env bash
# capture-session.sh — Reads PostToolUse event JSON from stdin, appends to session file.
# Called by Agent Rulez run: action. Event schema:
#   {"hook_event_name","tool_name","tool_input","session_id","timestamp"}
# Output: .code-wizard/sessions/{session_id}.json
set -euo pipefail

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")
SESSION_FILE=".code-wizard/sessions/${SESSION_ID}.json"
mkdir -p .code-wizard/sessions

if [ ! -f "$SESSION_FILE" ]; then
  echo '{"version":"1.0","session_id":"'"$SESSION_ID"'","turns":[]}' > "$SESSION_FILE"
fi

export SESSION_FILE
export INPUT
python3 -c "
import sys, json, os
session_file = os.environ['SESSION_FILE']
event_json = os.environ['INPUT']
data = json.loads(open(session_file).read())
event = json.loads(event_json)
data['turns'].append(event)
open(session_file, 'w').write(json.dumps(data, indent=2))
" 2>/dev/null || true
