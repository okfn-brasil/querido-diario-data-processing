from typing import Generator, Dict
import abc


class DatabaseInterface(abc.ABC):
    """
    Interface to abstract the iteraction with the database storing data used by the
    tasks
    """

    @abc.abstractmethod
    def get_pending_gazettes() -> Generator:
        """
        Get all gazettes waitning to be processed by the data processing pipeline
        """

    @abc.abstractmethod
    def set_gazette_as_processed(id: int, gazette_file_checksum: str) -> None:
        """
        Set the gazette of the given ID and file checksum as processed
        """


class StorageInterface(abc.ABC):
    """
    Interface to abstract the interaction with the object store system.
    """

    @abc.abstractmethod
    def get_file(file_to_be_downloaded: str, destination) -> None:
        """
        Download the given file key in the destination on the host
        """

    @abc.abstractmethod
    def upload_content(file_key: str, content_to_be_uploaded: str) -> None:
        """
        Upload the given content to the destination on the host
        """


class IndexInterface(abc.ABC):
    """
    Interface to abstract the interaction with the index system
    """

    @abc.abstractmethod
    def create_index(index_name: str) -> None:
        """
        Create the index used by the application
        """

    def index_document(document: Dict, index: str) -> None:
        """
        Upload document to the index
        """

class TextExtractorInterface(abc.ABC):
    def extract_text(self, filepath: str) -> str:
        """
        Extract the text from the given file
        """
