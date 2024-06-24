import logging
import os
from typing import Generator
from io import BytesIO

import boto3

from tasks import StorageInterface


def get_storage_region():
    return os.environ["STORAGE_REGION"]


def get_storage_endpoint():
    return os.environ["STORAGE_ENDPOINT"]


def get_storage_access_key():
    return os.environ["STORAGE_ACCESS_KEY"]


def get_storage_access_secret():
    return os.environ["STORAGE_ACCESS_SECRET"]


def get_storage_bucket():
    return os.environ["STORAGE_BUCKET"]


def create_storage_interface() -> StorageInterface:
    """
    Build an object to interact with the object storage
    """
    return DigitalOceanSpaces(
        get_storage_region(),
        get_storage_endpoint(),
        get_storage_access_key(),
        get_storage_access_secret(),
        get_storage_bucket(),
    )


class DigitalOceanSpaces(StorageInterface):
    """
    Class to interact with the Digital Ocena Spaces using the S3 protocol
    """

    def __init__(
        self,
        region: str,
        endpoint: str,
        access_key: str,
        access_secret: str,
        bucket: str,
    ):
        self._region = region
        self._endpoint = endpoint
        self._access_key = access_key
        self._access_secret = access_secret
        self._bucket = bucket
        self._session = boto3.session.Session()
        self._client = self._session.client(
            "s3",
            region_name=self._region,
            endpoint_url=self._endpoint,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._access_secret,
        )

    def get_file(self, file_key: str, destination) -> None:
        logging.debug(f"Getting {file_key}")
        self._client.download_fileobj(self._bucket, file_key, destination)

    def upload_content(
        self,
        file_key: str,
        content_to_be_uploaded: str,
        permission: str = "public-read",
    ) -> None:
        logging.debug(f"Uploading {file_key}")
        f = BytesIO(content_to_be_uploaded.encode())
        self._client.upload_fileobj(
            f, self._bucket, file_key, ExtraArgs={"ACL": permission}
        )

    def upload_zip(
        self,
        file_key: str,
        content_to_be_uploaded: BytesIO,
        permission: str = "public-read",
    ) -> None:
        logging.debug(f"Uploading {file_key}")
        self._client.upload_fileobj(
            content_to_be_uploaded, self._bucket, file_key, ExtraArgs={"ACL": permission}
        )

    def copy_file(self, source_file_key: str, destination_file_key: str) -> None:
        logging.debug(f"Copying {source_file_key} to {destination_file_key}")
        self._client.copy_object(
            Bucket=self._bucket,
            CopySource={'Bucket': self._bucket, 'Key': source_file_key},
            Key=destination_file_key
        )

    def delete_file(self, file_key: str) -> None:
        logging.debug(f"Deletando {file_key}")
        self._client.delete_object(Bucket=self._bucket, Key=file_key)
