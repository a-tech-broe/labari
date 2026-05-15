import json
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from ulid import ULID

from shared.auth import get_jwt_secret
from shared.db import get_table
from shared.response import error_response, success_response


def register(event, context):
    body = json.loads(event.get("body") or "{}")
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    name = body.get("name", "").strip()

    if not email or not password or not name:
        return error_response(400, "email, password, and name are required")

    if len(password) < 8:
        return error_response(400, "password must be at least 8 characters")

    table = get_table()
    if table.get_item(Key={"PK": f"USER#{email}", "SK": f"USER#{email}"}).get("Item"):
        return error_response(409, "An account with this email already exists")

    now = datetime.now(timezone.utc).isoformat()
    user = {
        "PK": f"USER#{email}",
        "SK": f"USER#{email}",
        "type": "USER",
        "id": str(ULID()),
        "email": email,
        "name": name,
        # All registered users are admins — this is a single-author blog
        "role": "admin",
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
        "created_at": now,
    }

    table.put_item(Item=user)
    return success_response({"token": _create_token(user), "user": _format_user(user)}, 201)


def login(event, context):
    body = json.loads(event.get("body") or "{}")
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not email or not password:
        return error_response(400, "email and password are required")

    table = get_table()
    result = table.get_item(Key={"PK": f"USER#{email}", "SK": f"USER#{email}"})
    user = result.get("Item")

    if not user or not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return error_response(401, "Invalid email or password")

    return success_response({"token": _create_token(user), "user": _format_user(user)})


def _create_token(user):
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def _format_user(user):
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "created_at": user["created_at"],
    }
