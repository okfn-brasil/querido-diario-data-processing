import logging
import magic
import os

import subprocess


def check_file_exists(filepath: str):
    if not os.path.exists(filepath):
        raise Exception(f"File does not exists: {filepath}")


def check_file_type_supported(filepath: str) -> None:
    if not is_doc(filepath) and not is_pdf(filepath) and not is_txt(filepath):
        raise Exception("Unsupported file type: " + get_file_type(filepath))


def extract_text(filepath: str) -> str:
    logging.debug(f"Extracting text from {filepath}")
    if is_txt(filepath):
        return filepath
    text_path = filepath + ".txt"
    command = f"java -jar /tika-app.jar --text {filepath}"
    with open(text_path, "w") as f:
        subprocess.run(command, shell=True, check=True, stdout=f)
    return text_path


def get_text_from_file(filepath: str):
    check_file_exists(filepath)
    check_file_type_supported(filepath)
    return extract_text(filepath)


def is_pdf(filepath):
    """
    If the file type is pdf returns True. Otherwise,
    returns False
    """
    return is_file_type(filepath, file_types=["application/pdf"])


def is_doc(filepath):
    """
    If the file type is doc or similar returns True. Otherwise,
    returns False
    """
    file_types = [
        "application/msword",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    return is_file_type(filepath, file_types)


def is_txt(filepath):
    """
    If the file type is txt returns True. Otherwise,
    returns False
    """
    return is_file_type(filepath, file_types=["text/plain"])


def get_file_type(filepath):
    """
    Returns the file's type
    """
    return magic.from_file(filepath, mime=True)


def is_file_type(filepath, file_types):
    """
    Generic method to check if a identified file type matches a given list of types
    """
    return get_file_type(filepath) in file_types
