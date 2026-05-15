import json
import os

import boto3
from ulid import ULID

from shared.response import error_response, success_response

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def presign(event, context):
    body = json.loads(event.get("body") or "{}")
    file_type = body.get("file_type", "image/jpeg")

    if file_type not in ALLOWED_TYPES:
        return error_response(400, f"file_type must be one of: {', '.join(sorted(ALLOWED_TYPES))}")

    ext = file_type.split("/")[1].replace("jpeg", "jpg")
    key = f"uploads/{event['user']['sub']}/{ULID()}.{ext}"

    s3 = boto3.client("s3")
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": os.environ["IMAGES_BUCKET"],
            "Key": key,
            "ContentType": file_type,
        },
        ExpiresIn=300,
    )

    return success_response({
        "upload_url": upload_url,
        "key": key,
        "public_url": f"https://{os.environ['IMAGES_CDN_DOMAIN']}/{key}",
    })
