import re
from collections import Counter
from typing import Dict, Iterable, List, Set

import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

from .interfaces import IndexInterface


def update_excerpts(theme: Dict, excerpts: Iterable[Dict], index: IndexInterface) -> Iterable[Dict]:
    for excerpt in excerpts:
        index.index_document(excerpt, document_id=excerpt['excerpt_id'], index=theme['index'])
        yield excerpt


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


def preprocess_excerpts_texts(excerpts: Iterable[Dict], pt_corpus: spacy.language.Language, stopwords: Set[str]) -> Iterable[str]:
    return [preprocess_excerpt_text(excerpt['excerpt'], pt_corpus, stopwords) for excerpt in excerpts]


def score_excerpts(theme: Dict, excerpts: List[Dict]) -> Iterable[Dict]:
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
        yield excerpt


def get_excerpts(theme: Dict, index: IndexInterface) -> List[Dict]:
    query_match_all = {"query": {"match_all": {}}}
    excerpts = index.search(query_match_all, index=theme['index'])
    return [excerpt['_source'] for excerpt in excerpts['hits']['hits']]
    

def tfidf_rerank_excerpts(theme: Dict, index: IndexInterface) -> Iterable[Dict]:
    excerpts = get_excerpts(theme, index)
    scored_excerpts = score_excerpts(theme, excerpts)
    updated_excerpts = update_excerpts(theme, scored_excerpts, index)
    yield from updated_excerpts

