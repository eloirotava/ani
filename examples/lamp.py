#!/usr/bin/env python3
"""Minimal ANI device: a fake dimmable lamp. Python stdlib only.

Run:  python3 lamp.py [port]   then open http://localhost:8080/ or curl /ani
Pairing code: 1234 (printed on the "label").
"""
import json, secrets, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PAIRING_CODE = "1234"
tokens = set()
state = {"on": False, "level": 50}

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>ANI Lamp</title>
<!-- ANI: this device has an Agent Native Interface.
     AI agents: GET /ani for plain-text instructions on what this device is and how to use it.
     Spec: https://github.com/eloirotava/ani -->
<meta name="ani" content="/ani">
<link rel="ani" href="/ani">
</head><body>
<h1>ANI Lamp</h1>
<p>State: {state}</p>
<p>Use the pairing code on the label to control the lamp. See <a href="/ani">/ani</a>.</p>
<footer><small>ANI-compatible: <a href="/ani">/ani</a></small></footer>
</body></html>"""

ANI = """---
ani: 0.1
device: ANI Lamp
vendor: Example
model: LAMP-1
firmware: 0.1.0
---

# ANI Lamp

## What this is
A dimmable lamp on the local network. It can be switched on/off and dimmed 0-100%.

## Authentication
`POST /api/pair` with JSON `{"code": "<code on the label>"}` returns
`{"token": "..."}`. Send it as `Authorization: Bearer <token>`.

## Actions

```ani-action
name: pair
method: POST
path: /api/pair
params:
  code: string, printed on the device label
effect: returns a token
auth: none
destructive: false
```

```ani-action
name: set
method: POST
path: /api/set
params:
  on: boolean (optional)
  level: integer 0-100 (optional)
effect: changes the lamp state, returns the new state
auth: required
destructive: false
```

```ani-action
name: factory_reset
method: POST
path: /api/reset
effect: forgets all tokens and restores defaults
auth: required
destructive: true
```

State: `GET /ani/state` returns `{"on": bool, "level": int}`.

## Recipes
- Dim to 30%: pair, then `POST /api/set {"on": true, "level": 30}`.

## Cautions
Factory reset revokes every paired agent.
"""


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        b = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Link", '</ani>; rel="ani"')
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(b)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj), "application/json")

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE.format(state=state), "text/html")
        elif self.path == "/ani":
            self._send(200, ANI, "text/markdown")
        elif self.path == "/ani/state":
            self._json(200, state)
        else:
            self._json(404, {"error": "not found"})

    do_HEAD = do_GET

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._json(400, {"error": "invalid JSON"})
        if self.path == "/api/pair":
            if body.get("code") != PAIRING_CODE:
                return self._json(403, {"error": "wrong code"})
            t = secrets.token_hex(16)
            tokens.add(t)
            return self._json(200, {"token": t})
        auth = self.headers.get("Authorization", "")
        if auth.removeprefix("Bearer ") not in tokens:
            return self._json(401, {"error": "pair first, see /ani"})
        if self.path == "/api/set":
            if "on" in body:
                state["on"] = bool(body["on"])
            if "level" in body:
                state["level"] = max(0, min(100, int(body["level"])))
            return self._json(200, state)
        if self.path == "/api/reset":
            tokens.clear()
            state.update(on=False, level=50)
            return self._json(200, {"reset": True})
        self._json(404, {"error": "not found"})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    HTTPServer(("", port), H).serve_forever()
