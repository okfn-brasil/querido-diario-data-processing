"""Tarefa para listar excertos temáticos existentes no índice para re-execução do embedding"""

import logging
from typing import Dict, List

from index import IndexInterface


def get_themed_excerpt_ids_without_embedding(
    theme: Dict, index: IndexInterface
) -> List[str]:
    """
    Retorna IDs de todos os excertos do índice temático que ainda não possuem
    excerpt_embedding_score, para permitir re-execução ad-hoc do reranqueamento.
    """
    index_name = theme["index"]
    logging.info(f"Buscando excertos sem embedding no índice {index_name}")

    query = {
        "query": {
            "bool": {"must_not": {"exists": {"field": "excerpt_embedding_score"}}}
        },
        "_source": False,
        "size": 1000,
    }

    ids = []
    for page in index.paginated_search(query, index=index_name):
        for hit in page["hits"]["hits"]:
            ids.append(hit["_id"])

    logging.info(f"Encontrados {len(ids)} excertos sem embedding em {index_name}")
    return ids
