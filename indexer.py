"""
Step 3 - Inverted index builder.
Reads all documents from Postgres, tokenizes them, and builds:
  - inverted_index: term -> list of {doc_id, positions, tf}
  - doc_lengths: doc_id -> token count
  - term_doc_freq: term -> number of docs containing it
  - total_docs, avg_dl
Serializes everything to index.pkl via pickle.
"""
import os
import pickle
import time
from collections import defaultdict

import psycopg2
from dotenv import load_dotenv

from tokenizer import tokenize

load_dotenv()

DB = dict(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)


def build_index():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    cur.execute("SELECT id, content FROM documents;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    print(f"Loaded {len(rows)} documents from Postgres. Tokenizing + indexing...")

    inverted_index = defaultdict(list)
    doc_lengths = {}
    term_doc_freq = defaultdict(int)

    start = time.time()
    for doc_id, content in rows:
        tokens = tokenize(content)
        doc_lengths[doc_id] = len(tokens)

        term_positions = defaultdict(list)
        for pos, term in enumerate(tokens):
            term_positions[term].append(pos)

        for term, positions in term_positions.items():
            tf = len(positions) / len(tokens) if tokens else 0
            inverted_index[term].append({"doc_id": doc_id, "positions": positions, "tf": tf})
            term_doc_freq[term] += 1

    total_docs = len(rows)
    avg_dl = sum(doc_lengths.values()) / total_docs

    elapsed = time.time() - start
    print(f"Indexed {total_docs} docs in {elapsed:.1f}s")
    print(f"Vocabulary size (unique terms): {len(inverted_index)}")
    print(f"Average document length: {avg_dl:.1f} tokens")

    data = {
        "inverted_index": dict(inverted_index),
        "doc_lengths": doc_lengths,
        "term_doc_freq": dict(term_doc_freq),
        "total_docs": total_docs,
        "avg_dl": avg_dl,
    }
    with open("index.pkl", "wb") as f:
        pickle.dump(data, f)

    size_mb = os.path.getsize("index.pkl") / (1024 * 1024)
    print(f"Saved index.pkl ({size_mb:.1f} MB)")

    return data


if __name__ == "__main__":
    data = build_index()
    # Adapted done-when check: "algorithm" doesn't occur in a financial-news
    # corpus, so we check a term that actually appears (e.g. "trade")
    postings = data["inverted_index"].get("trade", [])
    print(f"\nDone when check -> inverted_index['trade'] has {len(postings)} postings")
    if postings:
        print("Sample posting:", postings[0])