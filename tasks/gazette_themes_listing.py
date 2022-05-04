import json
import pathlib
from typing import Dict, List


def get_themes() -> List[Dict]:
    ROOT = pathlib.Path(__file__).parent.parent
    themes_config = ROOT / "config" / "themes_config.json"

    with themes_config.open() as f:
        themes = json.load(f)["themes"]

    return themes
