#!/usr/bin/env python3
"""Public, study-only Recoup server for Terac participants."""

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app import FailedClosed, MAX_BODY, ROOT, init_db, save_study_response


class StudyHandler(BaseHTTPRequestHandler):
    def json(self, status: int, value: object) -> None:
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        files = {"/": "study.html", "/study.js": "study.js", "/styles.css": "styles.css", "/redesign.css": "redesign.css"}
        name = files.get(self.path.split("?", 1)[0])
        if not name:
            return self.send_error(404)
        body = (ROOT / "web" / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/api/study/responses":
            return self.send_error(404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY:
                raise FailedClosed("Invalid request size.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise FailedClosed("Expected a JSON object.")
            save_study_response(payload)
            self.json(201, {"accepted": True})
        except (FailedClosed, ValueError, json.JSONDecodeError) as exc:
            self.json(422, {"error": str(exc), "failed_closed": True})


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("STUDY_PORT", "8001"))
    print(f"Recoup study running at http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), StudyHandler).serve_forever()
