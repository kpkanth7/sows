const sources = ["all", "github", "hn", "stackexchange", "arxiv", "producthunt", "gdelt"];

export default function FilterBar({ filters, onChange }) {
  return (
    <section className="filter-bar" aria-label="Filters">
      <label>
        Source
        <select
          value={filters.source}
          onChange={(event) => onChange({ ...filters, source: event.target.value })}
        >
          {sources.map((source) => (
            <option key={source} value={source}>
              {source}
            </option>
          ))}
        </select>
      </label>
      <label>
        Window
        <select
          value={filters.window}
          onChange={(event) => onChange({ ...filters, window: event.target.value })}
        >
          <option value="24h">24 hours</option>
          <option value="7d">7 days</option>
          <option value="30d">30 days</option>
        </select>
      </label>
    </section>
  );
}
