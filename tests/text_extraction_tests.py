from unittest import TestCase, skip
from unittest.mock import patch, mock_open, MagicMock
import os

from data_extraction import ApacheTikaTextExtractor, create_apache_tika_text_extraction
from tasks import TextExtractorInterface


class ApacheTikaTextExtractorTest(TestCase):
    def setUp(self):
        self.url = "http://localhost:9998"
        self.extractor = ApacheTikaTextExtractor(self.url)

    def test_text_extractor_wrapper_creation(self):
        self.assertEqual(self.url, self.extractor._url)

    @patch("requests.put")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("magic.from_file", return_value="application/pdf")
    def test_request_is_sent_to_apache_tika_server(
        self, magic_mock, open_mock, request_get_mock
    ):
        filepath = "tests/data/fake_gazette.pdf"
        expected_headers = {"Content-Type": "application/pdf"}
        self.extractor.extract_text(filepath)
        open_mock.assert_called_with(filepath, "rb")
        magic_mock.assert_called_with(filepath, mime=True)
        request_get_mock.assert_called_with(
            f"{self.url}/tika", data=open_mock(), headers=expected_headers
        )

    @patch("requests.put", return_value=MagicMock(text="Fake gazette content"))
    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("magic.from_file", return_value="application/pdf")
    def test_request_reponse_return(self, magic_mock, open_mock, request_get_mock):
        text = self.extractor.extract_text("tests/data/fake_gazette.pdf")
        self.assertEqual("Fake gazette content", text)

    @patch("requests.put", side_effect=Exception())
    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("magic.from_file", return_value="application/pdf")
    def test_odt_file_content_extraction(self, magic_mock, open_mock, request_get_mock):
        with self.assertRaisesRegex(Exception, "Could not extract file content"):
            text = self.extractor.extract_text("tests/data/fake_gazette.pdf")

    def test_extract_from_pdf_file_should_return_text_file(self):
        text = self.extractor.extract_text("tests/data/fake_gazette.pdf")
        self.check_if_text_has_the_fake_text(text)

    def test_extract_from_doc_file_should_return_text_file(self):
        text = self.extractor.extract_text("tests/data/fake_gazette.doc")
        self.check_if_text_has_the_fake_text(text)

    def test_extract_from_docx_file_should_return_text_file(self):
        text = self.extractor.extract_text("tests/data/fake_gazette.docx")
        self.check_if_text_has_the_fake_text(text)

    def test_extract_from_odt_file_should_return_text_file(self):
        text = self.extractor.extract_text("tests/data/fake_gazette.odt")
        self.check_if_text_has_the_fake_text(text)

    def test_extract_from_txt_file_should_return_text_file(self):
        text = self.extractor.extract_text("tests/data/fake_gazette.txt")
        self.check_if_text_has_the_fake_text(text)

    def test_extract_text_from_invalid_file(self):
        self.assertRaisesRegex(
            Exception,
            "File does not exists",
            self.extractor.extract_text,
            "file/does/not/exits",
        )

    def test_extract_from_invalid_file_type_should_fail(self):
        self.assertRaisesRegex(
            Exception,
            "Unsupported file type",
            self.extractor.extract_text,
            "tests/data/fake_gazette.jpg",
        )

    def check_if_text_has_the_fake_text(self, text):
        self.assertIsNotNone(text, msg="Extracted text should not be None")
        self.assertNotEqual(0, len(text), msg="Extracted text should not be empty")
        self.assertIn(
            "Hi this is a document created to test the text extraction for the Querido Diário project.",
            text,
            msg="Extracted text does not have the expected string",
        )


@patch.dict(
    "os.environ",
    {
        "APACHE_TIKA_SERVER": "http://localhost",
    },
)
class FactoryMethodApacheTikaTest(TestCase):
    def test_object_type_returned(self):
        text_extractor = create_apache_tika_text_extraction()
        self.assertIsInstance(text_extractor, TextExtractorInterface)

    def test_object_attributes_returned(self):
        text_extractor = create_apache_tika_text_extraction()
        self.assertEqual("http://localhost", text_extractor._url)
