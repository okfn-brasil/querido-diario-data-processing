import hashlib, os


def hash_content(content: bytes) -> str:
    """
    Receives a content of byte format and returns its SHA-256 hash
    """

    result_hash = hashlib.sha256(content).hexdigest()

    return result_hash