"""
Step 1 - Corpus ingestion.
Loads the NLTK Reuters corpus (10,788 news documents) into PostgreSQL.
"""
import os
import psycopg2
from dotenv import load_dotenv
from nltk.corpus import reuters

load_dotenv()

DB = dict(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)


def extract_title_and_content(raw: str) -> tuple[str, str]:
    """Reuters docs start with an all-caps headline line; use it as title."""
    lines = raw.strip().split("\n")
    title = lines[0].strip().title()
    content = raw.strip()
    return title, content


def main():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS documents;")
    cur.execute("""
        CREATE TABLE documents (
            id SERIAL PRIMARY KEY,
            title TEXT,
            content TEXT,
            url TEXT,
            token_count INT
        );
    """)

    fileids = reuters.fileids()
    print(f"Found {len(fileids)} Reuters documents to ingest")

    rows = []
    for fid in fileids:
        raw = reuters.raw(fid)
        if not raw.strip():
            continue
        title, content = extract_title_and_content(raw)
        token_count = len(content.split())
        url = f"reuters://{fid}"
        rows.append((title, content, url, token_count))

    cur.executemany(
        "INSERT INTO documents (title, content, url, token_count) VALUES (%s, %s, %s, %s)",
        rows,
    )
    conn.commit()

    cur.execute("SELECT COUNT(*), AVG(token_count) FROM documents;")
    count, avg_len = cur.fetchone()
    print(f"Done when check -> rows: {count}, avg token_count: {avg_len:.1f}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()