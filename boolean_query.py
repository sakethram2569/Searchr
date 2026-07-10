"""
Step 5 - Posting list intersection for boolean AND/OR/NOT queries.
Postings must be sorted by doc_id for two-pointer to work.
"""


def intersect(a, b):
    """AND: two-pointer intersection. a, b: lists of posting dicts sorted by doc_id."""
    result, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i]["doc_id"] == b[j]["doc_id"]:
            result.append(a[i])
            i += 1
            j += 1
        elif a[i]["doc_id"] < b[j]["doc_id"]:
            i += 1
        else:
            j += 1
    return result


def union(a, b):
    """OR: two-pointer merge, keeping all doc_ids from either list."""
    result, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i]["doc_id"] == b[j]["doc_id"]:
            result.append(a[i])
            i += 1
            j += 1
        elif a[i]["doc_id"] < b[j]["doc_id"]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result


def subtract(a, b):
    """NOT: keep postings in a whose doc_id is not present in b."""
    exclude_ids = {p["doc_id"] for p in b}
    return [p for p in a if p["doc_id"] not in exclude_ids]


def multi_and(posting_lists):
    """AND across 3+ terms: intersect shortest lists first for less total work."""
    posting_lists = sorted(posting_lists, key=len)
    result = posting_lists[0]
    for lst in posting_lists[1:]:
        result = intersect(result, lst)
    return result

def phrase_run_length(query_terms, doc_id, postings_by_term):
    """
    Longest run of query words that appear at consecutive positions,
    in original query order, in the given document.

    query_terms: list of query words, in original query order.
    doc_id: the document being scored.
    postings_by_term: {term: {doc_id: posting_dict}}, posting_dict has "positions".

    Returns an int. A single-word query has nothing to be adjacent to,
    so callers should skip this for len(query_terms) < 2.
    """
    n = len(query_terms)
    if n < 2:
        return n

    positions = []
    for term in query_terms:
        posting = postings_by_term.get(term, {}).get(doc_id)
        positions.append(set(posting["positions"]) if posting else set())

    best = 1
    for i in range(n):
        for p in positions[i]:
            run, k = 1, 1
            while i + k < n and (p + k) in positions[i + k]:
                run += 1
                k += 1
            best = max(best, run)
    return best