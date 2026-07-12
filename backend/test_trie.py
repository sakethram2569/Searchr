import pickle
import time
from trie import Trie

with open("index.pkl", "rb") as f:
    data = pickle.load(f)

term_doc_freq = data["term_doc_freq"]

start = time.time()
trie = Trie()
for term, df in term_doc_freq.items():
    trie.insert(term, df)
build_time = time.time() - start
print(f"Built Trie from {len(term_doc_freq)} vocabulary terms in {build_time:.2f}s")

for prefix in ["trad", "econ", "compan"]:
    start = time.time()
    results = trie.completions(prefix, limit=5)
    elapsed_ms = (time.time() - start) * 1000
    print(f"\ncompletions({prefix!r}) -> {results}  ({elapsed_ms:.2f}ms)")