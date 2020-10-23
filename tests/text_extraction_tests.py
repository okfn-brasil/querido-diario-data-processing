from unittest import TestCase
import os

from data_extraction import get_text_from_file


class TextExtractionTests(TestCase):
    def tearDown(self):
        self.clean_txt_file_generated_during_tests()

    def clean_txt_file_generated_during_tests(self):
        for root, dirs, files in os.walk("tests/data/"):
            for generated_file in self.get_generated_files_during_tests(root, files):
                print(f"{generated_file}")
                os.remove(generated_file)

    def get_generated_files_during_tests(self, root, files):
        for f in files:
            if ".txt" in f and f != "fake_gazette.txt":
                yield f"{root}{f}"

    def test_extract_text_from_invalid_file(self):
        self.assertRaisesRegex(
            Exception, "File does not exists", get_text_from_file, "file/does/not/exits"
        )

    def test_extract_from_invalid_file_type_should_fail(self):
        self.assertRaisesRegex(
            Exception,
            "Unsupported file type",
            get_text_from_file,
            "tests/data/fake_gazette.jpg",
        )

    def test_extract_from_pdf_file_should_return_text_file(self):
        text_file = get_text_from_file("tests/data/fake_gazette.pdf")
        self.assertIsNotNone(text_file)
        self.assertNotEqual(0, len(text_file))
        self.check_if_text_has_the_fake_text(text_file)

    def test_extract_from_docx_file_should_return_text_file(self):
        text_file = get_text_from_file("tests/data/fake_gazette.docx")
        self.assertIsNotNone(text_file)
        self.assertNotEqual(0, len(text_file))
        self.check_if_text_has_the_fake_text(text_file)

    def test_extract_from_doc_file_should_return_text_file(self):
        text_file = get_text_from_file("tests/data/fake_gazette.doc")
        self.assertIsNotNone(text_file)
        self.assertNotEqual(0, len(text_file))
        self.check_if_text_has_the_fake_text(text_file)

    def test_extract_from_odt_file_should_return_text_file(self):
        text_file = get_text_from_file("tests/data/fake_gazette.odt")
        self.assertIsNotNone(text_file)
        self.assertNotEqual(0, len(text_file))
        self.check_if_text_has_the_fake_text(text_file)

    def test_extract_from_txt_file_should_return_text_file(self):
        text = get_text_from_file("tests/data/fake_gazette.txt")
        self.assertIsNotNone(text)
        self.assertNotEqual(0, len(text))
        self.check_if_text_has_the_fake_text(text)

    def check_if_text_has_the_fake_text(self, text_file_path):
        with open(text_file_path, "r") as f:
            text = f.read()
            self.assertIn(
                "Hi this is a document created to test the text extraction for the Querido Diário project.",
                text,
                msg="Extracted text does not have the expected string",
            )
