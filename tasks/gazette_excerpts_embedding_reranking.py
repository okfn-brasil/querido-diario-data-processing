from typing import Dict, Iterable, List, Set

import sentence_transformers

from .interfaces import IndexInterface


def embedding_rerank_excerpts(theme: Dict, excerpts: Iterable[Dict], index: IndexInterface) -> None:
    model = sentence_transformers.SentenceTransformer("/root/models/bert-base-portuguese-cased")
    queries = get_natural_language_queries(theme)
    queries_vectors = model.encode(queries, convert_to_tensor=True)
    for excerpt in excerpts:
        excerpt_vector = model.encode(excerpt['excerpt'], convert_to_tensor=True)
        excerpt_max_score = sentence_transformers.util.semantic_search(excerpt_vector, queries_vectors, top_k=1)
        excerpt['excerpt_embedding_score'] = excerpt_max_score[0][0]['score']
        index.index_document(excerpt, document_id=excerpt['excerpt_id'], index=theme['index'])


def get_natural_language_queries(theme: Dict) -> List[str]:
    return [query['natural_language'] for query in theme['queries']]

