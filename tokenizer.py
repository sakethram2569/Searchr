import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

STOP = set(stopwords.words('english'))
stemmer = PorterStemmer()


def tokenize(text: str) -> list[str]:
    words = re.findall(r'\b[a-z]+\b', text.lower())
    return [stemmer.stem(w) for w in words if w not in STOP]


def tokenize_with_surface(text: str) -> list[tuple[str, str]]:
    """Same filtering as tokenize(), but also keeps the raw (pre-stem) word
    for each kept token. Used only by the indexer to build a stem -> most-common
    surface-form mapping for display purposes (autocomplete), without touching
    the matching pipeline itself."""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    return [(w, stemmer.stem(w)) for w in words if w not in STOP]