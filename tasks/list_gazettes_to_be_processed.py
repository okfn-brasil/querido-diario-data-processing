"""Tarefa para listar os documentos a ser processados de acordo com o modo de execução"""

import logging
import os
from typing import Dict, Iterable

from database import DatabaseInterface

# Configuration for pagination to prevent OOM
DEFAULT_PAGE_SIZE = 1000
QUERY_PAGE_SIZE = int(os.environ.get("GAZETTE_QUERY_PAGE_SIZE", DEFAULT_PAGE_SIZE))


def get_gazettes_to_be_processed(
    execution_mode: str, database: DatabaseInterface
) -> Iterable[Dict]:
    if execution_mode == "DAILY":
        yield from get_gazettes_extracted_since_yesterday(database)
    elif execution_mode == "ALL":
        yield from get_all_gazettes_extracted(database)
    elif execution_mode == "UNPROCESSED":
        yield from get_unprocessed_gazettes(database)
    else:
        raise Exception(f'Execution mode "{execution_mode}" is invalid.')


def get_gazettes_extracted_since_yesterday(
    database: DatabaseInterface,
) -> Iterable[Dict]:
    """
    List the gazettes which were extracted since yesterday
    Uses pagination to prevent loading all data into memory at once (OOM prevention)
    """
    logging.info("Listing gazettes extracted since yesterday (paginated)")

    offset = 0
    while True:
        command = f"""
        SELECT
            gazettes.id,
            gazettes.source_text,
            gazettes.date,
            gazettes.edition_number,
            gazettes.is_extra_edition,
            gazettes.power,
            gazettes.file_checksum,
            gazettes.file_path,
            gazettes.file_url,
            gazettes.scraped_at,
            gazettes.created_at,
            gazettes.territory_id,
            gazettes.processed,
            territories.name as territory_name,
            territories.state_code
        FROM
            gazettes
        INNER JOIN territories ON territories.id = gazettes.territory_id
        WHERE
            scraped_at > current_timestamp - interval '1 day'
        ORDER BY gazettes.id
        LIMIT {QUERY_PAGE_SIZE} OFFSET {offset}
        ;
        """

        page_results = list(database.select(command))

        if not page_results:
            break

        logging.debug(
            f"Processing page with {len(page_results)} gazettes (offset={offset})"
        )

        for gazette in page_results:
            yield format_gazette_data(gazette)

        offset += QUERY_PAGE_SIZE

        # If we got fewer results than page size, we're done
        if len(page_results) < QUERY_PAGE_SIZE:
            break


def get_all_gazettes_extracted(
    database: DatabaseInterface,
) -> Iterable[Dict]:
    """
    List all the gazettes which were extracted
    Uses pagination to prevent loading all data into memory at once (OOM prevention)
    """
    logging.info("Listing all gazettes extracted (paginated)")

    offset = 0
    while True:
        command = f"""
        SELECT
            gazettes.id,
            gazettes.source_text,
            gazettes.date,
            gazettes.edition_number,
            gazettes.is_extra_edition,
            gazettes.power,
            gazettes.file_checksum,
            gazettes.file_path,
            gazettes.file_url,
            gazettes.scraped_at,
            gazettes.created_at,
            gazettes.territory_id,
            gazettes.processed,
            territories.name as territory_name,
            territories.state_code
        FROM
            gazettes
        INNER JOIN territories ON territories.id = gazettes.territory_id
        ORDER BY gazettes.id
        LIMIT {QUERY_PAGE_SIZE} OFFSET {offset}
        ;
        """

        page_results = list(database.select(command))

        if not page_results:
            break

        logging.debug(
            f"Processing page with {len(page_results)} gazettes (offset={offset})"
        )

        for gazette in page_results:
            yield format_gazette_data(gazette)

        offset += QUERY_PAGE_SIZE

        # If we got fewer results than page size, we're done
        if len(page_results) < QUERY_PAGE_SIZE:
            break


def get_unprocessed_gazettes(
    database: DatabaseInterface,
) -> Iterable[Dict]:
    """
    List all the unprocessed gazettes
    Uses pagination to prevent loading all data into memory at once (OOM prevention)
    """
    logging.info("Listing unprocessed gazettes (paginated)")

    offset = 0
    while True:
        command = f"""
        SELECT
            gazettes.id,
            gazettes.source_text,
            gazettes.date,
            gazettes.edition_number,
            gazettes.is_extra_edition,
            gazettes.power,
            gazettes.file_checksum,
            gazettes.file_path,
            gazettes.file_url,
            gazettes.scraped_at,
            gazettes.created_at,
            gazettes.territory_id,
            gazettes.processed,
            territories.name as territory_name,
            territories.state_code
        FROM
            gazettes
        INNER JOIN territories ON territories.id = gazettes.territory_id
        WHERE
            processed is False
        ORDER BY gazettes.id
        LIMIT {QUERY_PAGE_SIZE} OFFSET {offset}
        ;
        """

        page_results = list(database.select(command))

        if not page_results:
            break

        logging.debug(
            f"Processing page with {len(page_results)} unprocessed gazettes (offset={offset})"
        )

        for gazette in page_results:
            yield format_gazette_data(gazette)

        offset += QUERY_PAGE_SIZE

        # If we got fewer results than page size, we're done
        if len(page_results) < QUERY_PAGE_SIZE:
            break


def format_gazette_data(data):
    return {
        "id": data[0],
        "source_text": data[1],
        "date": data[2],
        "edition_number": data[3],
        "is_extra_edition": data[4],
        "power": data[5],
        "file_checksum": data[6],
        "file_path": data[7],
        "file_url": data[8],
        "scraped_at": data[9],
        "created_at": data[10],
        "territory_id": data[11],
        "processed": data[12],
        "territory_name": data[13],
        "state_code": data[14],
    }
