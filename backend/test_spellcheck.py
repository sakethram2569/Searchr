import pickle
import time
from trie import Trie
from spellcheck import spellcheck

with open("index.pkl", "rb") as f:
    data = pickle.load(f)
term_doc_freq = data["term_doc_freq"]

trie = Trie()
for term, df in term_doc_freq.items():
    trie.insert(term, df)

test_cases = ["tradee", "pryce", "intrest", "companey", "econmy"]
for misspelled in test_cases:
    start = time.time()
    result = spellcheck(misspelled, trie, max_edits=2)
    elapsed_ms = (time.time() - start) * 1000
    print(f"spellcheck({misspelled!r}) -> {result!r}  ({elapsed_ms:.2f}ms)")