from datetime import date, datetime
from dataclasses import dataclass


@dataclass
class GazetteSegment:
    """
    Dataclass to represent a gazette segment of a association
    related to a city
    """
    id: str
    territory_name: str
    source_text: str
    date: date
    edition_number: str
    is_extra_edition: bool
    power: str
    file_checksum: str
    scraped_at: datetime
    created_at: datetime
    processed: bool
    file_path: str
    file_url: str
    state_code: str
    territory_id: str
    file_raw_txt: str
    url: str