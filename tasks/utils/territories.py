import unicodedata
from typing import Dict, Iterable

from ..interfaces import DatabaseInterface


def get_territory(target_state: str, target_city: str):
    target_state = target_state.strip().lower()
    target_city = _clear_city_name(target_city)

    database = DatabaseInterface()
    territories = _get_territories_gazettes(database)
    territory_to_data = {
        (_clear_city_name(t["territory_name"]), t["state_code"].lower()): t
        for t in territories
    }
    territory_data = territory_to_data.get((target_city, target_state))
    return territory_data


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
        # "state": data[3],
    }


def _clear_city_name(name: str):
    clean_name = name.replace("'", "")
    clean_name = unicodedata.normalize("NFD", clean_name)
    clean_name = clean_name.encode("ascii", "ignore").decode("utf-8")
    clean_name = clean_name.lower()
    clean_name = clean_name.strip()
    return clean_name
