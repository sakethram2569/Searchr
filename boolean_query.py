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