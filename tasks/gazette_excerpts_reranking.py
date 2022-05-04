import os
import re
from collections import Counter
from typing import Dict, Iterable, List, Set

import nltk
import sentence_transformers
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

from .interfaces import IndexInterface


def preprocess_excerpt_text(excerpt_text: str, pt_corpus: spacy.language.Language, stopwords: Set[str]) -> str:
    # clean extra whitespaces
    text = re.sub(r"\s+", " ", excerpt_text)

    # iterate over words and convert them to lemmas
    tokens = []
    for word in text.split():
        word = re.sub(r"[^\w\s]", "", word).lower()
        if word in stopwords:
            continue
        if len(word) <= 1:
            continue
        if word.isdigit():
            continue
        tokens.append(word)

    # extract lemmas
    doc = pt_corpus(f"{' '.join(tokens)}")
    lemmas = [token.lemma_ for token in doc]
    lemmas = " ".join(lemma for lemma in lemmas if len(lemma) > 1)
    return lemmas


def preprocess_excerpts_texts(excerpts: List[Dict], pt_corpus: spacy.language.Language, stopwords: Set[str]) -> List[str]:
    return [preprocess_excerpt_text(excerpt['excerpt'], pt_corpus, stopwords) for excerpt in excerpts]


def tfidf_score_excerpts(theme: Dict, excerpts: List[Dict], index: IndexInterface) -> None:
    pt_corpus = spacy.load("pt_core_news_sm")
    stopwords = set(nltk.corpus.stopwords.words("portuguese")) | pt_corpus.Defaults.stop_words | set(theme["stopwords"])
    preprocessed_excerpts = preprocess_excerpts_texts(excerpts, pt_corpus, stopwords)

    vectorizer = TfidfVectorizer(use_idf=True, stop_words=stopwords)
    tfidf = vectorizer.fit_transform(preprocessed_excerpts)
    scores = tfidf[0].T.todense().tolist()
    scores = [score[0] for score in scores]
    indexed_terms = vectorizer.get_feature_names_out()
    scores_tfidf = dict(zip(indexed_terms, scores))

    for excerpt, preprocessed_excerpt in zip(excerpts, preprocessed_excerpts):
        tokens = preprocessed_excerpt.split()
        found_terms = Counter(tokens)
        excerpt_score = sum([term_count * scores_tfidf[term] for term, term_count in found_terms.items() if term in indexed_terms])
        excerpt['excerpt_tfidf_score'] = excerpt_score
        index.index_document(excerpt, document_id=excerpt['excerpt_id'], index=theme['index'])


def get_natural_language_queries(theme: Dict) -> List[str]:
    return [query['natural_language'] for query in theme['queries']]


def embedding_score_excerpts(theme: Dict, unscored_excerpts_ids: Set[str], excerpts: List[Dict], index: IndexInterface) -> None:
    model = sentence_transformers.SentenceTransformer("/root/models/bert-base-portuguese-cased")
    queries = get_natural_language_queries(theme)
    queries_vectors = model.encode(queries, convert_to_tensor=True)
    for excerpt in excerpts:
        if excerpt["excerpt_id"] not in unscored_excerpts_ids:
            continue
        excerpt_vector = model.encode(excerpt['excerpt'], convert_to_tensor=True)
        excerpt_max_score = sentence_transformers.util.semantic_search(excerpt_vector, queries_vectors, top_k=1)
        excerpt['excerpt_embedding_score'] = excerpt_max_score[0][0]['score']
        index.index_document(excerpt, document_id=excerpt['excerpt_id'], index=theme['index'])


def get_all_excerpts(theme: Dict, index: IndexInterface) -> List[Dict]:
    query_match_all = {"query": {"match_all": {}}, "size": 10000}
    excerpts = index.search(query_match_all, index=theme['index'])
    return [excerpt['_source'] for excerpt in excerpts['hits']['hits']]
    

def get_excerpts_ids(excerpts: Iterable[Dict]) -> Set[str]:
    return {excerpt['excerpt_id'] for excerpt in excerpts}


def rerank_excerpts(theme: Dict, unscored_excerpts: Iterable[Dict], index: IndexInterface) -> None:
    unscored_excerpts_ids = get_excerpts_ids(unscored_excerpts)
    excerpts = get_all_excerpts(theme, index)
    tfidf_score_excerpts(theme, excerpts, index)
    embedding_score_excerpts(theme, unscored_excerpts_ids, excerpts, index)

