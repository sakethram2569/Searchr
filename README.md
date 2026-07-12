# Searchr

A full-text search engine built from scratch — no Elasticsearch, no Lucene, no Solr. Just an inverted index, BM25 ranking, boolean query logic, a trie-based autocomplete, and a BFS spell corrector, all implemented directly so the internals of a real search engine are visible and understood rather than hidden behind a library.

The corpus is NLTK's **Reuters corpus** (10,788 financial news documents), loaded into PostgreSQL and indexed locally into a serialized `index.pkl`.

## Why

Most people who use a search box never see what's underneath it: how a query turns into a ranked list of documents in milliseconds. Searchr rebuilds that path end to end — tokenization, an inverted index with term positions, BM25 scoring, two-pointer boolean set operations, phrase and exclusion parsing, autocomplete, and spell correction — to understand each piece well enough to reason about its tradeoffs, not just call an API.

## Features

- **Inverted index with term positions** — built once via `indexer.py`, serialized to `index.pkl`, loaded into memory at API startup.
- **BM25 ranking** (`k1=1.5`, `b=0.75`) with TF-saturation and document-length normalization.
- **Boolean AND / OR / NOT**, implemented with three distinct techniques rather than one:
  - `intersect()` (AND) — two-pointer intersection over doc-id-sorted posting lists.
  - `union()` (OR) — two-pointer merge.
  - `subtract()` (NOT) — hash-set-based exclusion.
  - `multi_and()` handles 3+ terms by intersecting the shortest posting lists first.
  - All three are `O(m+n)` overall, but via different mechanisms — worth keeping straight rather than calling everything "two-pointer."
