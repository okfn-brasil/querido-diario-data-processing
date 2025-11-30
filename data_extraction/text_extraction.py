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
    def __init__(self, url: str, max_retries: int = 3):
        self._url = url
        self._max_retries = max_retries

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
        Extract text from file using streaming when possible to prevent OOM.
        Implements retry logic for transient network errors.
        """
        if self.is_txt(filepath):
            return self._return_file_content(filepath)

        file_size = os.path.getsize(filepath)
        content_type = self._get_file_type(filepath)
        
        # Log requisição ao Tika
        log_tika_request(filepath, file_size, content_type, self._url)
        
        last_exception = None
        for attempt in range(self._max_retries):
            start_time = time.time()
            
            try:
                return self._make_tika_request(filepath, file_size, content_type, start_time)
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                last_exception = e
                
                if attempt < self._max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logging.warning(
                        f"Transient error on attempt {attempt + 1}/{self._max_retries} "
                        f"for {filepath}: {type(e).__name__}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logging.error(
                        f"Failed after {self._max_retries} attempts for {filepath}: {type(e).__name__}"
                    )
            except Exception as e:
                # Non-retryable errors
                raise e
        
        # If we exhausted all retries
        raise last_exception

    def _make_tika_request(self, filepath: str, file_size: int, content_type: str, start_time: float) -> str:
        """Make the actual HTTP request to Tika"""
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
                    timeout=(30, 300),  # (connect timeout, read timeout) in seconds
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                # Check for HTTP errors
                if response.status_code != 200:
                    error_msg = (
                        f"Tika returned HTTP {response.status_code} for {filepath}. "
                        f"Response: {response.text[:500]}"
                    )
                    log_tika_error(
                        filepath,
                        f"HTTPError{response.status_code}",
                        error_msg,
                        duration_ms,
                        file_size=file_size,
                        status_code=response.status_code
                    )
                    raise requests.HTTPError(error_msg)
                
                response.encoding = "UTF-8"
                text = response.text
                
                # Log resposta bem-sucedida
                log_tika_response(filepath, duration_ms, len(text), response.status_code)

                # Explicit cleanup to free memory immediately
                response.close()
                del response
                gc.collect()

                return text
        except requests.exceptions.ConnectionError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Failed to connect to Tika at {self._url}: {str(e)}"
            log_tika_error(
                filepath,
                "ConnectionError",
                error_msg,
                duration_ms,
                file_size=file_size
            )
            logging.error(f"Tika connection error for {filepath}: {error_msg}")
            gc.collect()
            raise
        except requests.exceptions.Timeout as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Tika request timeout after {duration_ms/1000:.1f}s for file: {filepath}"
            log_tika_error(
                filepath,
                "TimeoutError",
                error_msg,
                duration_ms,
                file_size=file_size
            )
            logging.error(f"Tika timeout for {filepath}: {error_msg}")
            gc.collect()
            raise
        except requests.exceptions.ChunkedEncodingError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Chunked encoding error (connection interrupted) for {filepath}: {str(e)}"
            log_tika_error(
                filepath,
                "ChunkedEncodingError",
                error_msg,
                duration_ms,
                file_size=file_size
            )
            logging.error(f"Tika chunked encoding error for {filepath}: {error_msg}")
            gc.collect()
            raise
        except requests.HTTPError as e:
            # Already logged above, just ensure cleanup
            gc.collect()
            raise
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
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            file_type = self._get_file_type(filepath) if os.path.exists(filepath) else "unknown"
            error_details = (
                f"Could not extract file content: {filepath} "
                f"(size: {file_size / 1024 / 1024:.2f}MB, type: {file_type}, "
                f"error: {type(e).__name__}: {str(e)})"
            )
            logging.error(error_details)
            raise Exception(error_details) from e

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
