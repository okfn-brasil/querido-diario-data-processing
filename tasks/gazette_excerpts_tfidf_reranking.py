from collections import Counter
from typing import Dict, List, Set

import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

from .interfaces import IndexInterface
from .utils import get_all_documents, lemmatize, tokenize


def tfidf_rerank_excerpts(theme: Dict, index: IndexInterface) -> None:
    excerpts = [
        excerpt["_source"] for excerpt in get_all_documents(index, theme["index"])
    ]
    tfidf_score_excerpts(theme, excerpts, index)


def tfidf_score_excerpts(
    theme: Dict, excerpts: List[Dict], index: IndexInterface
) -> None:
    if len(excerpts) == 0:
        return

    pt_language = spacy.load("pt_core_news_sm")
    stopwords = (
        set(nltk.corpus.stopwords.words("portuguese"))
        | pt_language.Defaults.stop_words
        | set(theme["stopwords"])
    )
    preprocessed_excerpts = preprocess_excerpts_texts(excerpts, pt_language, stopwords)

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

        # Elasticsearch only accepts strictly positive values for rank_features
        excerpt["excerpt_tfidf_score"] = (
            0.000001 if excerpt_score == 0.0 else excerpt_score
        )

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
    excerpt_text: str, pt_language: spacy.language.Language, stopwords: Set[str]
) -> str:
    tokens = tokenize(excerpt_text, stopwords)
    lemmas = lemmatize(" ".join(tokens), pt_language)
    return " ".join(lemmas)
