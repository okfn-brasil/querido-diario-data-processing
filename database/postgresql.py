from typing import Dict, Iterable, Tuple
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
    def __init__(self, host, database, user, password, port):
        self._connection = psycopg2.connect(
            dbname=database, user=user, password=password, host=host, port=port
        )

    def _commit_changes(self, command: str, data: Dict = {}) -> None:
        with self._connection.cursor() as cursor:
            logging.debug(f"Making change: {cursor.query}")
            cursor.execute(command, data)
            self._connection.commit()

    def select(self, command: str) -> Iterable[Tuple]:
        with self._connection.cursor() as cursor:
            cursor.execute(command)
            logging.debug(f"Starting query: {cursor.query}")
            for entry in cursor:
                logging.debug(entry)
                yield entry
            logging.debug(f"Finished query: {cursor.query}")

    def insert(self, command: str, data: Dict = {}):
        logging.debug(f"Inserting:")
        self._commit_changes(command, data)
        logging.debug(f"Finished inserting")

    def update(self, command: str, data: Dict = {}):
        logging.debug(f"Updating:")
        self._commit_changes(command, data)
        logging.debug(f"Finished updating")

    def delete(self, command: str, data: Dict = {}):
        logging.debug(f"Deleting:")
        self._commit_changes(command, data)
        logging.debug(f"Finished deleting")
