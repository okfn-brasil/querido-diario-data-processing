from typing import Union
from pathlib import Path
import abc
from io import BytesIO


class StorageInterface(abc.ABC):
    """
    Interface to abstract the interaction with the object store system.
    """

    @abc.abstractmethod
    def get_file(self, file_to_be_downloaded: Union[str, Path], destination) -> None:
        """
        Download the given file key in the destination on the host
        """

    @abc.abstractmethod
    def upload_content(self, file_key: str, content_to_be_uploaded: Union[str, BytesIO]) -> None:
        """
        Upload the given content to the destination on the host
        """

    @abc.abstractmethod
    def copy_file(self, source_file_key: str, destination_file_key: str) -> None:
        """
        Copy the given source file to the destination place on the host
        """

    @abc.abstractmethod
    def delete_file(self, file_key: str) -> None:
        """
        Delete a file on the host.
        """
