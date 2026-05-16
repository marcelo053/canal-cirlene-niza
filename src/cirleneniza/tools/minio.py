import boto3
from botocore.config import Config
from loguru import logger
from pathlib import Path


class MinIOClient:
    """MinIO/S3 client for Canal Cirlene Niza asset storage."""

    def __init__(
        self,
        endpoint: str = "186.202.209.88:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket_work: str = "openclaw-work",
        bucket_final: str = "openclaw-final",
    ):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )
        self.bucket_work = bucket_work
        self.bucket_final = bucket_final

    def upload_file(
        self,
        file_path: Path | str,
        bucket: str,
        key: str,
    ) -> str:
        """Upload file to MinIO bucket."""
        file_path = Path(file_path)
        self.s3.upload_file(str(file_path), bucket, key)
        logger.info(f"Uploaded {file_path.name} to {bucket}/{key}")
        return f"minio://{bucket}/{key}"

    def download_file(self, bucket: str, key: str, dest: Path) -> Path:
        """Download file from MinIO."""
        self.s3.download_file(bucket, key, str(dest))
        logger.info(f"Downloaded {bucket}/{key} to {dest}")
        return dest

    def generate_presigned_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for sharing."""
        url = self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url
