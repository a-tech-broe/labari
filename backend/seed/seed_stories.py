#!/usr/bin/env python3"""
Seed sample stories from stories.json.
Skips stories whose titles already exist (idempotent).

Required env vars:
  API_URL        - base URL of the API
  ADMIN_EMAIL    - email of an admin account to authenticate with
  ADMIN_PASSWORD - password for the admin account
"""
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = os.environ.get("API_URL", "").rstrip("/")
EMAIL = os.environ.get("ADMIN_EMAIL", "")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

if not API_URL or not API_URL.startswith("http"):
    print("Error: API_URL is not set.", file=sys.stderr)
    sys.exit(1)
if not EMAIL or not PASSWORD:
    print("Error: ADMIN_EMAIL and ADMIN_PASSWORD must be set.", file=sys.stderr)
    sys.exit(1)


def api(path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"{API_URL}{path}",
        data=json.dumps(data).encode() if data else None,
        headers=headers,
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


# Login
try:
    auth = api("/auth/login", {"email": EMAIL, "password": PASSWORD})
    token = auth["token"]
except Exception as e:
    print(f"Login failed: {e}", file=sys.stderr)
    sys.exit(1)

# Fetch existing titles
try:
    existing = {p["title"] for p in api("/posts").get("posts", [])}
except Exception:
    existing = set()

# Seed stories
seed_file = os.path.join(os.path.dirname(__file__), "stories.json")
with open(seed_file) as f:
    stories = json.load(f)

errors = 0
for story in stories:
    if story["title"] in existing:
        print(f"  exists  : {story['title'][:60]} (skipped)")
        continue
    try:
        req = urllib.request.Request(
            f"{API_URL}/posts",
            data=json.dumps(story).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        print(f"  created : {story['title'][:60]}")
    except Exception as e:
        print(f"  error   : {story['title'][:60]} — {e}", file=sys.stderr)
        errors += 1

if errors:
    sys.exit(1)
