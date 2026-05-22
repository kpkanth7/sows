# Real-Time Tech & Company Intelligence Copilot with Trend Forecasting
## Codex Project Instructions

## 1. Project Overview

Build a full-stack, real-time intelligence platform that ingests live data from multiple public technology-related APIs, streams that data through Kafka, processes it through structured workflows using LangGraph, stores it in PostgreSQL, summarizes and explains trends using an LLM, forecasts short-term trend movement using TimesFM, and presents everything in a dashboard.

This is not a static dataset project. It must use live API ingestion and real-time or near-real-time processing.

The project should combine signals from multiple ecosystems such as:
- engineering activity
- developer discussion
- developer questions
- product launches
- research publications
- optional live news/event data

The platform should identify trending technologies, tools, frameworks, repositories, products, and companies, explain why they are trending, and forecast whether the trend is likely to continue.

---

## 2. Main Aim of the Project

Create a real-time multi-source intelligence system that:
- ingests live information from multiple APIs
- streams and processes the data through Kafka
- unifies and normalizes data from different sources
- detects technology and company trends
- summarizes insights using an LLM
- forecasts short-term trend movement using TimesFM
- stores processed data in PostgreSQL
- exposes backend APIs via FastAPI
- displays the intelligence in a React dashboard

---

## 3. Core Goals

### Goal 1: Multi-Source Live Data Ingestion
Use real APIs, not static CSV files or datasets.

### Goal 2: Real-Time Streaming
Use Kafka as the event streaming layer to publish and consume normalized events from API ingestors.

### Goal 3: Workflow Orchestration
Use LangGraph to organize the processing flow from ingestion to enrichment to summarization to forecasting.

### Goal 4: LLM-Based Summarization
Use an LLM to explain trends, summarize what is happening, and generate short intelligence notes.

### Goal 5: Time-Series Forecasting
Use TimesFM to forecast short-term trend movement using daily or hourly aggregated metrics.

### Goal 6: Structured Storage
Use PostgreSQL to store normalized items, extracted entities, trend metrics, summaries, and forecast outputs.

### Goal 7: Dashboard Visualization
Use React to build a dashboard that displays:
- trending technologies
- trending companies
- source-specific activity
- summaries
- comparison charts
- forecast charts

---

## 4. Data Sources / APIs

The system should use the following live APIs.

### Primary APIs
1. GitHub API
   - repositories
   - stars
   - issues
   - pull requests
   - repo/company activity

2. Hacker News API
   - top stories
   - new stories
   - best stories
   - scores
   - comments
   - titles and URLs

3. Stack Exchange API
   - technology tags
   - recent questions
   - votes
   - answers
   - accepted answers

4. arXiv API
   - latest papers
   - paper metadata
   - categories
   - publication dates
   - titles and abstracts

### Secondary APIs
5. Product Hunt API
   - product launches
   - categories
   - votes
   - launch dates
   - startup/product activity

6. GDELT API or live open event/news source
   - news/event context
   - company mentions
   - global events related to technology or companies

### Important requirement
Do not assume all APIs will behave the same way.
Create one ingestion service per source and normalize them into a common schema before downstream processing.

---

## 5. Required Tech Stack

### Backend
- Python
- FastAPI

### Workflow / Orchestration
- LangGraph

### Streaming / Real-Time
- Apache Kafka

### Database
- PostgreSQL

### Forecasting
- TimesFM

### LLM Layer
Use one swappable LLM provider abstraction.
Preferred options:
- Qwen
- Mistral Small
- another efficient LLM if needed, but keep the code provider-agnostic

### Frontend
- React

### Scheduling / Background Processing
Use one of:
- APScheduler
- background worker pattern
- Kafka consumers for streaming processing

### Python Libraries
Potential packages:
- fastapi
- uvicorn
- requests or httpx
- sqlalchemy
- psycopg2-binary or asyncpg
- pydantic
- python-dotenv
- langgraph
- kafka-python or confluent-kafka
- pandas
- numpy
- timesfm
- transformers if required by selected models
- apscheduler

---

## 6. Project Architecture

The project should roughly follow this flow:

API Ingestors -> Kafka Topics -> Consumers / LangGraph Workflow -> PostgreSQL -> FastAPI Backend -> React Dashboard

### Detailed flow
1. Each API ingestor fetches live data
2. Raw data is normalized into a common event structure
3. Normalized events are pushed into Kafka topics
4. Kafka consumers read the events
5. LangGraph workflows process events through steps like:
   - cleaning
   - entity extraction
   - topic classification
   - trend scoring
   - summarization
   - forecasting
6. Processed results are written into PostgreSQL
7. FastAPI exposes endpoints for the frontend
8. React dashboard displays trends, summaries, and forecast charts

