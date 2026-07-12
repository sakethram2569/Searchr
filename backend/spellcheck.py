from collections import deque


def spellcheck(query_term: str, trie, max_edits: int = 2) -> str | None:
    """
    BFS over states (trie_node, remaining_query_suffix, path_so_far, edits_used).
    At each step, try:
      - match next char (0 edits, advance both)
      - delete a query char (1 edit, advance query only, trie stays)
      - insert a trie char (1 edit, advance trie only, query stays)
      - substitute (1 edit, advance both, trie char != query char)
    Among all trie words reached within max_edits, return the one
    with the highest doc_freq (most common word wins ties/ambiguity).
    """
    start = (trie.root, query_term, "", 0)
    visited = set()
    queue = deque([start])
    best = None  # (doc_freq, word)

    while queue:
        node, remaining, path, edits = queue.popleft()

        state_key = (id(node), remaining, edits)
        if state_key in visited:
            continue
        visited.add(state_key)

        if edits > max_edits:
            continue

        if node.is_end and remaining == "":
            if best is None or node.doc_freq > best[0]:
                best = (node.doc_freq, path)

        if edits == max_edits and remaining == "":
            continue

        if remaining:
            ch = remaining[0]
            if ch in node.children:
                queue.append((node.children[ch], remaining[1:], path + ch, edits))

        if edits < max_edits:
            if remaining:
                queue.append((node, remaining[1:], path, edits + 1))
            for ch, child in node.children.items():
                queue.append((child, remaining, path + ch, edits + 1))
            if remaining:
                for ch, child in node.children.items():
                    if ch != remaining[0]:
                        queue.append((child, remaining[1:], path + ch, edits + 1))

    return best[1] if best else None