import os
from functools import lru_cache

import boto3
import jwt


class AuthError(Exception):
    pass


@lru_cache(maxsize=1)
def get_jwt_secret():
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(
        Name=f"/{os.environ['PROJECT_NAME']}/{os.environ['ENVIRONMENT']}/jwt-secret",
        WithDecryption=True,
    )
    return response["Parameter"]["Value"]


def verify_token(event):
    headers = event.get("headers") or {}
    auth_header = headers.get("authorization") or headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise AuthError("Missing or invalid Authorization header")

    token = auth_header[7:]

    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
