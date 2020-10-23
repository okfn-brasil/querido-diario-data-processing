from unittest import TestCase, expectedFailure
from unittest.mock import patch
import datetime
import hashlib
import tempfile

from botocore.stub import Stubber
import boto3

from storage import DigitalOceanSpaces, create_storage_interface
from tasks import StorageInterface


@patch.dict(
    "os.environ",
    {
        "STORAGE_REGION": "fake3",
        "STORAGE_ACCESS_KEY": "fake key",
        "STORAGE_ACCESS_SECRET": "fake secret",
        "STORAGE_ENDPOINT": "https://querido-diario.org",
        "STORAGE_BUCKET": "querido-diario",
    },
)
class StorageInterfaceCreationTests(TestCase):
    def test_create_storage_interface_creation_function(self):
        with patch("boto3.Session.client",) as mock:
            storage = create_storage_interface()
            self.assertIsInstance(
                storage,
                StorageInterface,
                msg="Storage creation  should returns an object implementing the StorageInterface",
            )
            mock.called_once_with(
                "s3",
                region_name="fake3",
                endpoint_url="https://querido-diario.org",
                aws_access_key_id="fake key",
                aws_secret_access_key="fake secret",
            )
            self.assertEqual("querido-diario", storage._bucket)


class DigitalOceanSpacesIntegrationTests(TestCase):

    REGION = "fake3"
    ACCESS_KEY = "fake key"
    ACCESS_SECRET = "fake secret"
    ENDPOINT = "https://querido-diario.org"
    BUCKET = "querido-diario"

    def test_if_digital_ocean_spaces_class_implements_the_right_tasks_interface(self):
        with patch("boto3.Session.client",) as mock:
            spaces = DigitalOceanSpaces(
                self.REGION,
                self.ENDPOINT,
                self.ACCESS_KEY,
                self.ACCESS_SECRET,
                self.BUCKET,
            )
            self.assertIsInstance(
                spaces,
                StorageInterface,
                msg="DigitalOceanSpaces should implement the StorageInterface",
            )

    def test_object_create(self):
        with patch("boto3.Session.client",) as mock:
            spaces = DigitalOceanSpaces(
                self.REGION,
                self.ENDPOINT,
                self.ACCESS_KEY,
                self.ACCESS_SECRET,
                self.BUCKET,
            )
            mock.called_once_with(
                "s3",
                region_name=self.REGION,
                endpoint_url=self.ENDPOINT,
                aws_access_key_id=self.ACCESS_KEY,
                aws_secret_access_key=self.ACCESS_SECRET,
            )
            self.assertEqual(self.BUCKET, spaces._bucket)

    def test_download_files_should_receive_the_bucket_filekey_destination(self):
        with patch("boto3.s3.inject.download_fileobj") as mock:
            spaces = DigitalOceanSpaces(
                self.REGION,
                self.ENDPOINT,
                self.ACCESS_KEY,
                self.ACCESS_SECRET,
                self.BUCKET,
            )
            file_to_be_downloaded = "test/sc_gaspar/2020/09/10/fake_gazette.pdf"
            with tempfile.TemporaryFile() as tmpfile:
                spaces.get_file(file_to_be_downloaded, tmpfile)
                mock.assert_called_once_with(
                    self.BUCKET, file_to_be_downloaded, tmpfile
                )

    @expectedFailure
    def test_get_file_when_boto3_fail(self):
        with patch(
            "boto3.s3.inject.download_fileobj", side_effect=Exception("Dummy error")
        ) as mock:
            spaces = DigitalOceanSpaces(
                self.REGION,
                self.ENDPOINT,
                self.ACCESS_KEY,
                self.ACCESS_SECRET,
                self.BUCKET,
            )
            file_to_be_downloaded = "test/sc_gaspar/2020/09/10/fake_gazette.pdf"
            with tempfile.TemporaryFile() as tmpfile:
                spaces.get_file(file_to_be_downloaded, tmpfile)

    def test_updaload_file_to_digital_ocean_spaces(self):
        with patch("boto3.s3.inject.upload_file") as mock:
            spaces = DigitalOceanSpaces(
                self.REGION,
                self.ENDPOINT,
                self.ACCESS_KEY,
                self.ACCESS_SECRET,
                self.BUCKET,
            )
            file_key = "test/sc_gaspar/2020/09/10/fake_gazette.pdf"
            file_to_be_uploaded = "tests/data/fake_gazette.odt"
            spaces.upload_file(file_to_be_uploaded, file_key)
            mock.assert_called_once_with(file_to_be_uploaded, self.BUCKET, file_key)
