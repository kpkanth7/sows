# Architecture

## Flow

```text
API ingestors -> Kafka topics -> Kafka consumer -> LangGraph workflow -> PostgreSQL -> FastAPI -> React
```

## Sources

Each source has its own ingestion service under `backend/app/ingestion`:

- GitHub repositories
- Hacker News stories
- Stack Exchange questions
- arXiv papers
- Product Hunt launches
- GDELT news/events

Ingestors convert source-specific payloads into `NormalizedEvent` objects before publishing to Kafka.

## Kafka Topics

- `github_events`
- `hn_events`
- `stackexchange_events`
- `arxiv_events`
- `producthunt_events`
- `gdelt_events`
- `normalized_events`
- `summaries`
- `forecasts`

## LangGraph Workflow

`backend/app/workflows/trend_graph.py` keeps the processing flow readable:

1. validate event
2. extract entities
3. persist item and entity links
4. update trend metrics
5. generate summary
6. create forecast

## Storage

PostgreSQL tables model sources, normalized items, entities, item/entity mappings, metrics, summaries, and forecasts.
