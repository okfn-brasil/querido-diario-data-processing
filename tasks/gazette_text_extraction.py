import logging
import tempfile

from .interfaces import DatabaseInterface, StorageInterface


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


def get_text_file_name_in_remote_storage(gazette) -> str:
    """
    Build the file name which should be used to store the file with the gazette's text
    in the remote object storage
    """
    return f"{gazette['file_path']}.txt"


def extract_text_pending_gazettes(
    database: DatabaseInterface, storage: StorageInterface, text_extractor_function
) -> None:
    """
    Process the gazettes files waiting to extract the text

    This function access the database containing all the gazettes files found by
    the spider and extract the text from the gazettes marked as not processed yet.
    """
    logging.info("Starting text extraction from pending gazettes")
    for gazette in database.get_pending_gazettes():
        logging.debug(f"Processing gazette {gazette['file_path']}")
        gazette_file = download_gazette_file(gazette, storage)
        gazette_text_file = text_extractor_function(gazette_file)
        storage.upload_file(
            gazette_text_file, get_text_file_name_in_remote_storage(gazette)
        )
        database.set_gazette_as_processed(gazette["id"], gazette["file_checksum"])
