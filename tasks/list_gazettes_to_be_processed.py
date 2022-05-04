import logging
from typing import Dict, Iterable

from .interfaces import DatabaseInterface


def get_gazettes_extracted_since_yesterday(
    database: DatabaseInterface,
) -> Iterable[Dict]:
    """
    List the gazettes which were extracted since yesterday
    """
    logging.info("Listing gazettes extracted since yesterday")

    command = """
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
    ;
    """
    for gazette in database.select(command):
        yield format_gazette_data(gazette)


def get_all_gazettes_extracted(
    database: DatabaseInterface,
) -> Iterable[Dict]:
    """
    List all the gazettes which were extracted
    """
    logging.info("Listing all gazettes extracted")

    command = """
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
    ;
    """
    for gazette in database.select(command):
        yield format_gazette_data(gazette)


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

