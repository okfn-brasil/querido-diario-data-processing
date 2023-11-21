import logging
from typing import Dict, Iterable

from .interfaces import DatabaseInterface


def get_territories_gazettes(
    database: DatabaseInterface,
) -> Iterable[Dict]:

    command = """
    SELECT 
        *
    FROM
        territories
    ;
    """

    territories = [format_territories_data(territory) for territory in database.select(command)]

    return territories


def format_territories_data(data):
    return {
        "id": data[0],
        "territory_name": data[1],
        "state_code": data[2],
        "state": data[3],
    }