---

## 7. Functional Requirements

The system must be able to:

### Ingestion
- fetch live data from all configured APIs
- handle API limits gracefully
- log failures
- retry safely where appropriate
- normalize source-specific data into a common structure

### Trend Detection
- identify trending technologies
- identify trending companies/products
- detect spikes in mentions/activity
- support comparisons across sources

### Summarization
- generate short summaries such as:
  - what is trending
  - why it may be trending
  - which sources are contributing
- summaries should be readable and concise

### Forecasting
- aggregate time-series metrics by date/hour
- forecast short-term movement using TimesFM
- surface forecast results in charts and summary text

### Dashboard
- show top technologies
- show top companies/products
- show source-wise contributions
- show historical trend charts
- show forecast charts
- show recent LLM summaries

### Search / Filtering
- filter by source
- filter by entity type
- filter by time window
- compare multiple technologies or companies

---

## 8. Non-Functional Requirements

- modular code
- readable structure
- beginner-friendly implementation
- environment variables for secrets and config
- source-specific ingestion services
- no overengineering
- clear separation between ingestion, processing, storage, and presentation
- robust logging
- easy local development setup

---

## 9. Recommended Folder Structure

```text
project-root/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routes_trends.py
│   │   │   ├── routes_sources.py
│   │   │   ├── routes_forecasts.py
│   │   │   └── routes_summaries.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── logging_config.py
│   │   ├── models/
│   │   │   ├── source.py
│   │   │   ├── item.py
│   │   │   ├── entity.py
│   │   │   ├── metric.py
│   │   │   ├── summary.py
│   │   │   └── forecast.py
│   │   ├── schemas/
│   │   │   ├── item.py
│   │   │   ├── entity.py
│   │   │   ├── metric.py
│   │   │   ├── summary.py
│   │   │   └── forecast.py
│   │   ├── ingestion/
│   │   │   ├── github_ingestor.py
│   │   │   ├── hn_ingestor.py
│   │   │   ├── stackexchange_ingestor.py
│   │   │   ├── arxiv_ingestor.py
│   │   │   ├── producthunt_ingestor.py
│   │   │   └── gdelt_ingestor.py
│   │   ├── streaming/
│   │   │   ├── kafka_producer.py
│   │   │   ├── kafka_consumer.py
│   │   │   └── topics.py
│   │   ├── workflows/
│   │   │   ├── trend_graph.py
│   │   │   ├── summarization_graph.py
│   │   │   └── forecasting_graph.py
│   │   ├── services/
│   │   │   ├── normalization_service.py
│   │   │   ├── entity_extraction_service.py
│   │   │   ├── trend_scoring_service.py
│   │   │   ├── summarization_service.py
│   │   │   ├── forecasting_service.py
│   │   │   └── llm_service.py
│   │   └── utils/
│   │       ├── time_utils.py
│   │       └── text_utils.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   ├── charts/
│   │   └── App.jsx
│   └── package.json
│
├── docs/
│   ├── architecture.md
│   ├── api_setup.md
│   └── local_setup.md
│
├── scripts/
│   ├── run_ingestors.py
│   ├── run_consumers.py
│   └── seed_entities.py
│
└── README.md


10. PostgreSQL Data Design

At minimum, create tables/models for:

sources

Represents each source platform such as GitHub, Hacker News, Stack Exchange, arXiv, Product Hunt, GDELT

items

Normalized source items such as:

repository activity
discussion posts
questions
papers
product launches
news/events

Suggested fields:

id
source_id
external_id
title
body_text
url
author_name
score
created_at
raw_payload
item_type
entities

Represents technologies, companies, products, frameworks, or topics

Suggested fields:

id
name
entity_type
canonical_name
item_entities

Mapping table between items and detected entities

metrics

Stores aggregated trend metrics by day/hour and by source

Suggested fields:

id
entity_id
source_id
metric_date
mention_count
score_sum
item_count
trend_score
summaries

Stores LLM-generated summaries

Suggested fields:

id
summary_type
content
created_at
entity_id optional
source_id optional
forecasts

Stores TimesFM outputs

Suggested fields:

id
entity_id
source_id optional
forecast_date
predicted_value
horizon
created_at
11. Kafka Design

Kafka must be used for real-time streaming.

Suggested topics:

github_events
hn_events
stackexchange_events
arxiv_events
producthunt_events
gdelt_events
normalized_events
summaries
forecasts
Producer behavior

Each ingestor publishes normalized source events into a source-specific topic.

Consumer behavior

Consumers should:

read source events
normalize further if needed
run workflows
write results to PostgreSQL
publish summaries/forecast events if useful
12. LangGraph Requirements

LangGraph must be used as the workflow orchestration layer.

Suggested graph nodes:

fetch_or_receive_event
validate_event
normalize_event
extract_entities
classify_topic
update_metrics
summarize_trend
forecast_trend
persist_results

The workflow should remain simple and readable.
Do not build overly autonomous agents.
Use LangGraph as a structured workflow engine.

13. TimesFM Requirements

TimesFM must be included for forecasting.

Use it on aggregated metrics such as:

daily mentions of a technology
daily mentions of a company
daily repo star velocity
daily product launch activity
daily question volume by tag

Forecasts should focus on short-term trend prediction such as:

next 3 days
next 7 days
optional next 14 days

Store outputs in PostgreSQL and expose them via backend endpoints.

14. LLM Requirements

The LLM must be used for summarization and explanation.

Use the LLM to generate:

daily trend summary
source-specific summary
entity-specific explanation
comparison summary between two technologies or companies

The LLM layer must be abstracted so providers can be swapped later.

Implement a simple llm_service.py interface with methods like:

summarize_trends(...)
explain_entity_trend(...)
compare_entities(...)
15. API Setup Requirements

The app should be designed so each source can be configured through .env.

GitHub

Need:

personal access token
Hacker News

Need:

no key
Stack Exchange

Need:

optional API key for better quota
arXiv

Need:

no key for normal use
Product Hunt

Need:

client id
client secret
access token if required by chosen auth flow
GDELT

Need:

no key for open endpoints if available
16. Local Setup / Downloads Required

The developer needs to install or create the following:

Required local software
Python 3.11 or newer
Node.js and npm
PostgreSQL
Apache Kafka
Git
VS Code or similar editor
Python packages to install

Create a requirements.txt that includes all backend dependencies.

Frontend packages

React app with charting library and API client

Optional external accounts
GitHub account for token
Stack Apps / Stack Exchange developer key
Product Hunt account for API credentials
Hugging Face account if needed for model access
LLM provider account if using hosted model

17. .env Configuration

Create .env.example and support the following variables:

APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000

DATABASE_URL=postgresql://postgres:password@localhost:5432/tech_intel
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=tech_intel
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_GITHUB=github_events
KAFKA_TOPIC_HN=hn_events
KAFKA_TOPIC_STACK=stackexchange_events
KAFKA_TOPIC_ARXIV=arxiv_events
KAFKA_TOPIC_PRODUCTHUNT=producthunt_events
KAFKA_TOPIC_GDELT=gdelt_events
KAFKA_TOPIC_NORMALIZED=normalized_events
KAFKA_TOPIC_SUMMARIES=summaries
KAFKA_TOPIC_FORECASTS=forecasts

GITHUB_TOKEN=
STACKEXCHANGE_KEY=
PRODUCTHUNT_CLIENT_ID=
PRODUCTHUNT_CLIENT_SECRET=
PRODUCTHUNT_ACCESS_TOKEN=

HF_TOKEN=

LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=

LANGCHAIN_TRACING_V2=false
LANGSMITH_API_KEY=
18. Backend Endpoints

At minimum, implement these endpoints:

Health / Status
GET /health
GET /sources/status
Trends
GET /trends/technologies
GET /trends/companies
GET /trends/compare
Summaries
GET /summaries/latest
GET /summaries/entity/{entity_name}
Forecasts
GET /forecasts/entity/{entity_name}
GET /forecasts/top
Source Data
GET /sources/github/latest
GET /sources/hn/latest
GET /sources/stackexchange/latest
GET /sources/arxiv/latest
19. Frontend Requirements

Build a React dashboard with:

overview cards
top technologies chart
top companies chart
source contribution chart
forecast chart
summary panel
filters for source and time range
compare view for two entities

Keep the UI clean and readable.
Functionality matters more than visual perfection.

20. Implementation Expectations for Codex

When implementing:

work step by step
keep the system runnable
do not skip setup files
generate clean README instructions
create .env.example
create clear comments
keep code modular
avoid unnecessary abstraction
do not introduce unrelated tools
do not replace PostgreSQL with SQLite
do not remove Kafka
do not remove LangGraph
do not remove TimesFM
keep the selected stack intact
21. Immediate Priority Order

Build in this order:

project structure
.env.example
PostgreSQL connection
Kafka setup
FastAPI app skeleton
source ingestors
Kafka producer/consumer
normalized schema and models
LangGraph workflows
LLM summarization
TimesFM forecasting
dashboard endpoints
React dashboard
README and setup docs
22. Final Objective

The final result should be a working portfolio-quality project that demonstrates:

live API ingestion
real-time streaming
workflow orchestration
LLM-based intelligence
time-series forecasting
full-stack engineering
practical, recruiter-friendly system design

The project must feel like a real intelligence platform, not a toy demo.