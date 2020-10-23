from unittest import TestCase
from unittest.mock import MagicMock
import logging
from datetime import date, datetime
import tempfile

from data_extraction import get_text_from_file

from tasks import extract_text_pending_gazettes


class TextExtractionTaskTests(TestCase):
    def setUp(self):
        self.database_mock = MagicMock()
        self.data = [
            {
                "id": id,
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
            }
        ]
        self.database_mock.get_pending_gazettes = MagicMock(return_value=self.data)
        self.storage_mock = MagicMock()
        self.storage_mock.get_file = MagicMock()
        self.storage_mock.upload_file = MagicMock()
        self.text_extraction_function = MagicMock(return_value="/tmp/fake_txt_file")

    def test_database_call(self):
        extract_text_pending_gazettes(
            self.database_mock, self.storage_mock, self.text_extraction_function
        )
        self.database_mock.get_pending_gazettes.assert_called_once()

    def test_stoage_call_to_get_file(self):
        extract_text_pending_gazettes(
            self.database_mock, self.storage_mock, self.text_extraction_function
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
            self.database_mock, self.storage_mock, self.text_extraction_function
        )

        self.text_extraction_function.assert_called_once()
        self.assertEqual(len(self.text_extraction_function.call_args.args), 1)
        self.assertIsInstance(self.text_extraction_function.call_args.args[0], str)

    def test_text_file_upload_call(self):
        extract_text_pending_gazettes(
            self.database_mock, self.storage_mock, self.text_extraction_function
        )
        tmp_text_file = self.storage_mock.get_file.call_args.args[1].name
        self.storage_mock.upload_file.assert_called_once_with(
            "/tmp/fake_txt_file", f'{self.data[0]["file_path"]}.txt'
        )


class TextExtractionTaskFailuresTests(TestCase):
    def setUp(self):
        self.database_mock = MagicMock()
        self.storage_mock = MagicMock()
        self.text_extraction_function = MagicMock()

    def test_failure_get_data_from_database(self):
        # TODO
        pass
        # self.database_mock.get_pending_gazettes = MagicMock(side_effect=Exception("Failed to get pending gazettes from database"))
        # extract_text_pending_gazettes(
        #     self.database_mock, self.storage_mock, self.text_extraction_function
        # )
