import math

K1 = 1.5
B = 0.75


def precompute_idf(term_doc_freq: dict, total_docs: int) -> dict:
    return {
        term: math.log((total_docs - df + 0.5) / (df + 0.5) + 1)
        for term, df in term_doc_freq.items()
    }


def score_document(query_terms, doc_id, doc_length, avg_dl,
                    postings_by_term, idf) -> float:
    score = 0.0
    for term in query_terms:
        if term not in idf:
            continue
        posting = postings_by_term.get(term, {}).get(doc_id)
        if posting is None:
            continue
        tf = posting["tf"] * doc_length  # recover raw count from stored ratio
        numerator = tf * (K1 + 1)
        denominator = tf + K1 * (1 - B + B * doc_length / avg_dl)
        score += idf[term] * numerator / denominator
    return score