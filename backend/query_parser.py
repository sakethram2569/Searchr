"""
Step 12 - Query syntax parsing for quoted exact-phrase search and
-word exclusion. Pure string parsing only -- no tokenization here, so
this has no dependency on tokenizer.py and can be tested standalone.
Tokenization of the extracted pieces happens in main.py, the same way
it already happens today for a plain free-text query.
"""
import re

_QUOTED = re.compile(r'"([^"]+)"')


def parse_query(raw_query: str) -> dict:
    """
    Splits a raw query string into three raw (untokenized) groups:
      - phrases: list of raw phrase substrings, one per "quoted" section
      - excluded: list of raw words that were prefixed with -
      - free_text: remaining raw text (still needs tokenize())

    Multiple quoted phrases are all returned -- caller decides how to
    combine them (this project ANDs them, consistent with how free
    words already work).

    Malformed input (e.g. an unmatched trailing quote) is handled
    leniently: the dangling quote character just falls through into
    free_text rather than raising an error. A search box should never
    hard-fail because of a stray punctuation mark.
    """
    phrases = [m.group(1).strip() for m in _QUOTED.finditer(raw_query) if m.group(1).strip()]
    remainder = _QUOTED.sub(" ", raw_query)

    excluded = []
    free_words = []
    for word in remainder.split():
        if word.startswith("-") and len(word) > 1:
            excluded.append(word[1:])
        elif word == "-":
            continue  # a lone dash isn't an exclusion of anything
        else:
            free_words.append(word)

    return {
        "phrases": phrases,
        "excluded": excluded,
        "free_text": " ".join(free_words),
    }