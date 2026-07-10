import pickle
import heapq
import os
import psycopg2
from dotenv import load_dotenv
from tokenizer import tokenize
from bm25 import precompute_idf, score_document

load_dotenv()

with open("index.pkl", "rb") as f:
    data = pickle.load(f)

inverted_index = data["inverted_index"]
doc_lengths = data["doc_lengths"]
term_doc_freq = data["term_doc_freq"]
total_docs = data["total_docs"]
avg_dl = data["avg_dl"]

idf = precompute_idf(term_doc_freq, total_docs)

query = "oil price rise"
query_terms = tokenize(query)
print(f"Query: {query!r} -> tokens: {query_terms}")

postings_by_term = {}
candidate_docs = set()
for term in query_terms:
    postings_by_term[term] = {p["doc_id"]: p for p in inverted_index.get(term, [])}
    candidate_docs.update(postings_by_term[term].keys())

print(f"Candidate documents containing at least one query term: {len(candidate_docs)}")

scores = {}
for doc_id in candidate_docs:
    scores[doc_id] = score_document(query_terms, doc_id, doc_lengths[doc_id], avg_dl, postings_by_term, idf)

top5 = heapq.nlargest(5, scores.items(), key=lambda x: x[1])

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"), dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()

print("\nTop 5 BM25 results:")
for doc_id, score in top5:
    cur.execute("SELECT title FROM documents WHERE id = %s", (doc_id,))
    title = cur.fetchone()[0]
    print(f"  score={score:.3f}  doc_id={doc_id}  title={title!r}")

cur.close()
conn.close()