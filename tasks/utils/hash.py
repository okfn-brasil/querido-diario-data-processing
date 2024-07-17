import hashlib, os

def hash_xml(content : str):
    """
    Receives a text content of a XML file and returns its SHA-256 hash
    """

    seed_hash = bytes(os.environ['SEED_HASH'].encode('utf-8'))

    # Escolha o algoritmo de hash (no caso, SHA-256)
    algorithm = hashlib.sha256
    result_hash = hashlib.pbkdf2_hmac(algorithm().name, content.encode('utf-8'), seed_hash, 100000)

    # Converta o resultado para uma representação legível (hexadecimal)
    hash_hex = result_hash.hex()

    return hash_hex

def hash_zip(zip_content: bytes) -> str:
    """
    Receives the content of a zip file and returns its SHA-256 hash.
    """
    seed_hash = bytes(os.environ.get('SEED_HASH', 'default_seed').encode('utf-8'))

    # Escolha o algoritmo de hash (no caso, SHA-256)
    algorithm = hashlib.sha256
    result_hash = hashlib.pbkdf2_hmac(algorithm().name, zip_content, seed_hash, 100000)

    # Converta o resultado para uma representação legível (hexadecimal)
    hash_hex = result_hash.hex()

    return hash_hex