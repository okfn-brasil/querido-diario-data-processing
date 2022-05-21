from typing import Dict, Iterable, Tuple
import abc


class DatabaseInterface(abc.ABC):
    """
    Interface to abstract the iteraction with the database storing data used by the
    tasks
    """

    @abc.abstractmethod
    def _commit_changes(self, command: str, data: Dict) -> None:
        """
        Make a change in the database and commit it
        """

    @abc.abstractmethod
    def select(self, command: str) -> Iterable[Tuple]:
        """
        Select entries from the database
        """

    @abc.abstractmethod
    def insert(self, command: str, data: Dict) -> None:
        """
        Insert entries into the database
        """

    @abc.abstractmethod
    def update(self, command: str, data: Dict) -> None:
        """
        Update entries from the database
        """

    @abc.abstractmethod
    def delete(self, command: str, data: Dict) -> None:
        """
        Delete entries from the database
        """


class StorageInterface(abc.ABC):
    """
    Interface to abstract the interaction with the object store system.
    """

    @abc.abstractmethod
    def get_file(self, file_to_be_downloaded: str, destination) -> None:
        """
        Download the given file key in the destination on the host
        """

    @abc.abstractmethod
    def upload_content(self, file_key: str, content_to_be_uploaded: str) -> None:
        """
        Upload the given content to the destination on the host
        """


class IndexInterface(abc.ABC):
    """
    Interface to abstract the interaction with the index system
    """

    @abc.abstractmethod
    def create_index(self, index_name: str, body: Dict) -> None:
        """
        Create the index used by the application
        """

    @abc.abstractmethod
    def refresh_index(self, index_name: str) -> None:
        """
        Refreshes the index to make it up-to-date for future searches
        """

    @abc.abstractmethod
    def index_document(
        self, document: Dict, document_id: str, index: str, refresh: bool
    ) -> None:
        """
        Upload document to the index
        """

    @abc.abstractmethod
    def search(self, query: Dict, index: str) -> Dict:
        """
        Searches the index with the provided query
        """

    @abc.abstractmethod
    def paginated_search(
        self, query: Dict, index: str, keep_alive: str
    ) -> Iterable[Dict]:
        """
        Searches the index with the provided query, with pagination
        """


class TextExtractorInterface(abc.ABC):
    @abc.abstractmethod
    def extract_text(self, filepath: str) -> str:
        """
        Extract the text from the given file
        """
