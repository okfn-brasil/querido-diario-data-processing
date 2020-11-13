import logging
import tempfile
import os
from typing import Dict

from .interfaces import DatabaseInterface, StorageInterface, IndexInterface


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


def load_gazette_content(gazette: Dict, gazette_text_file: str) -> None:
    """
    Load the gazette content in the gazette dictionary
    """
    with open(gazette_text_file, "r") as f:
        gazette["source_text"] = f.read()


def delete_gazette_files(gazette_file: str, gazette_text_file: str) -> None:
    """
    Removes the files used to process the gazette content.
    """
    os.remove(gazette_file)
    os.remove(gazette_text_file)


def try_to_extract_content(gazette_file: str, text_extractor_function) -> str:
    """
    Calls the function to extract the content from the gazette file. If it fails
    remove the gazette file and raise an exception
    """
    try:
        return text_extractor_function(gazette_file)
    except Exception as e:
        os.remove(gazette_file)
        raise e


def try_process_gazette_file(
    gazette: Dict,
    database: DatabaseInterface,
    storage: StorageInterface,
    index: IndexInterface,
    text_extractor_function,
) -> None:
    """
    Do all the work to extract the content from the gazette files
    """
    logging.debug(f"Processing gazette {gazette['file_path']}")
    gazette_file = download_gazette_file(gazette, storage)
    gazette_text_file = try_to_extract_content(gazette_file, text_extractor_function)
    load_gazette_content(gazette, gazette_text_file)
    index.index_document(gazette)
    database.set_gazette_as_processed(gazette["id"], gazette["file_checksum"])
    delete_gazette_files(gazette_file, gazette_text_file)


def process_gazette_file(
    gazette: Dict,
    database: DatabaseInterface,
    storage: StorageInterface,
    index: IndexInterface,
    text_extractor_function,
) -> None:
    """
    Try to process the gazette file. If an exception happen log a warning message
    and return.
    """
    try:
        try_process_gazette_file(
            gazette, database, storage, index, text_extractor_function
        )
    except Exception as e:
        logging.warning(f"Could process gazette: {gazette['file_path']}. Cause: {e}")


def extract_text_pending_gazettes(
    database: DatabaseInterface,
    storage: StorageInterface,
    index: IndexInterface,
    text_extractor_function,
) -> None:
    """
    Process the gazettes files waiting to extract the text

    This function access the database containing all the gazettes files found by
    the spider and extract the text from the gazettes marked as not processed yet.
    """
    logging.info("Starting text extraction from pending gazettes")
    for gazette in database.get_pending_gazettes():
        process_gazette_file(gazette, database, storage, index, text_extractor_function)
