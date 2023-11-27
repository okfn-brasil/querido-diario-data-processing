
import unicodedata
from typing import Dict, Iterable

from ..interfaces import DatabaseInterface


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


def get_territorie_info(state: str, name: str, territories: list):

    state = state.strip()
    name = limpar_name(name)

    for territorie in territories:
        territorie_name = limpar_name(territorie["territory_name"])
        if territorie["state"].lower() == state.lower() and territorie_name == name:

            return territorie["id"], territorie["territory_name"], territorie["state_code"]


def limpar_name(name: str):

    clean_name = name.replace("'", "")
    clean_name = unicodedata.normalize("NFD", clean_name)
    clean_name = clean_name.encode("ascii", "ignore").decode("utf-8")
    clean_name = clean_name.lower()
    clean_name = clean_name.strip()

    clean_name = "major isidoro" if clean_name == "major izidoro" else clean_name

    return clean_name
