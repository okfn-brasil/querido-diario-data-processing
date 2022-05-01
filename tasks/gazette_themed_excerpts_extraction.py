import hashlib
import json
import logging
import pathlib
from typing import Dict, Generator, List

from .interfaces import IndexInterface


def get_es_query_from_themed_query(
    query: Dict,
    gazette_ids: List[str],
) -> Dict:
    es_query = {
        "query": {
            "bool": {
                "must": [],
                "filter": {
                    "ids": {
                        "values": gazette_ids 
                    }
                } 
            }
        },
        "size": 10000,
        "highlight": {
            "fields": {
                "source_text": {
                    "type": "unified",
                    "fragment_size": 2000,
                    "number_of_fragments": 10000,
                    "pre_tags": [""],
                    "post_tags": [""],
                }
            },
        },
    }

    near_block = {"span_near": {"clauses": [], "slop": 20, "in_order": False}}
    for term_set in query['term_sets']:
        synonym_block = {"span_or" : {"clauses" : []}}
        for term in term_set:
            phrase_block = {"span_near": {"clauses": [], "slop": 0, "in_order": True}}
            for word in term.split():
                word_block = {"span_term": {"source_text" : word}}
                phrase_block["span_near"]["clauses"].append(word_block)
            synonym_block["span_or"]["clauses"].append(phrase_block)
        near_block["span_near"]["clauses"].append(synonym_block) 

    es_query["query"]["bool"]["must"].append(near_block)

    return es_query


def generate_excerpt_id(excerpt: str, gazette: Dict) -> str:
    hash = hashlib.md5()
    hash.update(excerpt.encode())
    return f"{gazette['file_checksum']}_{hash.hexdigest()}"


def get_excerpts_from_gazettes_with_themed_query(query: Dict, gazette_ids: List[str], index: IndexInterface) -> Generator:
    es_query = get_es_query_from_themed_query(query, gazette_ids)
    result = index.search(es_query)
    hits = result["hits"]["hits"]
    for hit in hits:
        if not hit.get('highlight'):
            continue

        gazette = hit['_source']
        excerpts = hit['highlight']["source_text"]
        for excerpt in excerpts:
            yield {
                "excerpt": excerpt,
                "excerpt_id": generate_excerpt_id(excerpt, gazette),
                "source_index_id": gazette["file_checksum"],
                "source_database_id": gazette["id"],
                "source_date": gazette["date"],
                "source_edition_number": gazette["date"],
                "source_is_extra_edition": gazette["is_extra_edition"],
                "source_power": gazette["power"],
                "source_file_checksum": gazette["file_checksum"],
                "source_file_path": gazette["file_path"],
                "source_file_url": gazette["file_url"],
                "source_scraped_at": gazette["scraped_at"],
                "source_created_at": gazette["created_at"],
                "source_territory_id": gazette["territory_id"],
                "source_processed": gazette["processed"],
                "source_territory_name": gazette["territory_name"],
                "source_state_code": gazette["state_code"],
                "source_url": gazette["url"],
                "source_file_raw_txt": gazette["file_raw_txt"],
            }


def try_extract_themed_excerpts(theme: Dict, gazette_ids: List[str], index: IndexInterface) -> Generator:
    for theme_query in theme['queries']:
        excerpts = get_excerpts_from_gazettes_with_themed_query(theme_query, gazette_ids, index)
        for excerpt in excerpts:
            index.index_document(excerpt, document_id=excerpt['excerpt_id'], index=theme['index'])
            yield excerpt


def extract_themed_excerpts(theme: Dict, gazette_ids: List[str], index: IndexInterface) -> Generator:
    try:
        yield from try_extract_themed_excerpts(theme, gazette_ids, index)
    except Exception as e:
        logging.warning(f"Could not extract theme \"{theme['name']}\". Cause: {e}")


def extract_gazette_ids(gazettes: Generator) -> List[str]:
    return [gazette["file_checksum"] for gazette in gazettes]


def extract_themed_excerpts_from_gazettes(theme: Dict, gazettes: Generator, index: IndexInterface) -> Generator:
    gazette_ids = extract_gazette_ids(gazettes)
    yield from extract_themed_excerpts(theme, gazette_ids, index)

