"""
Step 12 - Tests for filter_by_exact_phrases. This exists specifically
to close a gap that manual curl/browser testing couldn't: proving the
fallback branch actually EXECUTES, rather than just observing an
output that would look identical whether the fallback ran or the
phrase was never parsed at all in the first place.
"""
from boolean_query import filter_by_exact_phrases


def build_postings(term_positions_by_doc):
    """
    term_positions_by_doc: {doc_id: {term: [positions]}}
    Returns the {term: {doc_id: {"positions": [...]}}} shape
    filter_by_exact_phrases (via phrase_run_length) expects.
    """
    postings_by_term = {}
    for doc_id, term_positions in term_positions_by_doc.items():
        for term, positions in term_positions.items():
            postings_by_term.setdefault(term, {})[doc_id] = {"positions": positions}
    return postings_by_term


def check(candidate_ids, phrase_term_lists, term_positions_by_doc, expected, label=""):
    postings_by_term = build_postings(term_positions_by_doc)
    got = filter_by_exact_phrases(candidate_ids, phrase_term_lists, postings_by_term)
    ok = got == expected
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}: got={got} expected={expected}")
    return ok


def main():
    all_passed = True

    # 1. One doc has the exact phrase, one doesn't -- filter must keep
    #    only the matching doc, not fall back, since a match DOES exist.
    all_passed &= check(
        candidate_ids={1, 2},
        phrase_term_lists=[["oil", "price"]],
        term_positions_by_doc={
            1: {"oil": [0], "price": [1]},        # adjacent -- exact match
            2: {"oil": [0], "price": [5]},        # present but not adjacent
        },
        expected={1},
        label="exact match exists -- filters down to it",
    )

    # 2. THE important one: no candidate has the exact phrase anywhere.
    #    Must fall back to the full original candidate set, unchanged --
    #    this is the branch curl/browser testing couldn't cleanly prove.
    all_passed &= check(
        candidate_ids={1, 2, 3},
        phrase_term_lists=[["tax", "oil", "price"]],
        term_positions_by_doc={
            1: {"tax": [5], "oil": [0], "price": [1]},   # words present, not adjacent
            2: {"tax": [9], "oil": [2], "price": [3]},
            3: {"tax": [0], "oil": [5], "price": [6]},   # oil/price adjacent, tax isolated -- still not a full 3-word run
        },
        expected={1, 2, 3},
        label="zero exact matches -- falls back to full candidate set",
    )

    # 3. Multiple phrases: a doc must satisfy ALL of them (AND), not
    #    just one, to be kept.
    all_passed &= check(
        candidate_ids={1, 2},
        phrase_term_lists=[["oil", "price"], ["tax", "report"]],
        term_positions_by_doc={
            1: {"oil": [0], "price": [1], "tax": [5], "report": [6]},  # both phrases exact
            2: {"oil": [0], "price": [1], "tax": [5], "report": [9]},  # only 1st phrase exact
        },
        expected={1},
        label="multiple phrases are ANDed -- doc must satisfy every one",
    )

    # 4. Multiple phrases, NEITHER doc satisfies both -- must fall back
    #    to the full candidate set (not to whichever partially matched).
    all_passed &= check(
        candidate_ids={1, 2},
        phrase_term_lists=[["oil", "price"], ["tax", "report"]],
        term_positions_by_doc={
            1: {"oil": [0], "price": [1], "tax": [5], "report": [9]},  # only 1st phrase exact
            2: {"oil": [0], "price": [4], "tax": [5], "report": [6]},  # only 2nd phrase exact
        },
        expected={1, 2},
        label="no doc satisfies every phrase -- fallback, not partial credit",
    )

    # 5. No phrases at all -- pure passthrough, candidate set untouched.
    all_passed &= check(
        candidate_ids={1, 2, 3},
        phrase_term_lists=[],
        term_positions_by_doc={1: {}, 2: {}, 3: {}},
        expected={1, 2, 3},
        label="no quoted phrases -- passthrough, no filtering at all",
    )

    print()
    print("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)