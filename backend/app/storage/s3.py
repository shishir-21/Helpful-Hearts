from functools import lru_cache
from typing import Protocol

import boto3
from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from app.core.config import settings


class ObjectStorage(Protocol):
    def create_upload_url(self, key: str, content_type: str) -> str: ...
    def head(self, key: str) -> dict: ...
    def delete(self, key: str) -> None: ...


class S3Storage:
    def __init__(self) -> None:
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required for file storage")
        kwargs = {
            "region_name": settings.s3_region or None,
            "aws_access_key_id": settings.s3_access_key_id or None,
            "aws_secret_access_key": settings.s3_secret_access_key or None,
            "endpoint_url": settings.s3_endpoint_url or None,
        }
        self.bucket = settings.s3_bucket
        self.client: BaseClient = boto3.client("s3", **kwargs)

    def create_upload_url(self, key: str, content_type: str) -> str:
        try:
            return self.client.generate_presigned_url(
                "put_object",
                Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
                ExpiresIn=settings.s3_presigned_url_expire_seconds,
                HttpMethod="PUT",
            )
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(status_code=503, detail="File storage unavailable") from exc

    def head(self, key: str) -> dict:
        try:
            return self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 404:
                raise HTTPException(status_code=404, detail="Uploaded file not found") from exc
            raise HTTPException(status_code=503, detail="File storage unavailable") from exc
        except BotoCoreError as exc:
            raise HTTPException(status_code=503, detail="File storage unavailable") from exc

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(status_code=503, detail="File storage unavailable") from exc


@lru_cache
def get_storage() -> S3Storage:
    return S3Storage()
