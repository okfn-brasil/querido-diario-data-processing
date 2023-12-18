from typing import Dict, Iterable, List

from ..interfaces import IndexInterface


def get_documents_with_ids(
    ids: List[str], index: IndexInterface, index_name: str = ""
) -> Iterable[Dict]:
    query_filter_by_ids = {
        "query": {"bool": {"filter": {"ids": {"values": ids}}}},
        "size": 100,
    }
    yield from get_documents_from_query(query_filter_by_ids, index, index_name)


def get_documents_from_query(
    query: Dict, index: IndexInterface, index_name: str = ""
) -> Iterable[Dict]:
    index.refresh_index(index_name)
    documents = (
        hit
        for result in index.paginated_search(query, index=index_name)
        for hit in result["hits"]["hits"]
    )
    yield from documents


def get_documents_from_query_with_highlights(
    query: Dict, index: IndexInterface, index_name: str = ""
) -> Iterable[Dict]:
    index.refresh_index(index_name)
    documents = (
        hit
        for result in index.paginated_search(query, index=index_name)
        for hit in result["hits"]["hits"]
        if hit.get("highlight")
    )
    yield from documents
