import { useState } from "react";
import api from "./api";
import "./App.css";

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [meta, setMeta] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    const res = await api.get("/search", { params: { q: query } });
    setResults(res.data.results);
    setMeta({
      total: res.data.total,
      time_ms: res.data.time_ms,
      corrected_query: res.data.corrected_query,
    });
  };

  return (
    <div className="app">
      <h1>Searchr</h1>
      <form onSubmit={handleSearch}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search..."
        />
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