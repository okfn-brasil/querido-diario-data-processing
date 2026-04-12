import gc
import logging
import os
import random
import time

import magic
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry as Urllib3Retry

from monitoring import log_tika_error, log_tika_request, log_tika_response

from .interfaces import TextExtractorInterface


class UnsupportedFileTypeError(Exception):
    """Exception raised when a file type is not supported for text extraction."""

    pass


class ApacheTikaTextExtractor(TextExtractorInterface):
    def __init__(
        self,
        url: str,
        max_retries: int = 5,
        retry_base_delay: float = 2.0,
        connection_pool_size: int = 10,
    ):
        self._url = url
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay
        self._session = self._create_session(connection_pool_size)

    def _create_session(self, pool_size: int) -> requests.Session:
        """
        Create a requests session with connection pooling and keep-alive.
        This reuses TCP connections and improves performance.
        """
        session = requests.Session()

        # Configure connection pooling
        adapter = HTTPAdapter(
            pool_connections=pool_size,
            pool_maxsize=pool_size,
            max_retries=0,  # We handle retries manually with better logic
            pool_block=False,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers for keep-alive
        session.headers.update({"Connection": "keep-alive"})

        return session

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

        last_exception = None
        for attempt in range(self._max_retries):
            start_time = time.time()

            try:
                return self._make_tika_request(
                    filepath, file_size, content_type, start_time, attempt=attempt
                )
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError,
            ) as e:
                last_exception = e

                if attempt < self._max_retries - 1:
                    # Exponential backoff with jitter to prevent thundering herd
                    base_wait = self._retry_base_delay * (2**attempt)
                    jitter = random.uniform(0, base_wait * 0.1)  # 10% jitter
                    wait_time = base_wait + jitter

                    logging.warning(
                        f"Transient error on attempt {attempt + 1}/{self._max_retries} "
                        f"for {filepath}: {type(e).__name__}. Retrying in {wait_time:.1f}s..."
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

    def _make_tika_request(
        self,
        filepath: str,
        file_size: int,
        content_type: str,
        start_time: float,
        attempt: int = 0,
    ) -> str:
        """Make the actual HTTP request to Tika"""
        log_tika_request(filepath, file_size, content_type, self._url)
        try:
            with open(filepath, "rb") as file:
                headers = {
                    "Content-Type": content_type,
                    "Accept": "text/plain",
                }
                # Use streaming to prevent loading entire file in memory
                # Use session for connection pooling and keep-alive
                response = self._session.put(
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
                        status_code=response.status_code,
                    )
                    raise requests.HTTPError(error_msg)

                response.encoding = "UTF-8"
                text = response.text

                # Log resposta bem-sucedida
                log_tika_response(
                    filepath, duration_ms, len(text), response.status_code
                )

                # Explicit cleanup to free memory immediately
                response.close()
                del response
                gc.collect()

                return text
        except requests.exceptions.ConnectionError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Failed to connect to Tika at {self._url}: {str(e)}"
            log_tika_error(
                filepath, "ConnectionError", error_msg, duration_ms, file_size=file_size
            )
            gc.collect()
            raise
        except requests.exceptions.Timeout:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Tika request timeout after {duration_ms / 1000:.1f}s for file: {filepath}"
            log_tika_error(
                filepath, "TimeoutError", error_msg, duration_ms, file_size=file_size
            )
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
                file_size=file_size,
            )
            gc.collect()
            raise
        except requests.HTTPError:
            # Already logged above, just ensure cleanup
            gc.collect()
            raise
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_type = type(e).__name__
            error_message = str(e)

            # Log erro detalhado
            log_tika_error(
                filepath, error_type, error_message, duration_ms, file_size=file_size
            )

            # Ensure cleanup even on error
            gc.collect()
            raise e

    def extract_text(self, filepath: str) -> str:
        logging.debug(f"Extracting text from {filepath}")
        self.check_file_exists(filepath)
        self.check_file_type_supported(filepath)
        return self._try_extract_text(filepath)

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

    # Read configuration from environment with defaults
    max_retries = int(os.environ.get("TIKA_MAX_RETRIES", "5"))
    retry_base_delay = float(os.environ.get("TIKA_RETRY_BASE_DELAY", "2.0"))
    connection_pool_size = int(os.environ.get("TIKA_CONNECTION_POOL_SIZE", "10"))

    return ApacheTikaTextExtractor(
        apache_tika_server_url,
        max_retries=max_retries,
        retry_base_delay=retry_base_delay,
        connection_pool_size=connection_pool_size,
    )
