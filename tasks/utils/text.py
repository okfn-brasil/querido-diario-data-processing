import re
from typing import List, Set

import spacy


def clean_extra_whitespaces(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def tokenize(text: str, stopwords: Set[str], lower: bool = True) -> List[str]:
    clean_text = clean_extra_whitespaces(text)
    clean_text = clean_text.lower() if lower else clean_text

    tokens = []
    for word in clean_text.split():
        word = re.sub(r"[^\w\s]", "", word)
        if word in stopwords:
            continue
        if len(word) <= 1:
            continue
        if word.isdigit():
            continue
        tokens.append(word)

    return tokens


def lemmatize(text: str, language: spacy.language.Language) -> List[str]:
    document = language(text)
    lemmas = [token.lemma_ for token in document]
    return [lemma for lemma in lemmas if len(lemma) > 1]
