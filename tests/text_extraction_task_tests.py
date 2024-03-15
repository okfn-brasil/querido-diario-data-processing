from unittest import TestCase
from unittest.mock import MagicMock, patch
import os
from datetime import date, datetime
import tempfile

from tasks import (
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

    def copy_file_to_temporary_file(self, source_file):
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            with open(source_file, "r+b") as srcfile:
                tmpfile.write(srcfile.read())
            return tmpfile.name


    def file_should_not_exist(self, file_to_check):
        self.assertFalse(
            os.path.exists(file_to_check), msg=f"File {file_to_check} should be deleted"
        )


    def assert_called_twice(self, mock):
        self.assertEqual(mock.call_count, 2, msg="Mock should be called twice")


