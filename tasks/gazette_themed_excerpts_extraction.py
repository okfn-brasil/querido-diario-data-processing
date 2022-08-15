import hashlib
from typing import Dict, Iterable, List
import logging

from .interfaces import IndexInterface
from .utils import clean_extra_whitespaces, get_documents_from_query_with_highlights

logging.basicConfig(level=logging.DEBUG)

def extract_themed_excerpts_from_gazettes(
    theme: Dict, gazette_ids: List[str], index: IndexInterface
) -> List[str]:
    create_index(theme, index)
    ids = []
    import csv
    with open("dataset.csv", "w") as f:
        flag = True
        for theme_query in theme["queries"]:
            logging.debug(f"theme_query: {theme_query}")
            for excerpt in get_excerpts_from_gazettes_with_themed_query(
                theme_query, gazette_ids, index
            ):
                logging.info(excerpt)
                if flag:
                    flag = False
                    csvfile = csv.DictWriter(f, fieldnames=excerpt.keys())
                    csvfile.writeheader()

                csvfile.writerow(excerpt)
                # index.index_document(
                #     excerpt,
                #     document_id=excerpt["excerpt_id"],
                #     index=theme["index"],
                #     refresh=True,
                # )
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
                    "analyzer": "portuguese",
                    "index_options": "offsets",
                    "term_vector": "with_positions_offsets",
                    "fields": {
                        "portuguese_without_stopwords_removal": {
                            "type": "text",
                            "analyzer": "portuguese_without_stopwords_removal",
                            "index_options": "offsets",
                            "term_vector": "with_positions_offsets",
                        },
                        "exact": {
                            "type": "text",
                            "analyzer": "portuguese_exact",
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
            "analysis": {
                "filter": {
                    "portuguese_stemmer": {
                        "type": "stemmer",
                        "language": "light_portuguese",
                    }
                },
                "analyzer": {
                    "portuguese_without_stopwords_removal": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "portuguese_stemmer"],
                    },
                    "portuguese_exact": {
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
    es_query = get_es_query_from_themed_query(query, gazette_ids)
    # es_query = get_es_query_from_themed_interval_query_test(query, gazette_ids)
    logging.debug("→→→ Query executada:")
    logging.debug(es_query)
    logging.debug("←←← Fim da query executada")
    documents = get_documents_from_query_with_highlights(es_query, index)
    for document in documents:
        gazette = document["_source"]
        excerpts = document["highlight"]["source_text"]
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


""" Query de testes para extração de excertos """
def get_excerpts_from_gazettes_test() -> Iterable[Dict]:
    es_query = get_es_query_test()
    # es_query = get_es_query_from_themed_interval_query_test(query, gazette_ids)
    logging.debug("→→→ Query executada:")
    logging.debug(es_query)
    logging.debug("←←← Fim da query executada")
    documents = get_documents_from_query_with_highlights(es_query, index)
    ids = []
    for document in documents:
        gazette = document["_source"]
        excerpts = document["highlight"]["source_text"]
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
            ids.append(generate_excerpt_id(excerpt, gazette))
    return ids


""" Query de teste básica para verificar conexão com o índice remoto """
def get_es_query_test() -> Dict:
    es_query = {
        "query": {
            "simple_query_string": {
                "fields": [ "source_text" ],
                "query": "poluição"
            }
        }
    }
    return es_query

def get_es_query_from_themed_query(
    query: Dict,
    gazette_ids: List[str],
) -> Dict:
    es_query = {
        "query": {
            "bool": {
                "must": [],
                "filter": [
                    {"range": {"date": {"gte": "2020-01-01", "lte": "2022-04-30"}}},
                    {
                        "terms": {
                            "territory_id": [
                                "1302603",
                                "1400100",
                                "1501402",
                                "1702109",
                                "1721000",
                                "2103000",
                                "2211001",
                                "2408003",
                                "2408102",
                                "2507507",
                                "2607901",
                                "2611101",
                                "2611606",
                                "2704302",
                                "2910800",
                                "2927408",
                                "3106200",
                                "3304557",
                                "3525904",
                                "3552403",
                                "4106902",
                                "4205407",
                                "4314902",
                                "5002704",
                                "5103403",
                                "5208707",
                                "5300108",
                            ]
                        }
                    },
                    {"ids": {"values": gazette_ids}},
                ],
            }
        },
        "size": 100,
        "highlight": {
            "fields": {
                "source_text": {
                    "type": "unified",
                    "boundary_scanner_locale": "pt-BR",
                    "fragment_size": 2000,
                    "number_of_fragments": 10000,
                    "pre_tags": ["<__"],
                    "post_tags": ["__>"],
                }
            }
        }
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
                for word in term.split():
                    word_block = {"span_term": {"source_text": word}}
                    phrase_block["span_near"]["clauses"].append(word_block)
                synonym_block["span_or"]["clauses"].append(phrase_block)
            proximity_block["span_near"]["clauses"].append(synonym_block)
        macro_synonym_block["span_or"]["clauses"].append(proximity_block)
    es_query["query"]["bool"]["must"].append(macro_synonym_block)
    return es_query

def get_es_query_from_themed_interval_query(
    query: Dict,
    gazette_ids: List[str],
) -> Dict:
    es_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "intervals": {
                            "source_text": {
                                "all_of": {
                                    "intervals": [],
                                    "max_gaps" : 30
                                }
                            }
                        }
                    }
                ],
                "filter": [
                    {
                        "range": {
                            "date": {
                                "gte": "2020-01-01",
                                "lte": "2022-04-30"
                            }
                        }
                    },
                    {
                        "terms": {
                            "territory_id": [
                                "1302603",
                                "1400100",
                                "1501402",
                                "1702109",
                                "1721000",
                                "2103000",
                                "2211001",
                                "2408003",
                                "2408102",
                                "2507507",
                                "2607901",
                                "2611101",
                                "2611606",
                                "2704302",
                                "2910800",
                                "2927408",
                                "3106200",
                                "3304557",
                                "3525904",
                                "3552403",
                                "4106902",
                                "4205407",
                                "4314902",
                                "5002704",
                                "5103403",
                                "5208707",
                                "5300108",
                            ]
                        }
                    },
                    {
                        "ids": {
                            "values": gazette_ids
                        }
                    }
                ]
            }
        },
        "size": 100,
        "highlight": {
            "fields": {
                "source_text": {
                    "type": "unified",
                    "boundary_scanner_locale": "pt-BR",
                    "fragment_size": 2000,
                    "number_of_fragments": 10000,
                    "pre_tags": ["<__"],
                    "post_tags": ["__>"],
                }
            }
        }
    }

    # Lista de blocos de termos sinônimos, pode conter um ou mais blocos de sinônimos
    for macro_set in query["term_sets"]:
        # para cada bloco de termos
        for term_set in macro_set:
            # cria um bloco de sinônimos utilizando span_or, de modo que qualquer um que ocorra retorne positivo para o bloco
            synonym_block = {
                "any_of" : {
                    "intervals" : []
                }
            }
            # para cada termo do bloco de sinônimos
            for term in term_set:
                # cria um bloco para o termo / frase
                phrase_block = {}
                # frase (múltimplos termos)
                if len(term.split(" ")) >  0:
                    phrase_block = { "match" : { "query" : term, "ordered": True, "max_gaps": 0  } }
                # palavra única
                else:
                    phrase_block = { "match" : { "query" : term } }
                # Adiciona a frase ao bloco de sinônimos
                synonym_block["any_of"]["intervals"].append(phrase_block)
            # Adiciona o bloco de sinônimos ao bloco span_or
            must_clause = es_query["query"]["bool"]["must"][0]
            logging.debug(must_clause)
            must_clause["intervals"]["source_text"]["all_of"]["intervals"].append(synonym_block)
    return es_query

def preprocess_excerpt(excerpt: str) -> str:
    return clean_extra_whitespaces(excerpt)
