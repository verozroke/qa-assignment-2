"""Lightweight mock server that simulates the ticket management system."""

from __future__ import annotations

import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote_plus

VALID_USERNAME = "test.user"
VALID_PASSWORD = "ChangeMe123!"
VALID_TOKEN = "mock-jwt-token-abc123"
TICKETS: dict[str, dict] = {}

LOGIN_HTML = """<!DOCTYPE html>
<html><body>
<form method="POST" action="/login">
  <input name="username" />
  <input name="password" type="password" />
  <button type="submit">Login</button>
</form>
{error}
</body></html>"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html><body>
<main>
  <h1>Dashboard</h1>
  <a href="/tickets/new">Create Ticket</a>
  <div data-testid="user-menu">
    <button onclick="location.href='/logout'">Logout</button>
  </div>
</main>
</body></html>"""

CREATE_TICKET_HTML = """<!DOCTYPE html>
<html><body>
<main>
  <h1>Create Ticket</h1>
  <form method="POST" action="/tickets/new">
    <input name="title" />
    <textarea name="description"></textarea>
    <button type="submit">Submit</button>
  </form>
  {message}
</main>
</body></html>"""


class MockHandler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str, content_type: str = "text/html") -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(body.encode())

    def _send_json(self, code: int, data: dict) -> None:
        self._send(code, json.dumps(data), "application/json")

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/login":
            self._send(200, LOGIN_HTML.format(error=""))
        elif path == "/dashboard":
            self._send(200, DASHBOARD_HTML)
        elif path == "/tickets/new":
            self._send(200, CREATE_TICKET_HTML.format(message=""))
        elif path == "/logout":
            self.send_response(302)
            self.send_header("Location", "/login")
            self.end_headers()
        elif path.startswith("/api/tickets/"):
            token = self.headers.get("Authorization", "")
            if VALID_TOKEN not in token:
                self._send_json(401, {"error": "Unauthorized"})
                return
            ticket_id = path.split("/")[-1]
            if ticket_id in TICKETS:
                self._send_json(200, TICKETS[ticket_id])
            else:
                self._send_json(404, {"error": "Ticket not found"})
        else:
            self._send(404, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = self._read_body()

        # ── API: Auth ──
        if path == "/api/auth/login":
            try:
                data = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                self._send_json(400, {"error": "Invalid JSON"})
                return
            if data.get("username") == VALID_USERNAME and data.get("password") == VALID_PASSWORD:
                self._send_json(200, {"token": VALID_TOKEN})
            else:
                self._send_json(401, {"error": "Invalid credentials"})

        # ── API: Create ticket ──
        elif path == "/api/tickets":
            token = self.headers.get("Authorization", "")
            if VALID_TOKEN not in token:
                self._send_json(401, {"error": "Unauthorized"})
                return
            try:
                data = json.loads(body)
            except (json.JSONDecodeError, ValueError):
                self._send_json(400, {"error": "Invalid JSON"})
                return
            if not data.get("title") or not data.get("description"):
                errors = {}
                if not data.get("title"):
                    errors["title"] = "Title is required"
                if not data.get("description"):
                    errors["description"] = "Description is required"
                self._send_json(422, {"errors": errors})
                return
            ticket_id = str(uuid.uuid4())[:8]
            ticket = {"id": ticket_id, **data}
            TICKETS[ticket_id] = ticket
            self._send_json(201, ticket)

        # ── UI: Login form ──
        elif path == "/login":
            raw = parse_qs(body.decode(), keep_blank_values=True)
            params = {k: v[0] for k, v in raw.items()}
            if params.get("username") == VALID_USERNAME and params.get("password") == VALID_PASSWORD:
                self.send_response(302)
                self.send_header("Location", "/dashboard")
                self.end_headers()
            else:
                self._send(200, LOGIN_HTML.format(
                    error='<div class="alert-danger">Invalid username or password</div>'
                ))

        # ── UI: Create ticket form ──
        elif path == "/tickets/new":
            self._send(200, CREATE_TICKET_HTML.format(
                message='<div class="alert-success">Ticket created successfully</div>'
            ))

        else:
            self._send(404, "Not found")

    def log_message(self, format, *args) -> None:
        """Suppress request logs to keep CI output clean."""
        pass


def main() -> None:
    server = HTTPServer(("0.0.0.0", 8080), MockHandler)
    print("Mock server running on http://localhost:8080")
    server.serve_forever()


if __name__ == "__main__":
    main()