"""
Step 9 - FastAPI search endpoints.
Loads the pickled index once at startup, keeps it (and a small Postgres
connection pool) in memory, and serves /search, /autocomplete, /document.
"""
import heapq
import os
import pickle
import time
from contextlib import asynccontextmanager

import psycopg2
from psycopg2 import pool as pg_pool
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tokenizer import tokenize
from bm25 import precompute_idf, score_document
from boolean_query import union, multi_and, phrase_run_length, subtract, filter_by_exact_phrases
from trie import Trie
from spellcheck import spellcheck
from snippet import generate_snippet
from query_parser import parse_query

load_dotenv()

DB = dict(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)

state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    with open("index.pkl", "rb") as f:
        data = pickle.load(f)

    state["inverted_index"] = data["inverted_index"]
    state["doc_lengths"] = data["doc_lengths"]
    state["total_docs"] = data["total_docs"]
    state["avg_dl"] = data["avg_dl"]
    state["idf"] = precompute_idf(data["term_doc_freq"], data["total_docs"])

    trie = Trie()
    term_display_form = data["term_display_form"]
    for term, df in data["term_doc_freq"].items():
        trie.insert(term, df, term_display_form.get(term, term))
    state["trie"] = trie

    state["db_pool"] = pg_pool.SimpleConnectionPool(1, 5, **DB)

    print(f"Loaded index: {data['total_docs']} docs, {len(data['inverted_index'])} vocab terms")
    yield
    state["db_pool"].closeall()
    state.clear()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


def resolve_query(tokens: list[str]) -> tuple[list[str], bool]:
    """
    Only spell-correct a term if it doesn't already exist in the vocabulary.
    (Running spellcheck unconditionally, even on correctly-typed common
    words, would risk "correcting" a valid rare word into a more common
    but different one -- bad behavior. Only fix terms genuinely absent
    from the vocabulary.)
    """
    inverted_index = state["inverted_index"]
    trie = state["trie"]
    corrected, changed = [], False
    for t in tokens:
        if t in inverted_index:
            corrected.append(t)
        else:
            fix = spellcheck(t, trie, max_edits=2)
            if fix:
                corrected.append(fix)
                changed = True
            else:
                corrected.append(t)
    return corrected, changed


@app.get("/search")
def search(q: str, page: int = 1, size: int = 10):
    start_time = time.time()
    inverted_index = state["inverted_index"]
    doc_lengths = state["doc_lengths"]
    avg_dl = state["avg_dl"]
    idf = state["idf"]

    parsed = parse_query(q)

    free_terms, free_corrected = resolve_query(tokenize(parsed["free_text"]))

    phrase_term_lists = []
    phrase_corrected = False
    for phrase in parsed["phrases"]:
        terms, changed = resolve_query(tokenize(phrase))
        if terms:  # a phrase that tokenizes to nothing (e.g. all stopwords) contributes nothing
            phrase_term_lists.append(terms)
        phrase_corrected = phrase_corrected or changed

    excluded_terms = []
    excluded_corrected = False
    for word in parsed["excluded"]:
        terms, changed = resolve_query(tokenize(word))
        excluded_terms.extend(terms)
        excluded_corrected = excluded_corrected or changed

    # Every word from every phrase counts as a required word too --
    # a doc can't satisfy an exact phrase without containing each word
    # individually first. Deduplicated, order preserved.
    seen = set()
    query_terms = []
    for term in [t for phrase in phrase_term_lists for t in phrase] + free_terms:
        if term not in seen:
            seen.add(term)
            query_terms.append(term)

    corrected = free_corrected or phrase_corrected or excluded_corrected

    postings_lists = [inverted_index[t] for t in query_terms if t in inverted_index]

    if not postings_lists:
        candidates = []
    else:
        and_result = multi_and(postings_lists) if len(postings_lists) > 1 else postings_lists[0]
        if and_result:
            candidates = and_result
        else:
            # AND found nothing -- fall back to OR rather than showing zero
            # results (standard real-world search UX)
            or_result = postings_lists[0]
            for p in postings_lists[1:]:
                or_result = union(or_result, p)
            candidates = or_result
    
    # Exclusion is a real, unconditional filter -- unlike the phrase
    # fallback below, if excluding a term empties the result set, that's
    # correct: the user explicitly asked to remove it.
    for term in excluded_terms:
        if term in inverted_index:
            candidates = subtract(candidates, inverted_index[term])

    postings_by_term = {
        t: {p["doc_id"]: p for p in inverted_index.get(t, [])} for t in query_terms
    }

    candidate_ids = {p["doc_id"] for p in candidates}
    bm25_scores = {
        doc_id: score_document(query_terms, doc_id, doc_lengths[doc_id], avg_dl, postings_by_term, idf)
        for doc_id in candidate_ids
    }

    if len(query_terms) >= 2:
        # Phrase-adjacency bonus: squared run length rewards longer
        # consecutive matches more than linearly. Pure addition on top
        # of BM25 -- never replaces it, never filters candidates.
        scores = {
            doc_id: bm25_scores[doc_id] + phrase_run_length(query_terms, doc_id, postings_by_term) ** 2
            for doc_id in candidate_ids
        }
    else:
        scores = bm25_scores

    if phrase_term_lists:
        phrase_matched_ids = filter_by_exact_phrases(candidate_ids, phrase_term_lists, postings_by_term)
        scores = {doc_id: scores[doc_id] for doc_id in phrase_matched_ids}

    ranked = heapq.nlargest(len(scores), scores.items(), key=lambda x: x[1])
    total = len(ranked)
    start_idx = (page - 1) * size
    page_slice = ranked[start_idx:start_idx + size]

    conn = state["db_pool"].getconn()
    try:
        cur = conn.cursor()
        results = []
        for doc_id, score in page_slice:
            cur.execute("SELECT title, content, url FROM documents WHERE id = %s", (doc_id,))
            title, content, url = cur.fetchone()
            term_positions = {
                t: postings_by_term[t][doc_id]["positions"]
                for t in query_terms if doc_id in postings_by_term[t]
            }
            snippet = generate_snippet(content, term_positions, window_chars=200)
            results.append({
                "id": doc_id, "title": title, "snippet": snippet,
                "score": round(score, 3), "url": url,
            })
        cur.close()
    finally:
        state["db_pool"].putconn(conn)

    elapsed_ms = (time.time() - start_time) * 1000
    return {
        "results": results,
        "total": total,
        "page": page,
        "size": size,
        "time_ms": round(elapsed_ms, 2),
        "corrected_query": " ".join(query_terms) if corrected else None,
    }


@app.get("/autocomplete")
def autocomplete(prefix: str, limit: int = 8):
    suggestions = state["trie"].completions(prefix.lower(), limit=limit)
    return {"suggestions": suggestions}


@app.get("/document/{doc_id}")
def get_document(doc_id: int):
    conn = state["db_pool"].getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT title, content FROM documents WHERE id = %s", (doc_id,))
        row = cur.fetchone()
        cur.close()
    finally:
        state["db_pool"].putconn(conn)
    if not row:
        return {"error": "not found"}
    return {"title": row[0], "content": row[1]}