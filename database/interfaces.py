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
