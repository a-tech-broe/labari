import uuid

import boto3
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from core.auth import get_current_user
from core.config import settings

router = APIRouter(prefix="/images", tags=["images"])


class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str


@router.post("/upload")
def get_upload_url(body: PresignedUrlRequest, user=Depends(get_current_user)):
    if not settings.images_bucket:
        raise HTTPException(503, "Image uploads not configured")

    ext = body.filename.rsplit(".", 1)[-1].lower() if "." in body.filename else "bin"
    key = f"uploads/{uuid.uuid4()}.{ext}"

    s3 = boto3.client("s3", region_name=settings.aws_region)
    url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.images_bucket,
            "Key": key,
            "ContentType": body.content_type,
        },
        ExpiresIn=300,
    )
    return {"upload_url": url, "key": key}
