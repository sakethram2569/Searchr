class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.doc_freq = 0
        self.display_form = None


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, term: str, df: int, display_form: str = None):
        node = self.root
        for ch in term:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True
        node.doc_freq = df
        node.display_form = display_form or term  # falls back to stem if none given

    def completions(self, prefix: str, limit: int = 10) -> list[str]:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]

        results = []

        def dfs(n):
            if len(results) >= limit * 3:
                return
            if n.is_end:
                results.append((n.doc_freq, n.display_form))
            for child in n.children.values():
                dfs(child)

        dfs(node)
        results.sort(reverse=True)
        return [word for _, word in results[:limit]]