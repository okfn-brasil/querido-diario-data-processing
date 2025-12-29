import abc


class TextExtractorInterface(abc.ABC):
    @abc.abstractmethod
    def extract_text(self, filepath: str) -> str:
        """
        Extract the text from the given file
        """

    @abc.abstractmethod
    def is_zip(self, filepath: str) -> bool:
        """
        Check if the given file is a ZIP archive
        """
