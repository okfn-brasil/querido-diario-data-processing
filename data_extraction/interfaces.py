import abc


class TextExtractorInterface(abc.ABC):
    @abc.abstractmethod
    def extract_text(self, filepath: str) -> str:
        """
        Extract the text from the given file
        """
