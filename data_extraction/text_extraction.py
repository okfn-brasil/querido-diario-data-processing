import logging
import magic
import os
import subprocess

import requests

from tasks import TextExtractorInterface


class ApacheTikaTextExtractor(TextExtractorInterface):
    def __init__(self, url: str):
        self._url = url

    def _get_file_type(self, filepath: str) -> str:
        """
        Returns the file's type
        """
        return magic.from_file(filepath, mime=True)

    def _return_file_content(self, filepath: str) -> str:
        with open(filepath, "r") as file:
            return file.read()

    def _try_extract_text(self, filepath: str) -> str:
        if self.is_txt(filepath):
            return self._return_file_content(filepath)
        with open(filepath, "rb") as file:
            headers = {"Content-Type": self._get_file_type(filepath)}
            response = requests.put(f"{self._url}/tika", data=file, headers=headers)
            response.encoding = "UTF-8"
            return response.text

    def extract_text(self, filepath: str) -> str:
        logging.debug(f"Extracting text from {filepath}")
        self.check_file_exists(filepath)
        self.check_file_type_supported(filepath)
        try:
            return self._try_extract_text(filepath)
        except Exception as e:
            raise Exception("Could not extract file content") from e

    def check_file_exists(self, filepath: str):
        if not os.path.exists(filepath):
            raise Exception(f"File does not exists: {filepath}")

    def check_file_type_supported(self, filepath: str) -> None:
        if (
            not self.is_doc(filepath)
            and not self.is_pdf(filepath)
            and not self.is_txt(filepath)
        ):
            raise Exception("Unsupported file type: " + self.get_file_type(filepath))

    def is_pdf(self, filepath):
        """
        If the file type is pdf returns True. Otherwise,
        returns False
        """
        return self.is_file_type(filepath, file_types=["application/pdf"])

    def is_doc(self, filepath):
        """
        If the file type is doc or similar returns True. Otherwise,
        returns False
        """
        file_types = [
            "application/msword",
            "application/vnd.oasis.opendocument.text",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        return self.is_file_type(filepath, file_types)

    def is_txt(self, filepath):
        """
        If the file type is txt returns True. Otherwise,
        returns False
        """
        return self.is_file_type(filepath, file_types=["text/plain"])

    def get_file_type(self, filepath):
        """
        Returns the file's type
        """
        return magic.from_file(filepath, mime=True)

    def is_file_type(self, filepath, file_types):
        """
        Generic method to check if a identified file type matches a given list of types
        """
        return self.get_file_type(filepath) in file_types


def get_apache_tika_server_url():
    return os.environ["APACHE_TIKA_SERVER"]


def create_apache_tika_text_extraction() -> TextExtractorInterface:
    apache_tika_server_url = get_apache_tika_server_url()
    return ApacheTikaTextExtractor(apache_tika_server_url)
