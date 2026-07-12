"""
Step 12 - Tests for parse_query. Parsing is deterministic string
logic (not an algorithm with a subtle correctness question the way
phrase_run_length was), so hand-picked cases -- especially edge
cases -- carry the weight here rather than randomized fuzzing.
"""
from query_parser import parse_query


def check(raw_query, expected, label=""):
    got = parse_query(raw_query)
    ok = got == expected
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {label}: got={got}" + ("" if ok else f" expected={expected}"))
    return ok


def main():
    all_passed = True

    all_passed &= check(
        "oil price report",
        {"phrases": [], "excluded": [], "free_text": "oil price report"},
        label="plain free text, no syntax",
    )

    all_passed &= check(
        '"oil price" -crude report',
        {"phrases": ["oil price"], "excluded": ["crude"], "free_text": "report"},
        label="phrase + exclusion + free word, mixed",
    )

    all_passed &= check(
        '"oil price" "tax report"',
        {"phrases": ["oil price", "tax report"], "excluded": [], "free_text": ""},
        label="multiple quoted phrases, no free text left over",
    )

    all_passed &= check(
        "-oil -tax",
        {"phrases": [], "excluded": ["oil", "tax"], "free_text": ""},
        label="exclusion-only query",
    )

    all_passed &= check(
        '"oil"',
        {"phrases": ["oil"], "excluded": [], "free_text": ""},
        label="single-word quoted phrase",
    )

    all_passed &= check(
        "co-operative farming",
        {"phrases": [], "excluded": [], "free_text": "co-operative farming"},
        label="internal hyphen must NOT be parsed as exclusion",
    )

    all_passed &= check(
        "oil - price",
        {"phrases": [], "excluded": [], "free_text": "oil price"},
        label="lone dash token is dropped, not an exclusion of nothing",
    )

    all_passed &= check(
        'oil "price tax',
        {"phrases": [], "excluded": [], "free_text": 'oil "price tax'},
        label="unmatched trailing quote falls through leniently, no crash",
    )

    all_passed &= check(
        "",
        {"phrases": [], "excluded": [], "free_text": ""},
        label="empty query",
    )

    all_passed &= check(
        '  "oil price"   -crude   ',
        {"phrases": ["oil price"], "excluded": ["crude"], "free_text": ""},
        label="extra whitespace around syntax is tolerated",
    )

    print()
    print("ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED")
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)