- **AND-first with automatic OR-fallback** — if an AND of all query terms returns nothing, the engine falls back to OR rather than showing zero results.
- **Query syntax** — `"quoted phrases"` for exact matches and `-excluded` words (see [Query syntax](#query-syntax) below).
- **Phrase-adjacency ranking boost** — any multi-word query gets a bonus (squared longest consecutive run of query words, in order) added on top of the BM25 score. This is purely a ranking signal; it never filters candidates.
- **Trie-based autocomplete**, ranked by document frequency, showing real surface words rather than internal stems.
- **Spell correction** via BFS over the trie (match / delete / insert / substitute) within edit distance ≤ 2 — only triggered when a query term isn't already in the vocabulary.
- **Highlighted snippets** in search results (sliding window that maximizes distinct query terms covered) and **full-document highlighting** in the document-detail modal — both share the same backend position-based `<mark>` logic, so they're guaranteed consistent.
- **FastAPI backend + React frontend** with debounced autocomplete, pagination, light/dark theming (via `prefers-color-scheme`, no manual toggle), and a click-through document-detail modal.
- A small search-syntax help popover and an empty-state "tips" card with clickable example queries, shown before any search is run.

## Folder structure

```
Searchr/
├── backend/
│   ├── download_data.py     # Downloads the NLTK Reuters corpus, stopwords, and punkt tokenizer data
│   ├── ingest.py             # Loads the 10,788 Reuters docs into a Postgres `documents` table
│   │                         # (id, title, content, url, token_count)
│   ├── tokenizer.py          # Lowercases, strips non-letters, removes stopwords, applies Porter
│   │                         # stemming. tokenize() is the core pipeline; tokenize_with_surface()
│   │                         # also keeps pre-stem words, used by the indexer for display purposes
│   ├── indexer.py            # Reads all docs from Postgres, builds the inverted index
│   │                         # (term -> list of {doc_id, positions, tf}), doc_lengths,
│   │                         # term_doc_freq, avg_dl, and a term_display_form map
│   │                         # (stem -> most common surface form). Serializes it all to index.pkl
│   ├── bm25.py                # BM25 scoring: precompute_idf() and score_document(), k1=1.5, b=0.75
│   ├── boolean_query.py      # intersect() (AND), union() (OR), subtract() (NOT), multi_and()
│   │                         # (3+ term AND), phrase_run_length() (longest consecutive run of
│   │                         # query words in a doc — used both as a ranking bonus and as an
│   │                         # exact-phrase filter), filter_by_exact_phrases() (hard filter for
│   │                         # quoted phrases, with a safe fallback to unfiltered results if
│   │                         # nothing matches exactly)
│   ├── query_parser.py       # Parses raw query strings into quoted phrases, -excluded words,
│   │                         # and free text — pure string parsing, no tokenization, no
│   │                         # dependency on tokenizer.py
│   ├── trie.py                # Prefix trie for autocomplete, ranked by document frequency,
│   │                         # storing a display_form per node so suggestions show real words
│   ├── spellcheck.py         # BFS over the trie within edit distance ≤ 2, returns the most
│   │                         # frequent valid correction; only triggered when a query term
│   │                         # isn't already in the vocabulary
│   ├── snippet.py             # generate_snippet() builds a highlighted, sliding-window snippet
│   │                         # around query terms for search results; highlight_full_content()
│   │                         # applies the same position-based <mark> highlighting to a full
│   │                         # document (used by the document-detail modal)
│   ├── main.py                # FastAPI app; loads index.pkl and a Postgres connection pool at
│   │                         # startup. Endpoints: GET /search, GET /autocomplete, GET /document/{id}
│   ├── requirements.txt      # Pinned dependencies
│   ├── index.pkl              # Serialized inverted index (gitignored — build it locally, see Setup)
│   └── test_*.py              # One test file per module: test_tokenizer.py, test_bm25.py,
│                             # test_boolean.py, test_trie.py, test_spellcheck.py, test_snippet.py,
│                             # test_query_parser.py, test_phrase_ranking.py, test_phrase_filter.py.
│                             # Run as plain scripts (python test_x.py); most compare production
│                             # logic against independent brute-force reference implementations
│                             # or hand-picked edge cases, some using randomized fuzz testing
├── frontend/
│   └── src/
│       ├── App.jsx            # Main React component: search box with debounced autocomplete,
│       │                     # a search-syntax help popover, an empty-state "tips" card with
│       │                     # clickable example queries, paginated results, and a click-through
│       │                     # document-detail modal (closes on Escape, click-outside, or ×)
│       ├── App.css            # All styling; CSS custom properties drive light/dark theming via
│       │                     # prefers-color-scheme (auto-detects OS setting, no manual toggle)
│       ├── api.js             # Axios instance pointed at http://127.0.0.1:8000
│       └── main.jsx           # Vite/React entry point
├── .gitignore                 # Ignores venv/, __pycache__/, .env, *.pkl
└── README.md
```

## Query syntax

The search box supports three things at once: free text, exact phrases, and exclusions.

| Syntax | Meaning | Example |
|---|---|---|
| `word1 word2` | Free text — AND-matched first, falls back to OR if AND returns nothing | `oil price` |
| `"word1 word2"` | Exact phrase — words must appear consecutively, in that order | `"trade deficit"` |
| `-word` | Exclude documents containing this word | `-japan` |

These combine freely. For example:

```
"interest rate" -japan hike
```

finds documents that contain the exact phrase *"interest rate"*, do **not** mention *japan*, and are boosted (but not required) to also mention *hike*.

Every word inside a quoted phrase is also folded into the required-word set — a document can't satisfy an exact phrase without containing each of its words individually first. Exclusion is a real, unconditional filter: if excluding a word empties the result set, that's correct, since the user explicitly asked to remove it. A quoted phrase, by contrast, never causes zero results by itself — if nothing matches the phrase exactly, the engine falls back to the unfiltered candidate set rather than showing nothing.

## Known limitation

Positions used for phrase and adjacency detection are indices into the **stopword-filtered token stream**, not raw text. So `"oil of price"` and `"oil price"` register as equally adjacent after filtering, since `of` is removed before positions are assigned. Production systems like Elasticsearch handle this more precisely via position-increment gaps, which preserve a record of removed stopwords so genuine adjacency in the original text can still be distinguished from adjacency introduced by filtering. This is a known tradeoff of the current implementation, not a bug.

## API reference

### `GET /search`

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | — | Query string, supports `"phrases"` and `-exclusion` |
| `page` | int | `1` | Page number |
| `size` | int | `10` | Results per page |

Returns ranked results (BM25 + phrase-adjacency bonus where applicable), each with a highlighted snippet, plus `total`, `page`, `size`, `time_ms`, and `corrected_query` (non-null only if spellcheck changed a term).

### `GET /autocomplete`

| Param | Type | Default | Description |
|---|---|---|---|
| `prefix` | string | — | Prefix to complete |
| `limit` | int | `8` | Max suggestions |

Returns `{"suggestions": [...]}`, ranked by document frequency, shown as real surface words rather than stems.

### `GET /document/{doc_id}`

| Param | Type | Default | Description |
|---|---|---|---|
| `q` | string | `""` | Optional — if present, the response content is returned with `<mark>` highlighting for the query's terms (excluded words are deliberately left unhighlighted) |

Returns `{"title": ..., "content": ...}`.

## Setup

### Prerequisites

- Python 3.11+
- Node.js (for the frontend)
- PostgreSQL, running locally

### 1. Clone the repo

```powershell
git clone https://github.com/sakethram2569/Searchr.git
cd Searchr
```

### 2. Set up the Python virtual environment

```powershell
python -m venv venv
venv\Scripts\activate
cd backend
pip install -r requirements.txt
```

### 3. Create the Postgres database and user

Open `psql` (or your preferred Postgres client) and run:

```sql
CREATE DATABASE searchr;
CREATE USER searchr_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE searchr TO searchr_user;
```

### 4. Create `backend\.env`

In `backend\`, create a file named `.env` (already gitignored) with:

```
DB_HOST=localhost
DB_NAME=searchr
DB_USER=searchr_user
DB_PASSWORD=your_password_here
```

### 5. Download the corpus and build the index

Run these **in order** — each step depends on the previous one:

```powershell
python download_data.py
python ingest.py
python indexer.py
```

- `download_data.py` pulls the Reuters corpus, stopwords, and tokenizer data from NLTK.
- `ingest.py` loads the 10,788 documents into the `documents` table in Postgres.
- `indexer.py` reads them back out, tokenizes and stems everything, and writes `index.pkl`.

### 6. Run the backend

```powershell
uvicorn main:app --reload --port 8000
```

### 7. Run the frontend

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://127.0.0.1:8000` (see `frontend/src/api.js`).

## Performance

As independently tested by the developer: **10,788 documents**, **21,521 vocabulary terms**, `index.pkl` ≈ **14.9 MB**, query latency **6–25ms** across TestClient, live HTTP, and browser testing. Re-verify if the index has been rebuilt since, as these numbers depend on the exact corpus and vocabulary at index-build time.
