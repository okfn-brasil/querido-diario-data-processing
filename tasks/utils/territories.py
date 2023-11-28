import unicodedata
from typing import Dict, Iterable

from ..interfaces import DatabaseInterface


def get_territories_gazettes(
    database: DatabaseInterface,
) -> Iterable[Dict]:
    """
    Example
    -------
    >>> from tasks.utils import get_territories_gazettes
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


def get_territorie_info(state: str, name: str, territories: list):
    state = state.strip()
    name = limpar_name(name)
    for territorie in territories:
        territorie_name = limpar_name(territorie["territory_name"])
        if territorie["state"].lower() == state.lower() and territorie_name == name:
            return (
                territorie["id"],
                territorie["territory_name"],
                territorie["state_code"],
            )


def limpar_name(name: str):
    clean_name = name.replace("'", "")
    clean_name = unicodedata.normalize("NFD", clean_name)
    clean_name = clean_name.encode("ascii", "ignore").decode("utf-8")
    clean_name = clean_name.lower()
    clean_name = clean_name.strip()
    return clean_name
