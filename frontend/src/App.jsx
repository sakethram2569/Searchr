import { useState, useRef, useEffect } from "react";
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
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docLoading, setDocLoading] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const debounceRef = useRef(null);
  const helpRef = useRef(null);

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
    runSearch(query, 1);
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

  const handleExample = (exampleQuery) => {
    setQuery(exampleQuery);
    setShowSuggestions(false);
    runSearch(exampleQuery, 1);
  };

  const openDocument = async (id) => {
    setDocLoading(true);
    setSelectedDoc({ id, title: "", content: "" });
    const res = await api.get(`/document/${id}`, { params: { q: activeQuery } });
    setSelectedDoc({ id, title: res.data.title, content: res.data.content });
    setDocLoading(false);
  };

  const closeDocument = () => setSelectedDoc(null);

  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === "Escape") {
        closeDocument();
        setShowHelp(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (!showHelp) return;
    const onClickOutside = (e) => {
      if (helpRef.current && !helpRef.current.contains(e.target)) {
        setShowHelp(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [showHelp]);

  const totalPages = meta ? Math.max(1, Math.ceil(meta.total / PAGE_SIZE)) : 1;

  return (
    <div className="app">
      <h1>Searchr</h1>
      <form onSubmit={handleSearch} className="search-form">
        <div className="input-wrap">
          <input
            value={query}
            onChange={handleChange}
            onFocus={() => {
              setShowHelp(false);
              suggestions.length > 0 && setShowSuggestions(true);
            }}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 100)}
            placeholder="Search Reuters news articles..."
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

        <div className="syntax-help" ref={helpRef}>
          <button
            type="button"
            className="syntax-help-btn"
            aria-label="Search syntax help"
            aria-expanded={showHelp}
            onClick={() => setShowHelp((v) => !v)}
          >
            ?
          </button>
          {showHelp && (
            <div className="syntax-popover" role="dialog" aria-label="Search syntax examples">
              <p>
                <code>"exact phrase"</code> only matches documents containing that
                exact wording, in order.
              </p>
              <p>
                <code>-word</code> excludes documents containing that word.
              </p>
              <p>
                Combine them: <code>"oil price" -government</code>
              </p>
            </div>
          )}
        </div>

        <button type="submit">Search</button>
      </form>

      {!meta ? (
        <div className="empty-tips">
          <p className="empty-tips-heading">Search tips</p>
          <p>
            <code>"quoted text"</code> finds that exact phrase, in order.
          </p>
          <p>
            <code>-word</code> excludes results containing that word.
          </p>
          <p className="empty-tips-examples-label">Try an example</p>
          <div className="example-chips">
            <button type="button" onClick={() => handleExample('"oil price"')}>
              "oil price"
            </button>
            <button type="button" onClick={() => handleExample("trade -japan")}>
              trade -japan
            </button>
            <button
              type="button"
              onClick={() => handleExample('"interest rate" -government')}
            >
              "interest rate" -government
            </button>
          </div>
        </div>
      ) : (
        <p className="meta">
          {meta.total} results in {meta.time_ms}ms
          {meta.corrected_query && ` (showing results for "${meta.corrected_query}")`}
        </p>
      )}

      <ul className="results">
        {results.map((r) => (
          <li key={r.id} onClick={() => openDocument(r.id)}>
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

      {selectedDoc && (
        <div className="modal-overlay" onClick={closeDocument}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={closeDocument} aria-label="Close">×</button>
            {docLoading ? (
              <p className="modal-loading">Loading...</p>
            ) : (
              <>
                <h2>{selectedDoc.title}</h2>
                <p className="modal-content" dangerouslySetInnerHTML={{ __html: selectedDoc.content }} />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;