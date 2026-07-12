import pickle
import os
import psycopg2
from dotenv import load_dotenv
from snippet import generate_snippet

load_dotenv()
with open("index.pkl", "rb") as f:
    data = pickle.load(f)
inverted_index = data["inverted_index"]

query_terms = ["oil", "price", "rise"]
doc_id = 7575  # top BM25 result from Step 4 for "oil price rise"

term_positions = {}
for term in query_terms:
    for posting in inverted_index.get(term, []):
        if posting["doc_id"] == doc_id:
            term_positions[term] = posting["positions"]
            break

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"), dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()
cur.execute("SELECT title, content FROM documents WHERE id = %s", (doc_id,))
title, content = cur.fetchone()
cur.close()
conn.close()

print(f"Document: {title!r}")
print(f"Query terms found at token positions: {term_positions}")
snippet = generate_snippet(content, term_positions, window_chars=200)
print(f"\nSnippet:\n{snippet}")