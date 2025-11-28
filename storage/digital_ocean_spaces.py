import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Union

import boto3

from .interfaces import StorageInterface


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

    def get_file(self, file_to_be_downloaded: Union[str, Path], destination) -> None:
        """
        Download file using streaming to prevent loading entire file in memory (OOM prevention)
        """
        logging.debug(f"Getting {file_to_be_downloaded} (streaming)")
        self._client.download_fileobj(
            self._bucket, str(file_to_be_downloaded), destination
        )

    def upload_content(
        self,
        file_key: str,
        content_to_be_uploaded: Union[str, BytesIO],
        permission: str = "public-read",
    ) -> None:
        """
        Upload content using streaming to prevent loading entire content in memory (OOM prevention)
        """
        logging.debug(f"Uploading {file_key}")

        if isinstance(content_to_be_uploaded, str):
            f = BytesIO(content_to_be_uploaded.encode())
            self._client.upload_fileobj(
                f, self._bucket, file_key, ExtraArgs={"ACL": permission}
            )
            # Explicit cleanup
            f.close()
        else:
            self._client.upload_fileobj(
                content_to_be_uploaded,
                self._bucket,
                file_key,
                ExtraArgs={"ACL": permission},
            )

    def upload_file(
        self,
        file_key: str,
        file_path: str,
        permission: str = "public-read",
    ) -> None:
        logging.debug(f"Uploading {file_key}")
        self._client.upload_file(
            file_path, self._bucket, file_key, ExtraArgs={"ACL": permission}
        )

    def upload_file_multipart(
        self,
        file_key: str,
        file_path: str,
        permission: str = "public-read",
        part_size: int = 100 * 1024 * 1024,
    ) -> None:
        logging.debug(f"Uploading {file_key} with multipart")

        multipart_upload = self._client.create_multipart_upload(
            Bucket=self._bucket, Key=file_key, ACL=permission
        )
        upload_id = multipart_upload["UploadId"]

        parts = []

        try:
            with open(file_path, "rb") as file:
                part_number = 1
                while True:
                    data = file.read(part_size)
                    if not data:
                        break

                    response = self._client.upload_part(
                        Bucket=self._bucket,
                        Key=file_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=data,
                    )

                    parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
                    part_number += 1

            self._client.complete_multipart_upload(
                Bucket=self._bucket,
                Key=file_key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

        except Exception as e:
            logging.debug(f"Aborted uploading {file_key} with multipart")
            self._client.abort_multipart_upload(
                Bucket=self._bucket, Key=file_key, UploadId=upload_id
            )
            raise e
        else:
            logging.debug(f"Finished uploading {file_key} with multipart")

    def copy_file(self, source_file_key: str, destination_file_key: str) -> None:
        logging.debug(f"Copying {source_file_key} to {destination_file_key}")
        self._client.copy_object(
            Bucket=self._bucket,
            CopySource={"Bucket": self._bucket, "Key": source_file_key},
            Key=destination_file_key,
        )

    def delete_file(self, file_key: str) -> None:
        logging.debug(f"Deleting {file_key}")
        self._client.delete_object(Bucket=self._bucket, Key=file_key)
