import collections
from os import environ
import logging

from data_extraction import create_apache_tika_text_extraction
from database import create_database_interface
from storage import create_storage_interface
from index import create_index_interface
from tasks import extract_text_from_gazettes, extract_themed_excerpts_from_gazettes, get_pending_gazettes, get_themes


def is_debug_enabled():
    return environ.get("DEBUG", "0") == "1"


def enable_debug_if_necessary():
    """
    Enable debug logs with the DEBUG variable is ser to 1
    """
    if is_debug_enabled():
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Debug enabled")


def consume(iterator):
    """
    Consumes an entire iterator
    """
    collections.deque(iterator, maxlen=0)


def start_to_process_pending_gazettes():
    """
    Setup objects necessary to extract text from the gazettes and call the
    tasks function to extract the text
    """
    enable_debug_if_necessary()
    database = create_database_interface()
    storage = create_storage_interface()
    index = create_index_interface()
    text_extractor = create_apache_tika_text_extraction()
    pending_gazettes = get_pending_gazettes(database)
    text_extracted_gazettes = extract_text_from_gazettes(pending_gazettes, database, storage, index, text_extractor)
    themes = get_themes()
    for theme in themes:
        themed_excerpts = extract_themed_excerpts_from_gazettes(theme, text_extracted_gazettes, index)
        yield from themed_excerpts
        

if __name__ == "__main__":
    consume(start_to_process_pending_gazettes())
