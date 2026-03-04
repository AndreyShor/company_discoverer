from __future__ import annotations

import mimetypes
import uuid
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


async def upload_attachment(
    file_data: bytes,
    original_filename: str,
    user_id: str,
) -> dict:
    """Upload a file to S3 and return metadata about the stored object."""
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    object_key = f"attachments/{user_id}/{uuid.uuid4()}.{extension}"
    content_type = mimetypes.guess_type(original_filename)[0] or "application/octet-stream"

    client = _s3_client()
    try:
        client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=object_key,
            Body=file_data,
            ContentType=content_type,
        )
    except ClientError as exc:
        logger.error("s3_upload_failed", error=str(exc), key=object_key)
        raise

    metadata = {
        "object_key": object_key,
        "original_filename": original_filename,
        "content_type": content_type,
        "size_bytes": len(file_data),
        "bucket": settings.s3_bucket_name,
    }
    logger.info("attachment_uploaded", **metadata)
    return metadata


async def delete_attachment(object_key: str) -> None:
    """Delete a previously uploaded attachment from S3."""
    client = _s3_client()
    try:
        client.delete_object(Bucket=settings.s3_bucket_name, Key=object_key)
        logger.info("attachment_deleted", object_key=object_key)
    except ClientError as exc:
        logger.error("s3_delete_failed", error=str(exc), key=object_key)
        raise


async def get_presigned_url(object_key: str, expiry_seconds: int = 3600) -> str:
    """Generate a presigned S3 URL for temporary access to an attachment."""
    client = _s3_client()
    url: str = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": object_key},
        ExpiresIn=expiry_seconds,
    )
    return url
