import logging
from typing import Generator

from .interfaces import DatabaseInterface


def get_pending_gazettes(
    database: DatabaseInterface,
) -> Generator:
    """
    List the gazettes which are waiting to be processed 

    This function access the database containing all the gazettes files found by
    the spider marked as not processed yet.
    """
    logging.info("Listing pending gazettes")
    yield from database.get_pending_gazettes()

