from os import environ
import argparse
import logging

from data_extraction import create_apache_tika_text_extraction
from database import create_database_interface
from storage import create_storage_interface
from index import create_index_interface
from tasks import run_task


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


def gazette_texts_pipeline():
    execution_mode = get_execution_mode()
    database = create_database_interface()
    storage = create_storage_interface()
    index = create_index_interface()
    text_extractor = create_apache_tika_text_extraction()

    themes = run_task("get_themes")

    run_task("create_gazettes_index", index)
    territories = run_task("get_territories", database)
    gazettes_to_be_processed = run_task("get_gazettes_to_be_processed", execution_mode, database)
    indexed_gazette_ids = run_task("extract_text_from_gazettes", gazettes_to_be_processed, territories, database, storage, index, text_extractor)
   
    for theme in themes:
        run_task("create_themed_excerpts_index", theme, index)
        themed_excerpt_ids = run_task("extract_themed_excerpts_from_gazettes", theme, indexed_gazette_ids, index)
        run_task("embedding_rerank_excerpts", theme, themed_excerpt_ids, index)
        run_task("tag_entities_in_excerpts", theme, themed_excerpt_ids, index)


def aggregates_pipeline():
    database = create_database_interface()
    storage = create_storage_interface()

    run_task("create_aggregates_table", database)
    run_task("create_aggregates", database, storage)


def execute_pipeline(pipeline):
    enable_debug_if_necessary()

    if not pipeline or pipeline == "gazette_texts":
        gazette_texts_pipeline()
    elif pipeline == "aggregates":
        aggregates_pipeline()
    else:
        raise ValueError("Pipeline inválido.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pipeline", help="Qual pipeline deve ser executado.")
    args = parser.parse_args()
    execute_pipeline(args.pipeline)
