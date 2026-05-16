import json
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key
from ulid import ULID

from shared.auth import AuthError, verify_token
from shared.db import get_table
from shared.response import error_response, success_response


def list_comments(event, context):
    post_id = (event.get("pathParameters") or {}).get("id", "")
    result = get_table().query(
        KeyConditionExpression=Key("PK").eq(f"POST#{post_id}") & Key("SK").begins_with("COMMENT#"),
        ScanIndexForward=True,
    )
    return success_response({"comments": [_fmt(i) for i in result["Items"]]})


def create_comment(event, context):
    post_id = (event.get("pathParameters") or {}).get("id", "")
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return error_response(400, "Invalid JSON")

    author_name = (body.get("author_name") or "").strip()
    content = (body.get("content") or "").strip()

    if not author_name or not content:
        return error_response(400, "author_name and content are required")
    if len(content) > 2000:
        return error_response(400, "Comment too long (max 2000 characters)")

    table = get_table()
    if not table.get_item(Key={"PK": f"POST#{post_id}", "SK": f"POST#{post_id}"}).get("Item"):
        return error_response(404, "Post not found")

    comment_id = str(ULID())
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "PK": f"POST#{post_id}",
        "SK": f"COMMENT#{comment_id}",
        "type": "COMMENT",
        "comment_id": comment_id,
        "author_name": author_name,
        "content": content,
        "created_at": now,
    }
    table.put_item(Item=item)
    return success_response(_fmt(item), 201)


def delete_comment(event, context):
    try:
        verify_token(event)
    except AuthError:
        return error_response(401, "Unauthorized")

    post_id = (event.get("pathParameters") or {}).get("id", "")
    comment_id = (event.get("pathParameters") or {}).get("comment_id", "")
    get_table().delete_item(Key={"PK": f"POST#{post_id}", "SK": f"COMMENT#{comment_id}"})
    return success_response({"message": "Comment deleted"})


def _fmt(item):
    return {
        "id": item.get("comment_id"),
        "author_name": item.get("author_name"),
        "content": item.get("content"),
        "created_at": item.get("created_at"),
    }
