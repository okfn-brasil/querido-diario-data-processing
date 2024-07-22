import hashlib, os
import logging

logger = logging.getLogger(__name__)

def hash_content(content: bytes) -> str:
    """
    Receives a content of byte format and returns its SHA-256 hash
    """

    result_hash = hashlib.sha256(content).hexdigest()

    logger.info(f"Hash: {result_hash}")

    return result_hash