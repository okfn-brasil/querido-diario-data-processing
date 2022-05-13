import os
from typing import Dict, List

import sentence_transformers

from .interfaces import IndexInterface


def embedding_rerank_excerpts(
    theme: Dict, excerpt_ids: List[str], index: IndexInterface
) -> List[str]:
    user_folder = os.environ["HOME"]
    model = sentence_transformers.SentenceTransformer(
        f"{user_folder}/models/bert-base-portuguese-cased"
    )
    queries = get_natural_language_queries(theme)
    queries_vectors = model.encode(queries, convert_to_tensor=True)
    excerpts = get_excerpts_with_ids(theme, excerpt_ids, index)

    for excerpt in excerpts:
        excerpt_vector = model.encode(excerpt["excerpt"], convert_to_tensor=True)
        excerpt_max_score = sentence_transformers.util.semantic_search(
            excerpt_vector, queries_vectors, top_k=1
        )
        subthemes = list(
            set(
                excerpt["excerpt_subthemes"]
                + [queries[excerpt_max_score[0][0]["corpus_id"]]]
            )
        )
        excerpt.update(
            {
                "excerpt_embedding_score": excerpt_max_score[0][0]["score"],
                "excerpt_subthemes": subthemes,
            }
        )
        index.index_document(
            excerpt,
            document_id=excerpt["excerpt_id"],
            index=theme["index"],
            refresh=True,
        )

    return excerpt_ids


def get_excerpts_with_ids(theme: Dict, excerpt_ids: List[str], index: IndexInterface) -> List[Dict]:
    index.refresh_index(theme["index"])
    query_filter_by_ids = {"query": {"bool": {"filter": {"ids": {"values": excerpt_ids}}}}, "size": 100}
    for result in index.paginated_search(query_filter_by_ids, index=theme["index"]):
        hits = [hit for hit in result["hits"]["hits"]]
        for hit in hits:
            excerpt = hit["_source"]
            yield excerpt


def get_natural_language_queries(theme: Dict) -> List[str]:
    return [query["natural_language"] for query in theme["queries"]]
