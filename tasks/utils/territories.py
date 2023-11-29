from typing import Any, Dict, Iterable, Tuple, Union

from slugify import slugify


_territory_slug_to_data_map = {}


def get_territory_slug(name: str, state_code: str) -> str:
    full_name = f"{state_code} {name}"
    stopwords = ["de", "d", "da", "do", "das", "dos"]
    replacements = [("´", "'"), ("`", "'")]
    return slugify(full_name, separator="", stopwords=stopwords, replacements=replacements)


def get_territory_data(identifier: Union[str, Tuple[str, str]], territories: Iterable[Dict[str, Any]]) -> Dict[str, Dict]:
    if isinstance(identifier, tuple):
        territory_name, state_code = identifier
        territory_slug = get_territory_slug(territory_name, state_code)
    elif isinstance(identifier, str):
        territory_slug = identifier
    else:
        raise TypeError(f"Identifier must be 'str' or 'tuple'. Got: {type(identifier)}")

    slug_to_data = get_territory_slug_to_data_map(territories)

    if territory_slug not in slug_to_data:
        raise KeyError(f"Couldn't find info for \"{territory_slug}\"")

    return slug_to_data[territory_slug]


def get_territory_slug_to_data_map(territories: Iterable[Dict[str, Any]]) -> Dict[str, Dict]:
    global _territory_slug_to_data_map
    if not _territory_slug_to_data_map:
        territory_to_data = {
            get_territory_slug(t["territory_name"], t["state_code"]): t
            for t in territories
        }
        _territory_slug_to_data_map = territory_to_data

    return _territory_slug_to_data_map
