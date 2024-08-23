import abc
from typing import Dict, Iterable


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
