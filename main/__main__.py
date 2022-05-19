from os import environ
import logging

from data_extraction import create_apache_tika_text_extraction
from database import create_database_interface
from storage import create_storage_interface
from index import create_index_interface
from tasks import (
    embedding_rerank_excerpts,
    extract_text_from_gazettes,
    extract_themed_excerpts_from_gazettes,
    get_gazettes_to_be_processed,
    get_themes,
    tag_entities_in_excerpts,
    tfidf_rerank_excerpts,
)


def is_debug_enabled():
    return environ.get("DEBUG", "0") == "1"


def enable_debug_if_necessary():
    """
    Enable debug logs with the DEBUG variable is ser to 1
    """
    if is_debug_enabled():
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Debug enabled")


def get_execution_mode():
    return environ.get("EXECUTION_MODE", "DAILY")


def execute_pipeline():
    enable_debug_if_necessary()

    execution_mode = get_execution_mode()
    database = create_database_interface()
    storage = create_storage_interface()
    index = create_index_interface()
    text_extractor = create_apache_tika_text_extraction()
    themes = get_themes()

    gazettes_to_be_processed = get_gazettes_to_be_processed(execution_mode, database)
    indexed_gazette_ids = extract_text_from_gazettes(
        gazettes_to_be_processed, database, storage, index, text_extractor
    )
    for theme in themes:
        if theme['index'] != 'educacao':
            continue
        themed_excerpt_ids = extract_themed_excerpts_from_gazettes(
            theme, indexed_gazette_ids, index
        )
        #embedding_rerank_excerpts(theme, themed_excerpt_ids, index)
        #tag_entities_in_excerpts(theme, themed_excerpt_ids, index)
        #tfidf_rerank_excerpts(theme, index)


if __name__ == "__main__":
    execute_pipeline()
