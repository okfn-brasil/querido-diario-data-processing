import re
from typing import Dict, List

from .interfaces import IndexInterface
from .utils import (
    get_documents_from_query_with_highlights,
    get_documents_with_ids,
)


def tag_entities_in_excerpts(
    theme: Dict, excerpt_ids: List[str], index: IndexInterface
) -> None:
    tag_theme_cases(theme, excerpt_ids, index)
    tag_cnpjs(theme, excerpt_ids, index)


def tag_theme_cases(theme: Dict, excerpt_ids: List[str], index: IndexInterface) -> None:
    cases = theme["entities"]["cases"]
    es_queries = [get_es_query_from_entity_case(case, excerpt_ids) for case in cases]
    for case, es_query in zip(cases, es_queries):
        documents = get_documents_from_query_with_highlights(
            es_query, index, theme["index"]
        )
        for document in documents:
            excerpt = document["_source"]
            highlight = document["highlight"][
                "excerpt.with_stopwords"
            ][0]
            excerpt.update(
                {
                    "excerpt_entities": list(
                        set(excerpt.get("excerpt_entities", [])) | {case["title"]}
                    ),
                    "excerpt": highlight,
                }
            )
            index.index_document(
                excerpt,
                document_id=excerpt["excerpt_id"],
                index=theme["index"],
                refresh=True,
            )


def get_es_query_from_entity_case(
    case: Dict,
    excerpt_ids: List[str],
) -> Dict:
    es_query = {
        "query": {"bool": {"should": [], "filter": {"ids": {"values": excerpt_ids}}}},
        "size": 100,
        "highlight": {
            "fields": {
                "excerpt.with_stopwords": {  # Allows tagging phrases containing stopwords correctly
                    "type": "fvh",  # Only highlighter to tag phrases correctly and not the tokens individually
                    "matched_fields": ["excerpt", "excerpt.with_stopwords"],
                    "fragment_size": 10000,
                    "number_of_fragments": 1,
                    "pre_tags": [f"<{case['category']}>"],
                    "post_tags": [f"</{case['category']}>"],
                }
            },
        },
    }
    for value in case["values"]:
        es_query["query"]["bool"]["should"].append(
            {"match_phrase": {"excerpt.with_stopwords": value}}
        )

    return es_query


def tag_cnpjs(theme: Dict, excerpt_ids: List[str], index: IndexInterface) -> None:
    excerpts = (
        document["_source"]
        for document in get_documents_with_ids(excerpt_ids, index, theme["index"])
    )
    cnpj_regex = re.compile(
        r"""
        (^|[^\d])                                              # left boundary: start of string or not-a-digit
        (\d\.?\d\.?\d\.?\d\.?\d\.?\d\.?\d\.?\d/?\d{4}-?\d{2})  # cnpj
        ($|[^\d])                                              # right boundary: end of string or not-a-digit
        """,
        re.VERBOSE,
    )
    for excerpt in excerpts:
        found_cnpjs = re.findall(cnpj_regex, excerpt["excerpt"])
        if not found_cnpjs:
            continue

        for _, cnpj, _ in set(found_cnpjs):
            excerpt["excerpt"] = excerpt["excerpt"].replace(
                cnpj, f"<entidadecnpj>{cnpj}</entidadecnpj>"
            )

        excerpt["excerpt_entities"] = list(
            set(excerpt.get("excerpt_entities", [])) | {"CNPJ"}
        )
        index.index_document(
            excerpt,
            document_id=excerpt["excerpt_id"],
            index=theme["index"],
            refresh=True,
        )
