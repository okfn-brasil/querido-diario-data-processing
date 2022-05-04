from typing import Dict, Iterable
import os
import logging

import psycopg2

from tasks import DatabaseInterface


def get_database_name():
    return os.environ["POSTGRES_DB"]


def get_database_user():
    return os.environ["POSTGRES_USER"]


def get_database_password():
    return os.environ["POSTGRES_PASSWORD"]


def get_database_host():
    return os.environ["POSTGRES_HOST"]


def get_database_port():
    return os.environ["POSTGRES_PORT"]


def create_database_interface() -> DatabaseInterface:
    return PostgreSQL(
        get_database_host(),
        get_database_name(),
        get_database_user(),
        get_database_password(),
        get_database_port(),
    )


class PostgreSQL(DatabaseInterface):

    SELECT_PENDING_GAZETTES = """SELECT gazettes.id,
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
                                    FROM gazettes
                                    INNER JOIN territories ON territories.id = gazettes.territory_id
                                    WHERE processed is False;"""

    UPDATE_GAZETTE_AS_PROCESSED = """UPDATE gazettes
                                        SET processed = True
                                        WHERE id = %(id)s
                                        AND file_checksum = %(file_checksum)s;"""

    def __init__(self, host, database, user, password, port):
        self._connection = psycopg2.connect(
            dbname=database, user=user, password=password, host=host, port=port
        )

    def format_gazette_data(self, data):
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

    def get_pending_gazettes(self) -> Iterable[Dict]:
        with self._connection.cursor() as cursor:
            cursor.execute(self.SELECT_PENDING_GAZETTES)
            logging.debug(cursor.query)
            for gazette_data in cursor:
                logging.debug(gazette_data)
                yield self.format_gazette_data(gazette_data)
            logging.debug("No more gazettes to be processed")

    def set_gazette_as_processed(self, id: int, gazette_file_checksum: str) -> None:
        logging.debug(f"Marking {id}({gazette_file_checksum}) as processed")
        with self._connection.cursor() as cursor:
            cursor.execute(
                self.UPDATE_GAZETTE_AS_PROCESSED,
                {"id": id, "file_checksum": gazette_file_checksum},
            )
            self._connection.commit()
