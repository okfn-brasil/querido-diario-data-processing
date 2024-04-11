import hashlib
from typing import Dict, Iterable, List

from .interfaces import IndexInterface
from .utils import batched, clean_extra_whitespaces, get_documents_from_query_with_highlights


def extract_themed_excerpts_from_gazettes(
    theme: Dict, gazette_ids: List[str], index: IndexInterface
) -> List[str]:
    ids = []
    for theme_query in theme["queries"]:
        for batch in batched(gazette_ids, 500):
            for excerpt in get_excerpts_from_gazettes_with_themed_query(
                theme_query, batch, index
            ):
                # excerpts with less than 10% of the expected size of excerpt account for 
                # fewer than 1% of excerpts yet their score is usually high
                if len(excerpt["excerpt"]) < 200:
                    continue

                index.index_document(
                    excerpt,
                    document_id=excerpt["excerpt_id"],
                    index=theme["index"],
                    refresh=True,
                )
                ids.append(excerpt["excerpt_id"])

    return ids


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
        "size": 10,
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
