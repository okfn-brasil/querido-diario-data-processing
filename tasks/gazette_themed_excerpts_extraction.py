import hashlib
from typing import Dict, Iterable, List

from .interfaces import IndexInterface
from .utils import clean_extra_whitespaces, get_documents_from_query_with_highlights


def extract_themed_excerpts_from_gazettes(
    theme: Dict, gazette_ids: List[str], index: IndexInterface
) -> List[str]:
    create_index(theme, index)

    ids = []
    for theme_query in theme["queries"]:
        for excerpt in get_excerpts_from_gazettes_with_themed_query(
            theme_query, gazette_ids, index
        ):
            index.index_document(
                excerpt,
                document_id=excerpt["excerpt_id"],
                index=theme["index"],
                refresh=True,
            )
            ids.append(excerpt["excerpt_id"])

    return ids


def create_index(theme: Dict, index: IndexInterface) -> None:
    body = {
        "mappings": {
            "properties": {
                "excerpt_embedding_score": {"type": "rank_feature"},
                "excerpt_tfidf_score": {"type": "rank_feature"},
                "excerpt_subthemes": {"type": "keyword"},
                "excerpt_entities": {"type": "keyword"},
                "excerpt": {
                    "type": "text",
                    "analyzer": "brazilian",
                    "index_options": "offsets",
                    "term_vector": "with_positions_offsets",
                    "fields": {
                        "with_stopwords": {
                            "type": "text",
                            "analyzer": "brazilian_with_stopwords",
                            "index_options": "offsets",
                            "term_vector": "with_positions_offsets",
                        },
                        "exact": {
                            "type": "text",
                            "analyzer": "exact",
                            "index_options": "offsets",
                            "term_vector": "with_positions_offsets",
                        },
                    },
                },
                "excerpt_id": {"type": "keyword"},
                "source_database_id": {"type": "long"},
                "source_index_id": {"type": "keyword"},
                "source_created_at": {"type": "date"},
                "source_date": {"type": "date"},
                "source_edition_number": {"type": "keyword"},
                "source_file_checksum": {"type": "keyword"},
                "source_file_path": {"type": "keyword"},
                "source_file_raw_txt": {"type": "keyword"},
                "source_file_url": {"type": "keyword"},
                "source_is_extra_edition": {"type": "boolean"},
                "source_power": {"type": "keyword"},
                "source_processed": {"type": "boolean"},
                "source_scraped_at": {"type": "date"},
                "source_state_code": {"type": "keyword"},
                "source_territory_id": {"type": "keyword"},
                "source_territory_name": {"type": "keyword"},
                "source_url": {"type": "keyword"},
            }
        },
        "settings": {
            "index": {
              "sort.field": ["source_territory_id", "source_date"],
              "sort.order": ["asc", "desc"]
            },
            "analysis": {
                "filter": {
                    "brazilian_stemmer": {
                        "type": "stemmer",
                        "language": "brazilian",
                    }
                },
                "analyzer": {
                    "brazilian_with_stopwords": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "brazilian_stemmer"],
                    },
                    "exact": {
                        "tokenizer": "standard",
                        "filter": ["lowercase"],
                    },
                },
            }
        },
    }
    index.create_index(index_name=theme["index"], body=body)


def get_excerpts_from_gazettes_with_themed_query(
    query: Dict, gazette_ids: List[str], index: IndexInterface
) -> Iterable[Dict]:
    es_query = get_es_query_from_themed_query(query, gazette_ids, index)
    documents = get_documents_from_query_with_highlights(es_query, index)
    for document in documents:
        gazette = document["_source"]
        excerpts = document["highlight"]["source_text.with_stopwords"]
        for excerpt in excerpts:
            yield {
                "excerpt": preprocess_excerpt(excerpt),
                "excerpt_subthemes": [query["title"]],
                "excerpt_id": generate_excerpt_id(excerpt, gazette),
                "source_index_id": gazette["file_checksum"],
                "source_created_at": gazette["created_at"],
                "source_database_id": gazette["id"],
                "source_date": gazette["date"],
                "source_edition_number": gazette["edition_number"],
                "source_file_raw_txt": gazette["file_raw_txt"],
                "source_is_extra_edition": gazette["is_extra_edition"],
                "source_file_checksum": gazette["file_checksum"],
                "source_file_path": gazette["file_path"],
                "source_file_url": gazette["file_url"],
                "source_power": gazette["power"],
                "source_processed": gazette["processed"],
                "source_scraped_at": gazette["scraped_at"],
                "source_state_code": gazette["state_code"],
                "source_territory_id": gazette["territory_id"],
                "source_territory_name": gazette["territory_name"],
                "source_url": gazette["url"],
            }


def generate_excerpt_id(excerpt: str, gazette: Dict) -> str:
    hash = hashlib.md5()
    hash.update(excerpt.encode())
    return f"{gazette['file_checksum']}_{hash.hexdigest()}"


def get_es_query_from_themed_query(
    query: Dict,
    gazette_ids: List[str],
    index: IndexInterface,
) -> Dict:
    es_query = {
        "query": {"bool": {"must": [], "filter": {"ids": {"values": gazette_ids}}}},
        "size": 100,
        "highlight": {
            "fields": {
                "source_text.with_stopwords": {
                    "type": "unified",
                    "fragment_size": 2000,
                    "number_of_fragments": 10,
                    "pre_tags": [""],
                    "post_tags": [""],
                }
            },
        },
    }

    macro_synonym_block = {"span_or": {"clauses": []}}
    for macro_set in query["term_sets"]:
        proximity_block = {"span_near": {"clauses": [], "slop": 20, "in_order": False}}
        for term_set in macro_set:
            synonym_block = {"span_or": {"clauses": []}}
            for term in term_set:
                phrase_block = {
                    "span_near": {"clauses": [], "slop": 0, "in_order": True}
                }
                tokenized_term = index.analyze(text=term, field="source_text.with_stopwords")
                for token in tokenized_term["tokens"]:
                    word_block = {"span_term": {"source_text.with_stopwords": token["token"]}}
                    phrase_block["span_near"]["clauses"].append(word_block)
                synonym_block["span_or"]["clauses"].append(phrase_block)
            proximity_block["span_near"]["clauses"].append(synonym_block)
        macro_synonym_block["span_or"]["clauses"].append(proximity_block)

    es_query["query"]["bool"]["must"].append(macro_synonym_block)
    return es_query


def preprocess_excerpt(excerpt: str) -> str:
    return clean_extra_whitespaces(excerpt)
