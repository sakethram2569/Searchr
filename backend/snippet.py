import re
from nltk.corpus import stopwords

STOP = set(stopwords.words("english"))


def build_char_offsets(content: str) -> list[tuple[int, int]]:
    """
    Re-walks the content with the SAME word-splitting + stopword-filter
    logic as tokenizer.tokenize(), so offsets[i] lines up exactly with
    token position i as stored in the inverted index.
    """
    offsets = []
    for m in re.finditer(r"\b[a-z]+\b", content.lower()):
        w = m.group()
        if w in STOP:
            continue
        offsets.append((m.start(), m.end()))
    return offsets


def generate_snippet(content: str, term_positions: dict[str, list[int]],
                      window_chars: int = 150) -> str:
    """
    term_positions: {stemmed_query_term: [token_position, ...]} for THIS document
                    (the "positions" list from that term's posting for this doc_id).
    """
    char_offsets = build_char_offsets(content)

    occurrences = []
    for term, positions in term_positions.items():
        for pos in positions:
            if pos < len(char_offsets):
                start, end = char_offsets[pos]
                occurrences.append((start, end, term))
    occurrences.sort(key=lambda x: x[0])

    if not occurrences:
        return content[:window_chars] + ("..." if len(content) > window_chars else "")

    # sliding window: find the window of width <= window_chars covering
    # the most DISTINCT query terms
    best_window = None
    best_distinct = -1
    left = 0
    for right in range(len(occurrences)):
        while occurrences[right][1] - occurrences[left][0] > window_chars and left < right:
            left += 1
        distinct_terms = {occurrences[i][2] for i in range(left, right + 1)}
        if len(distinct_terms) > best_distinct:
            best_distinct = len(distinct_terms)
            best_window = (left, right)

    left, right = best_window
    win_start = occurrences[left][0]
    win_end = occurrences[right][1]

    pad = max(0, window_chars - (win_end - win_start))
    win_start = max(0, win_start - pad // 2)
    win_end = min(len(content), win_end + pad // 2)

    snippet_chars = list(content[win_start:win_end])
    in_window = [o for o in occurrences if o[0] >= win_start and o[1] <= win_end]
    for start, end, term in sorted(in_window, key=lambda x: -x[0]):
        rel_start, rel_end = start - win_start, end - win_start
        snippet_chars[rel_start:rel_end] = list(
            "<mark>" + "".join(snippet_chars[rel_start:rel_end]) + "</mark>"
        )

    prefix = "..." if win_start > 0 else ""
    suffix = "..." if win_end < len(content) else ""
    return prefix + "".join(snippet_chars) + suffix


def highlight_full_content(content: str, term_positions: dict[str, list[int]]) -> str:
    """
    Same position-based <mark> insertion as generate_snippet, but applied to
    the ENTIRE document with no window truncation -- used for the full
    document-detail view rather than a search-result preview snippet.
    """
    char_offsets = build_char_offsets(content)

    occurrences = []
    for term, positions in term_positions.items():
        for pos in positions:
            if pos < len(char_offsets):
                start, end = char_offsets[pos]
                occurrences.append((start, end))

    if not occurrences:
        return content

    content_chars = list(content)
    for start, end in sorted(occurrences, key=lambda x: -x[0]):
        content_chars[start:end] = list(
            "<mark>" + "".join(content_chars[start:end]) + "</mark>"
        )
    return "".join(content_chars)