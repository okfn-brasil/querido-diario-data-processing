from typing import Dict, Iterable
from ..interfaces import DatabaseInterface


def get_territory_to_data(database: DatabaseInterface):
    territories = _get_territories_gazettes(database)
    territory_to_data = {
        ((t["state_code"], t["territory_name"])): t
        for t in territories
    }
    return territory_to_data


def _get_territories_gazettes(
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
    }
