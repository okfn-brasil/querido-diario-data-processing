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
    get_all_gazettes_extracted,
    get_gazettes_extracted_since_yesterday,
    get_themes,
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


def daily_processing():
    """
    Processes all gazettes that were extracted since yesterday
    """
    enable_debug_if_necessary()
    database = create_database_interface()
    storage = create_storage_interface()
    index = create_index_interface()
    text_extractor = create_apache_tika_text_extraction()
    gazettes_to_be_processed = get_gazettes_extracted_since_yesterday(database)
    indexed_gazettes = extract_text_from_gazettes(
        gazettes_to_be_processed, storage, index, text_extractor
    )
    themes = get_themes()
    for theme in themes:
        themed_excerpts = extract_themed_excerpts_from_gazettes(
            theme, indexed_gazettes, index
        )
        embedding_rerank_excerpts(theme, themed_excerpts, index)
        tfidf_rerank_excerpts(theme, index)


def process_all():
    """
    Processes all available gazettes
    """
    enable_debug_if_necessary()
    database = create_database_interface()
    storage = create_storage_interface()
    index = create_index_interface()
    text_extractor = create_apache_tika_text_extraction()
    gazettes_to_be_processed = get_all_gazettes_extracted(database)
    indexed_gazettes = extract_text_from_gazettes(
        gazettes_to_be_processed, storage, index, text_extractor
    )
    themes = get_themes()
    for theme in themes:
        themed_excerpts = extract_themed_excerpts_from_gazettes(
            theme, indexed_gazettes, index
        )
        embedding_rerank_excerpts(theme, themed_excerpts, index)
        tfidf_rerank_excerpts(theme, index)


def execute_pipeline():
    pipeline = environ.get("PIPELINE")
    if pipeline == "DAILY":
        daily_processing()
    elif pipeline == "ALL":
        process_all()
    else:
        daily_processing()


if __name__ == "__main__":
    execute_pipeline()
