"""
Tarefas para criar índices no motor de busca

Criação do índice principal (que contém os textos completos de cada edição de diário
oficial) e dos índices temáticos (excertos relacionados a algum tema que são
encontrados nos textos dos diários).
"""

from typing import Dict

from index import IndexInterface


def create_gazettes_index(index: IndexInterface) -> None:
    body = {
        "mappings": {
            "properties": {
                "created_at": {"type": "date"},
                "date": {"type": "date"},
                "edition_number": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "file_checksum": {"type": "keyword"},
                "file_path": {"type": "keyword"},
                "file_url": {"type": "keyword"},
                "id": {"type": "keyword"},
                "is_extra_edition": {"type": "boolean"},
                "power": {"type": "keyword"},
                "processed": {"type": "boolean"},
                "scraped_at": {"type": "date"},
                "source_text": {
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
                "state_code": {"type": "keyword"},
                "territory_id": {"type": "keyword"},
                "territory_name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "url": {"type": "keyword"},
            }
        },
        "settings": {
            "index": {
                "sort.field": ["territory_id", "date"],
                "sort.order": ["asc", "desc"],
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
            },
        },
    }
    index.create_index(body=body)


def create_themed_excerpts_index(theme: Dict, index: IndexInterface) -> None:
    body = {
        "mappings": {
            "properties": {
                "excerpt_embedding_score": {"type": "rank_feature"},
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
                "sort.order": ["asc", "desc"],
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
            },
        },
    }
    index.create_index(index_name=theme["index"], body=body)
