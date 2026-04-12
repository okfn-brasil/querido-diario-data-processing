import types
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from data_extraction import (
    ApacheTikaTextExtractor,
    TextExtractorInterface,
    create_apache_tika_text_extraction,
)


class ApacheTikaTextExtractorTest(TestCase):
    def setUp(self):
        self.url = "http://localhost:9998"
        self.extractor = ApacheTikaTextExtractor(self.url)

    def test_text_extractor_wrapper_creation(self):
        self.assertEqual(self.url, self.extractor._url)

    @patch("data_extraction.text_extraction.requests.Session")
    @patch("builtins.open", new_callable=mock_open, read_data=b"")
    @patch("magic.from_file", return_value="application/pdf")
    def test_request_is_sent_to_apache_tika_server(
        self, magic_mock, open_mock, session_mock
    ):
        # Configure mock session and response
        mock_response = MagicMock(status_code=200, text="")
        mock_response.close = MagicMock()
        mock_session_instance = MagicMock()
        mock_session_instance.put = MagicMock(return_value=mock_response)
        session_mock.return_value = mock_session_instance

        # Create extractor with mocked session
        extractor = ApacheTikaTextExtractor(self.url)
        filepath = "tests/data/fake_gazette.pdf"
        expected_headers = {"Content-Type": "application/pdf", "Accept": "text/plain"}
        extractor.extract_text(filepath)

        magic_mock.assert_called_with(filepath, mime=True)
        call_kwargs = mock_session_instance.put.call_args
        self.assertEqual(call_kwargs[0][0], f"{self.url}/tika")
        self.assertIsInstance(call_kwargs[1]["data"], types.GeneratorType)
        self.assertEqual(call_kwargs[1]["headers"], expected_headers)
        self.assertEqual(call_kwargs[1]["stream"], False)
        self.assertEqual(call_kwargs[1]["timeout"], (30, 300))

    @patch("data_extraction.text_extraction.requests.Session")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("magic.from_file", return_value="application/pdf")
    def test_request_reponse_return(self, magic_mock, open_mock, session_mock):
        # Configure mock session and response
        mock_response = MagicMock(status_code=200, text="Fake gazette content")
        mock_response.close = MagicMock()
        mock_session_instance = MagicMock()
        mock_session_instance.put = MagicMock(return_value=mock_response)
        session_mock.return_value = mock_session_instance

        # Create extractor with mocked session
        extractor = ApacheTikaTextExtractor(self.url)
        text = extractor.extract_text("tests/data/fake_gazette.pdf")
        self.assertEqual("Fake gazette content", text)

    @patch("data_extraction.text_extraction.requests.Session")
    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch("magic.from_file", return_value="application/pdf")
    def test_odt_file_content_extraction(self, magic_mock, open_mock, session_mock):
        # Configure mock session to raise exception
        mock_session_instance = MagicMock()
        mock_session_instance.put = MagicMock(side_effect=Exception())
        session_mock.return_value = mock_session_instance

        # Create extractor with mocked session
        extractor = ApacheTikaTextExtractor(self.url)
        with self.assertRaises(Exception):
            extractor.extract_text("tests/data/fake_gazette.pdf")

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

    def test_chunk_file_generator_yields_chunks(self):
        filepath = "tests/data/fake_gazette.pdf"
        extractor = ApacheTikaTextExtractor(self.url, chunk_size=64)
        chunks = list(extractor._chunk_file_generator(filepath))
        self.assertGreater(len(chunks), 0)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 64)
        import os

        self.assertEqual(sum(len(c) for c in chunks), os.path.getsize(filepath))

    def test_chunk_file_generator_is_generator(self):
        filepath = "tests/data/fake_gazette.pdf"
        extractor = ApacheTikaTextExtractor(self.url)
        gen = extractor._chunk_file_generator(filepath)
        self.assertIsInstance(gen, types.GeneratorType)

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
