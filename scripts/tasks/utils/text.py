import re


def clean_extra_whitespaces(text: str) -> str:
    return re.sub(r"\s+", " ", text)
