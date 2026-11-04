import re
import uuid
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException
from app.config import get_settings

settings = get_settings()


class S3StorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.aws_endpoint_url_s3,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key.get_secret_value(),
            region_name=settings.aws_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"})
        )
        self.bucket = settings.s3_bucket_name

    def generate_presigned_upload_url(self, prefix: str, filename: str, expiration: int = 900) -> tuple[str, str]:
        """Temporary PUT URL for direct client uploads. `prefix` is built by the server, never by the client."""
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        ext = re.sub(r"[^A-Za-z0-9]", "", ext)[:10] or "bin"
        file_key = f"{prefix}/{uuid.uuid4()}.{ext}"

        try:
            url = self.client.generate_presigned_url(
                "put_object",
                Params={"Bucket": self.bucket, "Key": file_key},
                ExpiresIn=expiration,
            )
            return file_key, url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")

    def generate_presigned_url(self, file_key: str, expiration: int = 3600) -> str:
        """Temporary secure view URL since the bucket is private."""
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": file_key},
                ExpiresIn=expiration,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate secure file link: {str(e)}")

    def object_exists(self, file_key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=file_key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise HTTPException(status_code=502, detail="Storage service unavailable. Try again.")


s3_service = S3StorageService()