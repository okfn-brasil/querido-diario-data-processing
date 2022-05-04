from unittest import TestCase
from unittest.mock import MagicMock, patch
import os
import logging
from datetime import date, datetime
import tempfile

from tasks import (
    extract_text_pending_gazettes,
    upload_gazette_raw_text,
    TextExtractorInterface,
)


@patch.dict(
    "os.environ",
    {
        "QUERIDO_DIARIO_FILES_ENDPOINT": "http://test.com",
    },
)
class TextExtractionTaskTests(TestCase):
    def setUp(self):
        self.database_mock = MagicMock()
        self.data = [
            {
                "id": 1,
                "source_text": "",
                "date": date(2020, 10, 18),
                "edition_number": "1",
                "is_extra_edition": False,
                "power": "executive",
                "file_checksum": "972aca2e-1174-11eb-b2d5-a86daaca905e",
                "file_path": "sc_gaspar/2020-10-18/972aca2e-1174-11eb-b2d5-a86daaca905e.pdf",
                "file_url": "www.querido-diario.org",
                "scraped_at": datetime.now(),
                "created_at": datetime.now(),
                "territory_id": "3550308",
                "processed": False,
                "state_code": "SC",
                "territory_name": "Gaspar",
                "file_raw_txt": "http://test.com/sc_gaspar/2020-10-18/972aca2e-1174-11eb-b2d5-a86daaca905e.txt",
            }
        ]
        self.database_mock.get_pending_gazettes = MagicMock(return_value=self.data)
        self.database_mock.set_gazette_as_processed = MagicMock()
        self.storage_mock = MagicMock()
        self.storage_mock.get_file = MagicMock()
        self.storage_mock.upload_content = MagicMock()
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            self.tmpfile_returned_by_text_extraction_function_mock = tmpfile.name
        self.text_extraction_function = MagicMock(spec=TextExtractorInterface)
        self.text_extraction_function.extract_text.return_value = ""
        self.index_mock = MagicMock()
        self.index_mock.index_document = MagicMock()

    def tearDown(self):
        if os.path.exists(self.tmpfile_returned_by_text_extraction_function_mock):
            os.remove(self.tmpfile_returned_by_text_extraction_function_mock)

    def test_database_call(self):
        extract_text_pending_gazettes(
            self.database_mock,
            self.storage_mock,
            self.index_mock,
            self.text_extraction_function,
        )
        self.database_mock.get_pending_gazettes.assert_called_once()

    def test_storage_call_to_get_file(self):
        extract_text_pending_gazettes(
            self.database_mock,
            self.storage_mock,
            self.index_mock,
            self.text_extraction_function,
        )

        self.storage_mock.get_file.assert_called_once()
        self.assertEqual(
            self.storage_mock.get_file.call_args.args[0], self.data[0]["file_path"]
        )
        self.assertIsInstance(
            self.storage_mock.get_file.call_args.args[1], tempfile._TemporaryFileWrapper
        )

    def test_text_extraction_function_call(self):
        extract_text_pending_gazettes(
            self.database_mock,
            self.storage_mock,
            self.index_mock,
            self.text_extraction_function,
        )

        self.text_extraction_function.extract_text.assert_called_once()
        self.assertEqual(
            len(self.text_extraction_function.extract_text.call_args.args), 1
        )
        self.assertIsInstance(
            self.text_extraction_function.extract_text.call_args.args[0], str
        )

    def test_set_gazette_as_processed(self):
        extract_text_pending_gazettes(
            self.database_mock,
            self.storage_mock,
            self.index_mock,
            self.text_extraction_function,
        )

        self.database_mock.set_gazette_as_processed.assert_called_once_with(
            1, "972aca2e-1174-11eb-b2d5-a86daaca905e"
        )

    def test_should_index_document(self):
        extract_text_pending_gazettes(
            self.database_mock,
            self.storage_mock,
            self.index_mock,
            self.text_extraction_function,
        )
        self.index_mock.index_document.assert_called()

    def copy_file_to_temporary_file(self, source_file):
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            with open(source_file, "r+b") as srcfile:
                tmpfile.write(srcfile.read())
            return tmpfile.name

    def test_indexed_document_should_contain_gazette_content(self):
        database_mock = MagicMock()
        data = [
            {
                "id": 1,
                "source_text": "",
                "date": date(2020, 10, 18),
                "edition_number": "1",
                "is_extra_edition": False,
                "power": "executive",
                "file_checksum": "972aca2e-1174-11eb-b2d5-a86daaca905e",
                "file_path": "tests/data/fake_gazette.txt",
                "file_url": "www.querido-diario.org",
                "scraped_at": datetime.now(),
                "created_at": datetime.now(),
                "territory_id": "3550308",
                "processed": False,
                "state_code": "SC",
                "territory_name": "Gaspar",
                "url": "http://test.com/tests/data/fake_gazette.txt",
                "file_raw_txt": "http://test.com/tests/data/fake_gazette.txt",
            }
        ]
        expected_data = data[0].copy()
        with open("tests/data/fake_gazette.txt", "r") as f:
            expected_data["source_text"] = f.read()

        database_mock.get_pending_gazettes = MagicMock(return_value=data)
        database_mock.set_gazette_as_processed = MagicMock()

        tmp_gazette_file = self.copy_file_to_temporary_file(
            "tests/data/fake_gazette.txt"
        )
        text_extraction_function = MagicMock(spec=TextExtractorInterface)
        text_extraction_function.extract_text.return_value = expected_data[
            "source_text"
        ]

        extract_text_pending_gazettes(
            database_mock,
            self.storage_mock,
            self.index_mock,
            text_extraction_function,
        )
        self.index_mock.index_document.assert_called_once_with(expected_data)

    def file_should_not_exist(self, file_to_check):
        self.assertFalse(
            os.path.exists(file_to_check), msg=f"File {file_to_check} should be deleted"
        )

    def test_invalid_file_type_should_be_skipped(self):

        text_extraction_function = MagicMock(spec=TextExtractorInterface)
        text_extraction_function.extract_text.side_effect = Exception(
            "Unsupported file type"
        )

        extract_text_pending_gazettes(
            self.database_mock,
            self.storage_mock,
            self.index_mock,
            text_extraction_function,
        )
        self.storage_mock.get_file.assert_called_once()
        self.database_mock.get_pending_gazettes.assert_called_once()
        self.database_mock.set_gazette_as_processed.assert_not_called()
        self.index_mock.index_document.assert_not_called()
        self.file_should_not_exist(
            text_extraction_function.extract_text.call_args.args[0]
        )

    def assert_called_twice(self, mock):
        self.assertEqual(mock.call_count, 2, msg="Mock should be called twice")

    def test_invalid_file_type_should_be_skipped_and_valid_should_be_processed(self):
        database_mock = MagicMock()
        data = [
            {
                "id": 1,
                "source_text": "",
                "date": date(2020, 10, 18),
                "edition_number": "1",
                "is_extra_edition": False,
                "power": "executive",
                "file_checksum": "972aca2e-1174-11eb-b2d5-a86daaca905e",
                "file_path": "sc_gaspar/2020-10-18/972aca2e-1174-11eb-b2d5-a86daaca905e.pdf",
                "file_url": "www.querido-diario.org",
                "scraped_at": datetime.now(),
                "created_at": datetime.now(),
                "territory_id": "3550308",
                "processed": False,
                "state_code": "SC",
                "territory_name": "Gaspar",
                "url": "http://test.com/sc_gaspar/2020-10-18/972aca2e-1174-11eb-b2d5-a86daaca905e.pdf",
                "file_raw_txt": "http://test.com/sc_gaspar/2020-10-18/972aca2e-1174-11eb-b2d5-a86daaca905e.txt",
            },
            {
                "id": 2,
                "source_text": "",
                "date": date(2020, 10, 19),
                "edition_number": "1",
                "is_extra_edition": False,
                "power": "executive",
                "file_checksum": "972aca2e-1174-11eb-b2d5-a86daaca905e",
                "file_path": "sc_gaspar/2020-10-18/972aca2e-1174-11eb-b2d5-a86daaca905e.pdf",
                "file_url": "www.querido-diario.org",
                "scraped_at": datetime.now(),
                "created_at": datetime.now(),
                "territory_id": "3550308",
                "processed": False,
                "state_code": "SC",
                "territory_name": "Gaspar",
                "url": "http://test.com/sc_gaspar/2020-10-18/972aca2e-1174-11eb-b2d5-a86daaca905e.pdf",
                "file_raw_txt": "http://test.com/sc_gaspar/2020-10-18/972aca2e-1174-11eb-b2d5-a86daaca905e.txt",
            },
        ]
        database_mock.get_pending_gazettes = MagicMock(return_value=data)
        database_mock.set_gazette_as_processed = MagicMock()

        file_content_returned_by_text_extraction_function_mock = None
        with open("tests/data/fake_gazette.txt", "r") as f:
            file_content_returned_by_text_extraction_function_mock = f.read()

        text_extraction_function = MagicMock(spec=TextExtractorInterface)
        text_extraction_function.extract_text.side_effect = [
            Exception("Unsupported file type"),
            file_content_returned_by_text_extraction_function_mock,
        ]

        extract_text_pending_gazettes(
            database_mock,
            self.storage_mock,
            self.index_mock,
            text_extraction_function,
        )

        database_mock.get_pending_gazettes.assert_called_once()
        self.assert_called_twice(self.storage_mock.get_file)
        self.assert_called_twice(text_extraction_function.extract_text)
        database_mock.set_gazette_as_processed.assert_called_once()
        self.index_mock.index_document.assert_called_once()
        self.file_should_not_exist(
            text_extraction_function.extract_text.call_args.args[0]
        )

    def test_gazette_url(self):
        expected_data = self.data[0].copy()
        expected_data["url"] = f"http://test.com/{expected_data['file_path']}"

        extract_text_pending_gazettes(
            self.database_mock,
            self.storage_mock,
            self.index_mock,
            self.text_extraction_function,
        )
        self.index_mock.index_document.assert_called_once_with(expected_data)

    def test_upload_gazette_raw_text(self):
        content = "some content"
        gazette = dict(file_path="some_file.pdf", source_text=content)
        upload_gazette_raw_text(gazette, self.storage_mock)
        self.assertEqual(gazette["file_raw_txt"], "http://test.com/some_file.txt")
        self.storage_mock.upload_content.assert_called_once_with(
            "some_file.txt", content
        )
