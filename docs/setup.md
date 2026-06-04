# Tech-Intel Setup

Single setup doc. Current system only. No legacy Kafka/FastAPI path.

## What you need

- GitHub repo
- Supabase project
- Vercel project when ready to deploy
- Python 3.11+
- Node.js + npm

## Actual architecture

- frontend: `frontend/` (`React` + `Vite`)
- database + realtime: `Supabase`
- background jobs: `.github/workflows/`
- ingestion + scoring + digest scripts: `scripts/`
- schema: `supabase/schema.sql`

## Step 1: Supabase

1. Create project in Supabase.
2. Run `supabase/schema.sql` in SQL Editor.
3. Copy:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

## Step 2: Local frontend env

Create `frontend/.env.local`:

```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## Step 3: Local script env

Copy `.env.example` to `.env`, then fill keys you actually use.

Core:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `FINNHUB_API_KEY`
- `THENEWSAPI_KEY`
- `YOUTUBE_API_KEY`
- `GH_PAT` or `GITHUB_TOKEN`
- `REDDIT_USER_AGENT`
- `GEMINI_API_KEY` and/or `GROQ_API_KEY`

Optional but useful:

- `CEREBRAS_API_KEY`
- `OPENROUTER_API_KEY`
- `PRODUCTHUNT_CLIENT_ID`
- `PRODUCTHUNT_CLIENT_SECRET`
- `ALPHA_VANTAGE_KEY`
- `SEC_USER_AGENT`
- `COURTLISTENER_API_TOKEN`

## Step 4: Install locally

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Python

From repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

## Step 5: Verify locally

Run a few direct checks:

```bash
PYTHONPATH=scripts pytest tests/ -q
python3 -m scripts.ingest_news
python3 -m scripts.ingest_stocks --tier 1
python3 -m scripts.generate_daily_digest
```

Frontend:

```bash
cd frontend
npm run build
```

## Step 6: GitHub Actions secrets

Add these in GitHub repo settings if you want scheduled jobs to work:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `FINNHUB_API_KEY`
- `THENEWSAPI_KEY`
- `YOUTUBE_API_KEY`
- `GH_PAT`
- `REDDIT_USER_AGENT`
- `GEMINI_API_KEY`
- `GROQ_API_KEY`

Often also needed:

- `CEREBRAS_API_KEY`
- `OPENROUTER_API_KEY`
- `PRODUCTHUNT_CLIENT_ID`
- `PRODUCTHUNT_CLIENT_SECRET`
- `ALPHA_VANTAGE_KEY`
- `SEC_USER_AGENT`
- `COURTLISTENER_API_TOKEN`
- `LLM_PROVIDER`
- `LLM_MODEL`

## Step 7: Deploy to Vercel

When ready:

1. Import repo into Vercel.
2. Set root directory to `frontend/`.
3. Add frontend env vars:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
4. Deploy.

`vercel.json` already exists in repo and should stay tracked.

## Active scheduled workflows

- `ingest_stocks.yml`
- `ingest_hackernews.yml`
- `ingest_firehoses.yml`
- `ingest_and_process.yml`
- `ingest_finnhub_extras.yml`
- `daily_digest.yml`
- `supabase_keepalive.yml`

Manual/deprecated helpers also exist, but main system runs from schedules above.

## Notes

- visible app feed uses recent window, but DB keeps longer retention for core tables
- `news_items` and `stock_snapshots` prune at `90 days`
- project still in active development; deploy polish and final live checks come later
