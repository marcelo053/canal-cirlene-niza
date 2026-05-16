import pytest
from unittest.mock import patch
from cirleneniza.tools.minio import MinIOClient


def test_minio_client_initialization():
    with patch("boto3.client"):
        client = MinIOClient(endpoint="test:9000", access_key="ak", secret_key="sk")
        assert client.bucket_work == "openclaw-work"
        assert client.bucket_final == "openclaw-final"


def test_minio_upload_method_exists():
    with patch("boto3.client"):
        client = MinIOClient()
        assert hasattr(client, "upload_file")
        assert hasattr(client, "download_file")
        assert hasattr(client, "generate_presigned_url")
