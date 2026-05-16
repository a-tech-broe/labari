import json
import re
from datetime import datetime, timezone

from boto3.dynamodb.conditions import Key
from ulid import ULID

from shared.db import get_table
from shared.response import error_response, success_response


def list_posts(event, context):
    params = event.get("queryStringParameters") or {}
    category = params.get("category", "").strip().lower()

    table = get_table()
    result = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq("POSTS#PUBLISHED"),
        ScanIndexForward=False,
    )

    posts = [_format_post(item) for item in result["Items"]]

    if category:
        posts = [p for p in posts if category in [c.lower() for c in (p.get("categories") or [])]]

    return success_response({"posts": posts})


def search_posts(event, context):
    params = event.get("queryStringParameters") or {}
    query = params.get("q", "").strip().lower()

    if not query or len(query) < 2:
        return error_response(400, "q must be at least 2 characters")

    table = get_table()
    result = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("GSI1PK").eq("POSTS#PUBLISHED"),
        ScanIndexForward=False,
    )

    matches = []
    for item in result["Items"]:
        haystack = " ".join([
            item.get("title", ""),
            item.get("excerpt", ""),
            item.get("content", ""),
            " ".join(item.get("categories") or []),
        ]).lower()
        if query in haystack:
            matches.append(_format_post(item))

    return success_response({"posts": matches, "query": query})


def get_post(event, context):
    post_id = (event.get("pathParameters") or {}).get("id", "")
    result = get_table().get_item(Key={"PK": f"POST#{post_id}", "SK": f"POST#{post_id}"})
    item = result.get("Item")
    if not item:
        return error_response(404, "Post not found")
    return success_response({"post": _format_post(item)})


def create_post(event, context):
    body = json.loads(event.get("body") or "{}")
    title = body.get("title", "").strip()
    content = body.get("content", "").strip()

    if not title or not content:
        return error_response(400, "title and content are required")

    post_id = str(ULID())
    now = datetime.now(timezone.utc).isoformat()
    published = bool(body.get("published", False))
    categories = _clean_categories(body.get("categories", []))

    item = {
        "PK": f"POST#{post_id}",
        "SK": f"POST#{post_id}",
        "type": "POST",
        "id": post_id,
        "title": title,
        "slug": _slugify(title),
        "content": content,
        "excerpt": body.get("excerpt") or content[:200],
        "cover_image": body.get("cover_image", ""),
        "categories": categories,
        "author_id": event["user"]["sub"],
        "published": published,
        "created_at": now,
        "updated_at": now,
    }

    if published:
        item["GSI1PK"] = "POSTS#PUBLISHED"
        item["GSI1SK"] = f"{now}#{post_id}"
        item["published_at"] = now

    get_table().put_item(Item=item)
    return success_response({"post": _format_post(item)}, 201)


def update_post(event, context):
    post_id = (event.get("pathParameters") or {}).get("id", "")
    body = json.loads(event.get("body") or "{}")
    table = get_table()

    result = table.get_item(Key={"PK": f"POST#{post_id}", "SK": f"POST#{post_id}"})
    item = result.get("Item")
    if not item:
        return error_response(404, "Post not found")

    now = datetime.now(timezone.utc).isoformat()
    set_parts = ["#updated_at = :updated_at"]
    names = {"#updated_at": "updated_at"}
    values = {":updated_at": now}

    for field in ["title", "content", "excerpt", "cover_image", "published"]:
        if field in body:
            set_parts.append(f"#{field} = :{field}")
            names[f"#{field}"] = field
            values[f":{field}"] = body[field]

    if "categories" in body:
        set_parts.append("#categories = :categories")
        names["#categories"] = "categories"
        values[":categories"] = _clean_categories(body["categories"])

    # First-time publish: add to GSI so it appears in public listing
    if body.get("published") and not item.get("published"):
        set_parts += ["#GSI1PK = :GSI1PK", "#GSI1SK = :GSI1SK", "#published_at = :published_at"]
        names.update({"#GSI1PK": "GSI1PK", "#GSI1SK": "GSI1SK", "#published_at": "published_at"})
        values.update({":GSI1PK": "POSTS#PUBLISHED", ":GSI1SK": f"{now}#{post_id}", ":published_at": now})

    table.update_item(
        Key={"PK": f"POST#{post_id}", "SK": f"POST#{post_id}"},
        UpdateExpression="SET " + ", ".join(set_parts),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )
    return success_response({"message": "Post updated"})


def like_post(event, context):
    post_id = (event.get("pathParameters") or {}).get("id", "")
    table = get_table()
    try:
        result = table.update_item(
            Key={"PK": f"POST#{post_id}", "SK": f"POST#{post_id}"},
            UpdateExpression="ADD like_count :inc",
            ConditionExpression="attribute_exists(PK)",
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="UPDATED_NEW",
        )
        return success_response({"like_count": int(result["Attributes"].get("like_count", 0))})
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return error_response(404, "Post not found")


def delete_post(event, context):
    post_id = (event.get("pathParameters") or {}).get("id", "")
    table = get_table()

    result = table.get_item(Key={"PK": f"POST#{post_id}", "SK": f"POST#{post_id}"})
    if not result.get("Item"):
        return error_response(404, "Post not found")

    table.delete_item(Key={"PK": f"POST#{post_id}", "SK": f"POST#{post_id}"})
    return success_response({"message": "Post deleted"})


def _clean_categories(raw):
    if not isinstance(raw, list):
        return []
    return [c.strip().lower() for c in raw if isinstance(c, str) and c.strip()]


def _slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def _format_post(item):
    return {
        "id": item.get("id"),
        "title": item.get("title"),
        "slug": item.get("slug"),
        "content": item.get("content"),
        "excerpt": item.get("excerpt"),
        "cover_image": item.get("cover_image"),
        "categories": item.get("categories") or [],
        "author_id": item.get("author_id"),
        "published": item.get("published", False),
        "published_at": item.get("published_at"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "like_count": int(item.get("like_count", 0)),
    }
