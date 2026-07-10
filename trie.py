class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.doc_freq = 0


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, term: str, df: int):
        node = self.root
        for ch in term:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True
        node.doc_freq = df

    def completions(self, prefix: str, limit: int = 10) -> list[str]:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]

        results = []

        def dfs(n, path):
            if len(results) >= limit * 3:
                return
            if n.is_end:
                results.append((n.doc_freq, path))
            for ch, child in n.children.items():
                dfs(child, path + ch)

        dfs(node, prefix)
        results.sort(reverse=True)
        return [word for _, word in results[:limit]]