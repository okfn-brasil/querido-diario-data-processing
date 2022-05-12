import os
from typing import Dict, List

import sentence_transformers

from .interfaces import IndexInterface


def tag_entities_in_excerpts(
    theme: Dict, excerpts: List[Dict], index: IndexInterface
) -> None:
    excerpts_ids = get_excerpts_ids(excerpts)
    for category in theme["entities"]["categories"]:
        cases = get_entities_cases_of_same_category(
            theme["entities"]["cases"], category
        )
        es_query = get_es_query_from_entity_cases(cases, category, excerpts_ids)
        for result in index.paginated_search(es_query, index=theme["index"]):
            hits = [hit for hit in result["hits"]["hits"] if hit.get("highlight")]
            for hit in hits:
                excerpt = hit["_source"]
                tagged_excerpt = hit["highlight"]["excerpt"][0]
                excerpt["excerpt"] = tagged_excerpt
                index.index_document(
                    excerpt,
                    document_id=excerpt["excerpt_id"],
                    index=theme["index"],
                    refresh=True,
                )


def get_excerpts_ids(
    excerpts: List[Dict],
) -> List[str]:
    return [excerpt["excerpt_id"] for excerpt in excerpts]


def get_entities_cases_of_same_category(
    cases: List[Dict], category: Dict
) -> List[Dict]:
    return [case for case in cases if case["category"] == category["name"]]


def get_es_query_from_entity_cases(
    cases: List[Dict],
    category: Dict,
    excerpts_ids: List[str],
) -> Dict:
    es_query = {
        "query": {"bool": {"should": [], "filter": {"ids": {"values": excerpts_ids}}}},
        "size": 10000,
        "highlight": {
            "fields": {
                "excerpt": {
                    "type": "fvh",  # Only highlighter to tag phrases correctly
                    "fragment_size": 10000,
                    "number_of_fragments": 1,
                    "pre_tags": [
                        f"<{category['name']} description={category['description']}>"
                    ],
                    "post_tags": [f"</{category['name']}>"],
                }
            },
        },
    }
    for case in cases:
        es_query["query"]["bool"]["should"].append(
            {"match_phrase": {"excerpt": case["value"]}}
        )

    return es_query
