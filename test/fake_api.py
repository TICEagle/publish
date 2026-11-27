import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("PORT", "8787"))
STATUS = os.environ.get("STATUS", "published")
EXCHANGE_PATH = "/api/v1/oidc/github/exchange"


class FakeCEagle(BaseHTTPRequestHandler):
    def answer(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        print("GET", self.path, flush=True)
        self.answer(200, {"value": "github-jwt"})

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        print("POST", self.path, self.headers.get("Authorization"), flush=True)
        if self.path == EXCHANGE_PATH:
            self.answer(200, {"token": "ceagle_OIDC", "project": "selftest", "expires_at": "2030-01-01T00:00:00Z"})
        else:
            self.answer(202, {"version": "1.0.0", "status": STATUS, "capabilities": [], "reason": "a test"})


HTTPServer(("127.0.0.1", PORT), FakeCEagle).serve_forever()
