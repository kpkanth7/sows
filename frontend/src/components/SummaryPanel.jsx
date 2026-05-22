export default function SummaryPanel({ summaries }) {
  if (!summaries.length) {
    return (
      <section className="panel">
        <h2>Latest Intelligence Notes</h2>
        <p>No summaries yet. Run ingestors to collect live signals.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Latest Intelligence Notes</h2>
      <div className="summary-list">
        {summaries.slice(0, 5).map((summary) => (
          <article className="summary-item" key={summary.id}>
            <strong>{summary.summary_type}</strong>
            <p>{summary.content}</p>
            <time>{new Date(summary.created_at).toLocaleString()}</time>
          </article>
        ))}
      </div>
    </section>
  );
}
