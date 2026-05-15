import json

from handlers import auth, images, posts
from shared.auth import AuthError, verify_token
from shared.response import error_response, success_response

PROTECTED_ROUTES = {
    "POST /posts",
    "PUT /posts/{id}",
    "DELETE /posts/{id}",
    "POST /images/upload",
}

ROUTE_MAP = {
    "GET /posts": posts.list_posts,
    "GET /posts/{id}": posts.get_post,
    "GET /search": posts.search_posts,
    "POST /posts": posts.create_post,
    "PUT /posts/{id}": posts.update_post,
    "DELETE /posts/{id}": posts.delete_post,
    "POST /auth/register": auth.register,
    "POST /auth/login": auth.login,
    "POST /images/upload": images.presign,
}


def lambda_handler(event, context):
    route_key = event.get("routeKey", "")

    # CORS preflight — API Gateway handles most CORS, but OPTIONS routes go to Lambda too
    if route_key == "OPTIONS /{proxy+}":
        return success_response({})

    handler_fn = ROUTE_MAP.get(route_key)
    if not handler_fn:
        return error_response(404, "Route not found")

    if route_key in PROTECTED_ROUTES:
        try:
            event["user"] = verify_token(event)
        except AuthError as e:
            return error_response(401, str(e))

    try:
        return handler_fn(event, context)
    except Exception as e:
        print(f"Unhandled error on {route_key}: {type(e).__name__}: {e}")
        return error_response(500, "Internal server error")
