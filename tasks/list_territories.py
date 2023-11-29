from functools import lru_cache 
from typing import Dict, Iterable
from .interfaces import DatabaseInterface


@lru_cache
def get_territories(
    database: DatabaseInterface,
) -> Iterable[Dict]:
    """
    Example
    -------
    >>> territories = get_territories_gazettes(database)
    """
    command = """SELECT * FROM territories;"""
    territories = [
        _format_territories_data(territory) for territory in database.select(command)
    ]
    return territories


def _format_territories_data(data):
    return {
        "id": data[0],
        "territory_name": data[1],
        "state_code": data[2],
        "state": data[3],
    }
