import hashlib
import logging
from typing import Dict, Iterable, List

from .interfaces import IndexInterface


def get_es_query_from_themed_query(
    query: Dict, gazette_ids: List[str],
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

    macro_synonym_block = {"span_or" : {"clauses" : []}}
    for macro_set in query['term_sets']:
        proximity_block = {"span_near": {"clauses": [], "slop": 20, "in_order": False}}
        for term_set in macro_set:
            synonym_block = {"span_or" : {"clauses" : []}}
            for term in term_set:
                phrase_block = {"span_near": {"clauses": [], "slop": 0, "in_order": True}}
                for word in term.split():
                    word_block = {"span_term": {"source_text" : word}}
                    phrase_block["span_near"]["clauses"].append(word_block)
                synonym_block["span_or"]["clauses"].append(phrase_block)
            proximity_block["span_near"]["clauses"].append(synonym_block) 
        macro_synonym_block["span_or"]["clauses"].append(proximity_block)

    es_query["query"]["bool"]["must"].append(macro_synonym_block)
    return es_query


def generate_excerpt_id(excerpt: str, gazette: Dict) -> str:
    hash = hashlib.md5()
    hash.update(excerpt.encode())
    return f"{gazette['file_checksum']}_{hash.hexdigest()}"


def get_excerpts_from_gazettes_with_themed_query(query: Dict, gazette_ids: List[str], index: IndexInterface) -> Iterable[Dict]:
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


def extract_gazette_ids(gazettes: Iterable[Dict]) -> List[str]:
    return [gazette["file_checksum"] for gazette in gazettes]


def create_index(theme: Dict, index: IndexInterface) -> None:
    body = {
        "mappings": {
            "properties": {
                "source_date": {
                    "type": "date",
                },
                "excerpt_embedding_score" : {
                    "type": "rank_feature",
                },
                "excerpt_tfidf_score": {
                    "type": "rank_feature",
                },
            }
        }
    }
    index.create_index(index_name=theme['index'], body=body)


def extract_themed_excerpts_from_gazettes(theme: Dict, gazettes: Iterable[Dict], index: IndexInterface) -> Iterable[Dict]:
    create_index(theme, index)
    gazette_ids = extract_gazette_ids(gazettes)
    for theme_query in theme['queries']:
        excerpts = get_excerpts_from_gazettes_with_themed_query(theme_query, gazette_ids, index)
        for excerpt in excerpts:
            index.index_document(excerpt, document_id=excerpt['excerpt_id'], index=theme['index'])
            yield excerpt

