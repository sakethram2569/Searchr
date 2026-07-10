import { useState, useRef } from "react";
import api from "./api";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [meta, setMeta] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = useRef(null);

  const runSearch = async (searchQuery) => {
    if (!searchQuery.trim()) return;
    const res = await api.get("/search", { params: { q: searchQuery } });
    setResults(res.data.results);
    setMeta({
      total: res.data.total,
      time_ms: res.data.time_ms,
      corrected_query: res.data.corrected_query,
    });
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setShowSuggestions(false);
    runSearch(query);
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
    runSearch(term);
  };

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
    </div>
  );
}

export default App;