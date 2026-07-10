import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

STOP = set(stopwords.words('english'))
stemmer = PorterStemmer()


def tokenize(text: str) -> list[str]:
    words = re.findall(r'\b[a-z]+\b', text.lower())
    return [stemmer.stem(w) for w in words if w not in STOP]