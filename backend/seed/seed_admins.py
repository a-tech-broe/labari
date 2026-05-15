#!/usr/bin/env python3
"""
Seed admin accounts from admins.json.
Skips accounts that already exist (idempotent).

Required env vars:
  API_URL        - base URL of the API (e.g. https://api.mailabari.com)
  ADMIN_PASSWORD - password to assign to all seeded admins
"""
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = os.environ.get("API_URL", "").rstrip("/")
PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

if not API_URL or not API_URL.startswith("http"):
    print("Error: API_URL is not set or is not a valid URL.", file=sys.stderr)
    print("Set the NEXT_PUBLIC_API_URL secret in GitHub, or the API_URL env var.", file=sys.stderr)
    sys.exit(1)

if not PASSWORD:
    print("Error: ADMIN_PASSWORD secret is not set.", file=sys.stderr)
    sys.exit(1)

seed_file = os.path.join(os.path.dirname(__file__), "admins.json")
with open(seed_file) as f:
    admins = json.load(f)

if not admins:
    print("No admins defined in admins.json — nothing to do.")
    sys.exit(0)

errors = 0
for admin in admins:
    payload = json.dumps({
        "name":     admin["name"],
        "email":    admin["email"],
        "password": PASSWORD,
    }).encode()

    req = urllib.request.Request(
        f"{API_URL}/auth/register",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req):
            print(f"  created : {admin['email']}")
    except urllib.error.HTTPError as e:
        if e.code == 409:
            print(f"  exists  : {admin['email']} (skipped)")
        else:
            body = e.read().decode(errors="replace")
            print(f"  error   : {admin['email']} — HTTP {e.code}: {body}", file=sys.stderr)
            errors += 1

if errors:
    sys.exit(1)
