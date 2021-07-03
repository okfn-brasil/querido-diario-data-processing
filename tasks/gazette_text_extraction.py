import logging
import tempfile
import os
from pathlib import Path
from typing import Dict

from .interfaces import DatabaseInterface, StorageInterface, IndexInterface, TextExtractorInterface


def get_gazette_file_key_used_in_storage(gazette) -> str:
    """
    Get the file key used to store the gazette in the object storage
    """
    return gazette["file_path"]


def download_gazette_file(gazette, storage: StorageInterface) -> str:
    """
    Download the file from the object storage and write it down in the local
    disk to allow the text extraction
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        gazette_file_key = get_gazette_file_key_used_in_storage(gazette)
        storage.get_file(gazette_file_key, tmpfile)
        return tmpfile.name


def delete_gazette_files(gazette_file: str) -> None:
    """
    Removes the files used to process the gazette content.
    """
    os.remove(gazette_file)


def try_to_extract_content(gazette_file: str, text_extractor: TextExtractorInterface) -> str:
    """
    Calls the function to extract the content from the gazette file. If it fails
    remove the gazette file and raise an exception
    """
    try:
        return text_extractor.extract_text(gazette_file)
    except Exception as e:
        os.remove(gazette_file)
        raise e

def get_file_endpoint() -> str:
    """
    Get the endpoint where the gazette files can be downloaded.
    """
    return os.environ["QUERIDO_DIARIO_FILES_ENDPOINT"]

def get_gazette_text_and_define_url(
    gazette: Dict, gazette_file: str, text_extractor: TextExtractorInterface
):
    """
    Extract file content and define the url to access the file in the storage
    """
    gazette["source_text"] = try_to_extract_content(gazette_file, text_extractor)
    file_endpoint = get_file_endpoint()
    gazette["url"] = f"{file_endpoint}/{gazette['file_path']}"

def upload_gazette_raw_text(
    gazette: Dict, storage
):
    """
    Define gazette raw text
    """
    file_raw_txt = Path(gazette['file_path']).with_suffix(".txt").as_posix()
    storage.upload_content(file_raw_txt, gazette["source_text"])
    logging.debug(f"file_raw_txt uploaded {file_raw_txt}")
    file_endpoint = get_file_endpoint()
    gazette["file_raw_txt"] = f"{file_endpoint}/{file_raw_txt}"


def try_process_gazette_file(
    gazette: Dict,
    database: DatabaseInterface,
    storage: StorageInterface,
    index: IndexInterface,
    text_extractor: TextExtractorInterface,
) -> None:
    """
    Do all the work to extract the content from the gazette files
    """
    logging.debug(f"Processing gazette {gazette['file_path']}")
    gazette_file = download_gazette_file(gazette, storage)
    get_gazette_text_and_define_url(gazette, gazette_file, text_extractor)
    upload_gazette_raw_text(gazette, storage)
    index.index_document(gazette)
    database.set_gazette_as_processed(gazette["id"], gazette["file_checksum"])
    delete_gazette_files(gazette_file)


def process_gazette_file(
    gazette: Dict,
    database: DatabaseInterface,
    storage: StorageInterface,
    index: IndexInterface,
    text_extractor: TextExtractorInterface,
) -> None:
    """
    Try to process the gazette file. If an exception happen log a warning message
    and return.
    """
    try:
        try_process_gazette_file(
            gazette, database, storage, index, text_extractor
        )
    except Exception as e:
        logging.warning(f"Could process gazette: {gazette['file_path']}. Cause: {e}")


def extract_text_pending_gazettes(
    database: DatabaseInterface,
    storage: StorageInterface,
    index: IndexInterface,
    text_extractor: TextExtractorInterface,
) -> None:
    """
    Process the gazettes files waiting to extract the text

    This function access the database containing all the gazettes files found by
    the spider and extract the text from the gazettes marked as not processed yet.
    """
    logging.info("Starting text extraction from pending gazettes")
    for gazette in database.get_pending_gazettes():
        process_gazette_file(gazette, database, storage, index, text_extractor)
