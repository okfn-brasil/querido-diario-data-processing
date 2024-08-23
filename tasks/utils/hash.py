import hashlib


def hash_content(content: bytes) -> str:
    """
    Receives a content of byte format and returns its md5 hash
    """

    result_hash = hashlib.md5(content).hexdigest()

    return result_hash


def hash_file(file) -> str:
    """
    Generate file md5 hash without hurting memory
    """
    hash = hashlib.md5()
    chunk_size = 128 * hash.block_size

    if isinstance(file, str):
        with open(file, 'rb') as f:
            _chunk_hashing(hash, chunk_size, f)
    else:
        file.seek(0)
        _chunk_hashing(hash, chunk_size, file)
        file.seek(0)

    return hash.hexdigest()


def _chunk_hashing(hash, chunk_size, file):
    for chunk in iter(lambda: file.read(chunk_size), b''): 
        hash.update(chunk)
