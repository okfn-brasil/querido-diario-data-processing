from typing import Union
from ..interfaces import DatabaseInterface


def zip_needs_upsert(hx: Union[str, bytes], zip_path:str, database:DatabaseInterface):
    """
    Verifies if zip need an upsert to the database (update or insert)
    """
    
    need_update = True

    query_existing_aggregate = list(database.select(f"SELECT hash_info FROM aggregates \
                                            WHERE file_path='{zip_path}';"))

    if query_existing_aggregate:
        need_update = hx != query_existing_aggregate[0][0]

    return need_update