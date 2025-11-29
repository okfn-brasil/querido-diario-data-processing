import gc
import logging
import os
import time

import magic
import requests

from .interfaces import TextExtractorInterface
from monitoring import log_tika_request, log_tika_response, log_tika_error


class UnsupportedFileTypeError(Exception):
    """Exception raised when a file type is not supported for text extraction."""

    pass


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
        """
        Extract text from file using streaming when possible to prevent OOM
        """
        if self.is_txt(filepath):
            return self._return_file_content(filepath)

        file_size = os.path.getsize(filepath)
        content_type = self._get_file_type(filepath)
        
        # Log requisição ao Tika
        log_tika_request(filepath, file_size, content_type, self._url)
        
        start_time = time.time()
        
        try:
            with open(filepath, "rb") as file:
                headers = {
                    "Content-Type": content_type,
                    "Accept": "text/plain",
                }
                # Use streaming to prevent loading entire file in memory
                response = requests.put(
                    f"{self._url}/tika",
                    data=file,
                    headers=headers,
                    stream=False,  # Tika requires full upload, but we stream the read
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                response.encoding = "UTF-8"
                text = response.text
                
                # Log resposta bem-sucedida
                log_tika_response(filepath, duration_ms, len(text), response.status_code)

                # Explicit cleanup to free memory immediately
                response.close()
                del response
                gc.collect()

                return text
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_type = type(e).__name__
            error_message = str(e)
            
            # Log erro detalhado
            log_tika_error(
                filepath, 
                error_type, 
                error_message, 
                duration_ms,
                file_size=file_size
            )
            
            # Ensure cleanup even on error
            gc.collect()
            raise e

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
        file_type = self.get_file_type(filepath)
        if (
            not self.is_doc(filepath)
            and not self.is_pdf(filepath)
            and not self.is_txt(filepath)
        ):
            raise UnsupportedFileTypeError(f"Unsupported file type: {file_type}")

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

    def is_zip(self, filepath):
        """
        If the file type is zip returns True. Otherwise,
        returns False
        """
        return self.is_file_type(filepath, file_types=["application/zip"])


def get_apache_tika_server_url():
    return os.environ["APACHE_TIKA_SERVER"]


def create_apache_tika_text_extraction() -> TextExtractorInterface:
    apache_tika_server_url = get_apache_tika_server_url()
    return ApacheTikaTextExtractor(apache_tika_server_url)
