import re
from collections import Counter
from typing import Dict, List, Set

import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

from .interfaces import IndexInterface


def tfidf_rerank_excerpts(theme: Dict, index: IndexInterface) -> None:
    excerpts = get_all_excerpts(theme, index)
    tfidf_score_excerpts(theme, excerpts, index)


def get_all_excerpts(theme: Dict, index: IndexInterface) -> List[Dict]:
    index.refresh_index(theme["index"])
    query_match_all = {"query": {"match_all": {}}, "size": 10000}
    excerpts = []
    for result in index.paginated_search(query_match_all, index=theme["index"]):
        excerpts.extend([excerpt["_source"] for excerpt in result["hits"]["hits"]])
    return excerpts


def tfidf_score_excerpts(
    theme: Dict, excerpts: List[Dict], index: IndexInterface
) -> None:
    pt_corpus = spacy.load("pt_core_news_sm")
    stopwords = (
        set(nltk.corpus.stopwords.words("portuguese"))
        | pt_corpus.Defaults.stop_words
        | set(theme["stopwords"])
    )
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
        excerpt_score = sum(
            [
                term_count * scores_tfidf[term]
                for term, term_count in found_terms.items()
                if term in indexed_terms
            ]
        )
        excerpt["excerpt_tfidf_score"] = excerpt_score
        index.index_document(
            excerpt, document_id=excerpt["excerpt_id"], index=theme["index"]
        )


def preprocess_excerpts_texts(
    excerpts: List[Dict], pt_corpus: spacy.language.Language, stopwords: Set[str]
) -> List[str]:
    return [
        preprocess_excerpt_text(excerpt["excerpt"], pt_corpus, stopwords)
        for excerpt in excerpts
    ]


def preprocess_excerpt_text(
    excerpt_text: str, pt_corpus: spacy.language.Language, stopwords: Set[str]
) -> str:
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
