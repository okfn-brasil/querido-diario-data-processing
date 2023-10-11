import re
import hashlib
from io import BytesIO


def clean_extra_whitespaces(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def get_checksum(source_text: str) -> str:
    """Calculate the md5 checksum of text
    by creating a file-like object without reading its
    whole content in memory.

    Example
    -------
    >>> extractor.get_checksum("A simple text")
        'ef313f200597d0a1749533ba6aeb002e'
    """
    file = BytesIO(source_text.encode(encoding="UTF-8"))

    m = hashlib.md5()
    while True:
        d = file.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()