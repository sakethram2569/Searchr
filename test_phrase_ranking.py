"""
Step 11 - Tests for phrase_run_length, following the same
ground-truth-comparison pattern as test_boolean.py: an independent,
brute-force reference implementation stands in for a trusted "answer key",
and the production function is checked against it -- including on
randomized inputs, not just hand-picked ones.
"""
import random
from boolean_query import phrase_run_length


def brute_force_run_length(query_terms, token_stream):
    """
    Reference implementation. Works directly on an ordered list of
    tokens (as if it were the actual document, stopwords already
    removed) rather than on postings/position sets -- a genuinely
    different code path from phrase_run_length, so agreement between
    the two is real evidence, not just two copies of the same bug.

    Must try starting the run at EVERY query-word index (i), not just
    index 0 -- a run doesn't have to begin with the first query word.
    E.g. query ["market", "report", "news"] against a doc containing
    "report news" but not "market" anywhere still has a genuine run of
    2 (the 2nd and 3rd query words, consecutive). An earlier version of
    this reference only tried anchoring at query_terms[0] and silently
    missed cases like this -- caught by the randomized fuzz test below.
    """
    n = len(query_terms)
    if n < 2:
        return n

    best = 1
    for i in range(n):
        for start in range(len(token_stream)):
            if token_stream[start] != query_terms[i]:
                continue
            run = 1
            pos = start
            for qi in range(i + 1, n):
                if pos + 1 < len(token_stream) and token_stream[pos + 1] == query_terms[qi]:
                    run += 1
                    pos += 1
                else:
                    break
            best = max(best, run)
    return best


def positions_from_stream(query_terms, token_stream):
    """Build the {term: {doc_id: {"positions": [...]}}} shape phrase_run_length expects."""
    postings_by_term = {}
    for term in set(query_terms):
        positions = [i for i, tok in enumerate(token_stream) if tok == term]
        postings_by_term[term] = {1: {"positions": positions}}
    return postings_by_term


def check(query_terms, token_stream, expected=None, label=""):
    postings_by_term = positions_from_stream(query_terms, token_stream)
    got = phrase_run_length(query_terms, 1, postings_by_term)
    truth = brute_force_run_length(query_terms, token_stream)
    ok = got == truth and (expected is None or got == expected)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}: production={got} brute_force={truth}"
          + (f" expected={expected}" if expected is not None else ""))
    return ok


def main():
    all_passed = True

    # 1. The exact example from the design notes.
    all_passed &= check(
        ["oil", "price", "tax"],
        ["oil", "price", "tax"],
        expected=3, label="full adjacency (oil price tax)",
    )
    all_passed &= check(
        ["oil", "price", "tax"],
        ["oil", "price", "report", "tax"],
        expected=2, label="partial adjacency (oil price ... tax)",
    )
    all_passed &= check(
        ["oil", "price", "tax"],
        ["tax", "report", "oil", "news", "price"],
        expected=1, label="no adjacency at all",
    )

    # 2. Single-word query -- main.py never calls this path (gated by
    #    len(query_terms) >= 2), but it should still behave sanely if
    #    called directly.
    all_passed &= check(["oil"], ["oil", "price"], expected=1, label="single-word query")

    # 3. Known limitation, made explicit: stopwords are stripped before
    #    positions are assigned, so "oil of price" collapses to the same
    #    adjacency as "oil price" in the position stream. This isn't a
    #    bug -- it's documented, expected behavior -- so we assert it
    #    rather than treating it as a surprise later.
    all_passed &= check(
        ["oil", "price"],
        ["oil", "price"],       # stopword-filtered stream: "of" already gone
        expected=2, label="stopword-collapsed adjacency (documented limitation)",
    )

    # 4. Query term repeated multiple times in the doc -- only some
    #    occurrences chain; the function must find the best one, not
    #    just whichever occurrence comes first.
    all_passed &= check(
        ["oil", "price"],
        ["price", "oil", "news", "oil", "price"],
        expected=2, label="repeated terms, best occurrence must be found",
    )

    # 5. Randomized fuzzing against the brute-force reference -- the
    #    real test, matching test_boolean.py's approach of trusting
    #    agreement across many random cases over a handful of
    #    hand-picked ones.
    random.seed(11)  # reproducible
    VOCAB = ["oil", "price", "tax", "report", "news", "market", "crude", "opec"]
    for trial in range(500):
        query_len = random.randint(2, 4)
        query_terms = random.sample(VOCAB, query_len)
        stream_len = random.randint(query_len, 15)
        token_stream = [random.choice(VOCAB) for _ in range(stream_len)]
        ok = check(query_terms, token_stream, label=f"random trial {trial}")
        all_passed &= ok
        if not ok:
            break  # stop at first mismatch rather than flooding output

    print()
    print("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)