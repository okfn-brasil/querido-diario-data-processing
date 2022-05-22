import os
from typing import Dict, List

import sentence_transformers

from .interfaces import IndexInterface
from .utils import get_documents_with_ids


def embedding_rerank_excerpts(
    theme: Dict, excerpt_ids: List[str], index: IndexInterface
) -> None:
    user_folder = os.environ["HOME"]
    model = sentence_transformers.SentenceTransformer(
        f"{user_folder}/models/bert-base-portuguese-cased"
    )
    queries = get_natural_language_queries(theme)
    queries_vectors = model.encode(queries, convert_to_tensor=True)

    excerpts = (
        excerpt["_source"]
        for excerpt in get_documents_with_ids(excerpt_ids, index, theme["index"])
    )
    for excerpt in excerpts:
        excerpt_vector = model.encode(excerpt["excerpt"], convert_to_tensor=True)
        excerpt_max_score = sentence_transformers.util.semantic_search(
            excerpt_vector, queries_vectors, top_k=1
        )
        excerpt["excerpt_embedding_score"] = excerpt_max_score[0][0]["score"]
        index.index_document(
            excerpt,
            document_id=excerpt["excerpt_id"],
            index=theme["index"],
            refresh=True,
        )


def get_natural_language_queries(theme: Dict) -> List[str]:
    return [query["title"] for query in theme["queries"]]
