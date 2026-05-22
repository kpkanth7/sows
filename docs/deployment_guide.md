# Tech-Intel v2 — Free Deployment Guide

## Prerequisites

You will need accounts at these free services (no credit card required):
1. **GitHub** — your repo is already here
2. **Supabase** — https://supabase.com (free tier)
3. **Vercel** — https://vercel.com (Hobby plan, free)
4. **Google AI Studio** — https://aistudio.google.com (Gemini API key)
5. **Finnhub** — https://finnhub.io (free stock API)

---

## Step 1: Supabase Setup

1. Create a new Supabase project at https://app.supabase.com
2. Name it `tech-intel` (or anything you like)
3. Choose a region close to you
4. Wait for the project to initialize (~2 minutes)
5. Go to **SQL Editor** → paste the entire contents of `supabase/schema.sql` → click **Run**
6. Go to **Settings → API** and copy:
   - **Project URL** (looks like `https://xyz.supabase.co`)
   - **anon public** key
   - **service_role** key (keep this secret!)

---

## Step 2: Get All Free API Keys

See `docs/free_api_setup.md` for detailed signup instructions.

Quick summary:
| Key | Where to Get |
|---|---|
| `FINNHUB_API_KEY` | https://finnhub.io → Sign Up → API Keys |
| `GEMINI_API_KEY` | https://aistudio.google.com → Get API Key |
| `THENEWSAPI_KEY` | https://thenewsapi.com → Register |
| `GITHUB_TOKEN` | GitHub → Settings → Developer Settings → PAT (classic) → generate with `repo:read` scope |
| `YOUTUBE_API_KEY` | https://console.cloud.google.com → Enable YouTube Data API v3 → Create credentials |
| `REDDIT_CLIENT_ID/SECRET` | https://reddit.com/prefs/apps → Create app → script type |
| `STACKEXCHANGE_KEY` | https://stackapps.com/apps/oauth/register |
| `ALPHA_VANTAGE_KEY` | https://www.alphavantage.co/support/#api-key |

---

## Step 3: Add GitHub Actions Secrets

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

Add each of these:
```
SUPABASE_URL          = https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY = your-service-role-key
FINNHUB_API_KEY       = your-finnhub-key
GEMINI_API_KEY        = your-gemini-key
THENEWSAPI_KEY        = your-thenewsapi-key
GH_PAT                = ghp_your-github-pat
YOUTUBE_API_KEY       = your-youtube-key
REDDIT_CLIENT_ID      = your-reddit-client-id
REDDIT_CLIENT_SECRET  = your-reddit-secret
REDDIT_USER_AGENT     = TechIntel/1.0 by YourGitHubUsername
PRODUCTHUNT_CLIENT_ID = your-ph-client-id (optional)
PRODUCTHUNT_CLIENT_SECRET = your-ph-secret (optional)
ALPHA_VANTAGE_KEY     = your-alpha-vantage-key
```

---

## Step 4: Seed Initial Company Data

Run the seed script locally to populate the `companies` table with the initial list:

```bash
cd Tech-Intel_project
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt

# Set env vars locally
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Seed companies
python3 -c "
from scripts.companies_config import TIER1_COMPANIES, TIER2_COMPANIES, TIER3_COMPANIES
from scripts.db import get_client
import json

sb = get_client()
all_cos = TIER1_COMPANIES + TIER2_COMPANIES + TIER3_COMPANIES
for co in all_cos:
    sb.table('companies').upsert(co, on_conflict='name').execute()
    print(f'Seeded: {co[\"name\"]}')
print(f'Done! Seeded {len(all_cos)} companies.')
"
```

---

## Step 5: Run First Ingestion Locally (Verify)

```bash
# Run news ingestor first (no expensive API calls)
export THENEWSAPI_KEY="your-key"
python3 -m scripts.ingest_news

# Check Supabase: go to Table Editor -> news_items -> verify rows appeared

# Run stocks (Tier 1 only to be safe)
export FINNHUB_API_KEY="your-key"
python3 -m scripts.ingest_stocks --tier 1

# Run LLM batch to categorize
export GEMINI_API_KEY="your-key"
python3 -m scripts.run_llm_batch
```

---

## Step 6: Deploy Frontend to Vercel

### Option A: Vercel CLI (Recommended)
```bash
cd frontend
npm install
npm run build  # verify it builds locally first

# Deploy
npx vercel --prod
```

When Vercel asks:
- Link to existing project? **No** → create new
- What's your project's name? **tech-intel**
- In which directory is your code? **./frontend**

### Option B: Vercel Dashboard
1. Go to https://vercel.com/new
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Add environment variables:
   - `VITE_SUPABASE_URL` = your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY` = your Supabase anon key
5. Deploy!

---

## Step 7: Enable GitHub Actions

The workflows in `.github/workflows/` will run automatically once you push to your main branch.

To trigger manually for the first time:
1. Go to your repo on GitHub
2. Click **Actions** tab
3. Click **Ingest News** workflow
4. Click **Run workflow** → **Run workflow**
5. Watch it succeed ✅

---

## Step 8: Verify Production

After deployment:
1. Visit your Vercel URL
2. You should see the news feed populated
3. Company cards should show in the dashboard
4. Check the browser Network tab — all requests should go to `supabase.co`, not to any backend

---

## Keeping Supabase Alive

The `supabase_keepalive.yml` workflow runs every 12 hours automatically. If you ever see your data disappear, it means Supabase paused your project. Just go to the Supabase dashboard and click **Restore project**.

To prevent this forever, make sure the keepalive workflow is enabled in your GitHub Actions.

---

## Free Tier Limits Summary

| Service | Limit | Your Usage |
|---|---|---|
| Supabase DB | 500 MB | ~50MB expected |
| Supabase Bandwidth | 5 GB/month | ~1-2GB expected |
| Finnhub | 60 req/min | ~13 req/min peak |
| Gemini API | 1M tokens/day | ~50K tokens/day |
| YouTube API | 10,000 units/day | ~120 units/day |
| GitHub Actions | 2,000 min/month | ~800 min/month |
| Vercel | 100 GB bandwidth | ~1-5 GB/month |

All well within free limits. 🎉
