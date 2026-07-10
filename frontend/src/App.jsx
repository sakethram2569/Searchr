import { useState, useRef } from "react";
import api from "./api";
import "./App.css";

const PAGE_SIZE = 10;

function App() {
  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [results, setResults] = useState([]);
  const [meta, setMeta] = useState(null);
  const [page, setPage] = useState(1);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = useRef(null);

  const runSearch = async (searchQuery, pageNum) => {
    if (!searchQuery.trim()) return;
    const res = await api.get("/search", {
      params: { q: searchQuery, page: pageNum, size: PAGE_SIZE },
    });
    setResults(res.data.results);
    setMeta({
      total: res.data.total,
      time_ms: res.data.time_ms,
      corrected_query: res.data.corrected_query,
    });
    setPage(pageNum);
    setActiveQuery(searchQuery);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setShowSuggestions(false);
    runSearch(query, 1); // any new submitted search starts back at page 1
  };

  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);

    clearTimeout(debounceRef.current);
    if (!value.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      const res = await api.get("/autocomplete", { params: { prefix: value, limit: 8 } });
      setSuggestions(res.data.suggestions);
      setShowSuggestions(res.data.suggestions.length > 0);
    }, 300);
  };

  const handleSuggestionPick = (term) => {
    setQuery(term);
    setShowSuggestions(false);
    runSearch(term, 1);
  };

  const totalPages = meta ? Math.max(1, Math.ceil(meta.total / PAGE_SIZE)) : 1;

  return (
    <div className="app">
      <h1>Searchr</h1>
      <form onSubmit={handleSearch} className="search-form">
        <div className="input-wrap">
          <input
            value={query}
            onChange={handleChange}
            onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 100)}
            placeholder="Search..."
            autoComplete="off"
          />
          {showSuggestions && (
            <ul className="suggestions">
              {suggestions.map((s) => (
                <li key={s} onMouseDown={() => handleSuggestionPick(s)}>
                  {s}
                </li>
              ))}
            </ul>
          )}
        </div>
        <button type="submit">Search</button>
      </form>

      {meta && (
        <p className="meta">
          {meta.total} results in {meta.time_ms}ms
          {meta.corrected_query && ` (showing results for "${meta.corrected_query}")`}
        </p>
      )}

      <ul className="results">
        {results.map((r) => (
          <li key={r.id}>
            <h3>{r.title}</h3>
            <p dangerouslySetInnerHTML={{ __html: r.snippet }} />
          </li>
        ))}
      </ul>

      {meta && meta.total > 0 && (
        <div className="pagination">
          <button disabled={page <= 1} onClick={() => runSearch(activeQuery, page - 1)}>
            Prev
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button disabled={page >= totalPages} onClick={() => runSearch(activeQuery, page + 1)}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default App;