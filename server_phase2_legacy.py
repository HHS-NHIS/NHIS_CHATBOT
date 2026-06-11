#!/usr/bin/env python
"""Tiny dependency-free local HTTP server for the DHIS/NHIS prototype.
Run: python server.py
Open: http://127.0.0.1:8018
API:  http://127.0.0.1:8018/answer?q=What%20percent%20of%20adults%20had%20current%20asthma%20in%202024%3F
"""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))
from retrieve_estimate import retrieve

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DHIS/NHIS FAQ + Estimate Prototype</title>
<style>
body { font-family: Arial, sans-serif; margin: 2rem; max-width: 980px; line-height: 1.4; }
textarea { width: 100%; height: 80px; font-size: 16px; }
button { margin-top: 0.75rem; padding: 0.6rem 1rem; font-size: 16px; }
pre { white-space: pre-wrap; background: #f6f6f6; padding: 1rem; border: 1px solid #ddd; }
.note { color: #555; font-size: 14px; }
</style>
</head>
<body>
<h1>DHIS/NHIS FAQ + Estimate Prototype</h1>
<p class="note">Phase 2: deterministic adult/child Summary Health Statistics retrieval with all-year/latest-year handling, subgroup-first context, high/low summaries, special-code handling, source excerpts, and fallback links. No free-form unsourced estimates.</p>
<textarea id="q">What percent of adults had current asthma?</textarea><br>
<label><input type="checkbox" id="debug" checked> show matched source details</label><br>
<button onclick="ask()">Ask</button>
<pre id="answer"></pre>
<script>
async function ask() {
  const q = document.getElementById('q').value;
  const debug = document.getElementById('debug').checked ? '1' : '0';
  const res = await fetch('/answer?q=' + encodeURIComponent(q) + '&debug=' + debug);
  const data = await res.json();
  document.getElementById('answer').textContent = data.answer;
}
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            return self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        if parsed.path == "/answer":
            qs = parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0]
            debug = (qs.get("debug") or ["0"])[0] in {"1", "true", "yes"}
            if not q.strip():
                payload = {"status": "error", "answer": "Please provide a question using ?q=..."}
            else:
                payload = retrieve(q, debug=debug)
            return self._send(200, json.dumps(payload, indent=2).encode("utf-8"), "application/json; charset=utf-8")
        return self._send(404, b"Not found", "text/plain; charset=utf-8")

if __name__ == "__main__":
    host, port = "127.0.0.1", 8018
    print(f"Serving DHIS/NHIS prototype at http://{host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
