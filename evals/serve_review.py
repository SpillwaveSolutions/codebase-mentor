#!/usr/bin/env python3
"""Serve the trigger tuning review UI.

Reads evals.json, serves the HTML viewer, and persists label changes
back to evals.json when the user clicks Save.

Usage:
    python evals/serve_review.py                    # default port 3118
    python evals/serve_review.py --port 8080        # custom port
    python evals/serve_review.py --static out.html  # export self-contained HTML

No dependencies beyond the Python stdlib.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import webbrowser
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

EVALS_DIR = Path(__file__).parent
EVALS_PATH = EVALS_DIR / "evals.json"
VIEWER_HTML = EVALS_DIR / "trigger_review.html"
NOTES_PATH = EVALS_DIR / "review_notes.json"


def _kill_port(port: int) -> None:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True, timeout=5,
        )
        for pid_str in result.stdout.strip().split("\n"):
            if pid_str.strip():
                try:
                    os.kill(int(pid_str.strip()), signal.SIGTERM)
                except (ProcessLookupError, ValueError):
                    pass
        if result.stdout.strip():
            time.sleep(0.5)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def generate_static_html() -> str:
    """Embed evals data directly into the HTML for static export."""
    template = VIEWER_HTML.read_text()
    evals = json.loads(EVALS_PATH.read_text())
    data_json = json.dumps(evals)
    return template.replace(
        "/*__EMBEDDED_DATA__*/",
        f"const EMBEDDED_DATA = {data_json};"
    )


class ReviewHandler(BaseHTTPRequestHandler):
    def __init__(self, evals_path: Path, notes_path: Path, *args, **kwargs):
        self.evals_path = evals_path
        self.notes_path = notes_path
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            html = VIEWER_HTML.read_text()
            content = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        elif self.path == "/api/evals":
            data = self.evals_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)

        elif self.path == "/api/notes":
            if self.notes_path.exists():
                data = self.notes_path.read_bytes()
            else:
                data = b"{}"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        else:
            self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if self.path == "/api/evals":
            try:
                data = json.loads(body)
                self.evals_path.write_text(json.dumps(data, indent=2) + "\n")
                resp = b'{"ok":true}'
                self.send_response(200)
            except (json.JSONDecodeError, OSError) as e:
                resp = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        elif self.path == "/api/notes":
            try:
                data = json.loads(body)
                self.notes_path.write_text(json.dumps(data, indent=2) + "\n")
                resp = b'{"ok":true}'
                self.send_response(200)
            except (json.JSONDecodeError, OSError) as e:
                resp = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)

        else:
            self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        pass  # suppress request logging


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve trigger tuning review UI")
    parser.add_argument("--port", "-p", type=int, default=3118)
    parser.add_argument("--static", "-s", type=Path, default=None,
                        help="Export self-contained HTML instead of serving")
    args = parser.parse_args()

    if not EVALS_PATH.exists():
        print(f"Error: {EVALS_PATH} not found", file=sys.stderr)
        sys.exit(1)

    if args.static:
        html = generate_static_html()
        args.static.parent.mkdir(parents=True, exist_ok=True)
        args.static.write_text(html)
        print(f"\n  Static viewer written to: {args.static}\n")
        sys.exit(0)

    port = args.port
    _kill_port(port)

    handler = partial(ReviewHandler, EVALS_PATH, NOTES_PATH)
    try:
        server = HTTPServer(("127.0.0.1", port), handler)
    except OSError:
        server = HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]

    url = f"http://localhost:{port}"
    print(f"\n  Trigger Tuning Review")
    print(f"  ─────────────────────────────────────")
    print(f"  URL:       {url}")
    print(f"  Evals:     {EVALS_PATH}")
    print(f"  Notes:     {NOTES_PATH}")
    print(f"\n  Press Ctrl+C to stop.\n")

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.server_close()


if __name__ == "__main__":
    main()
