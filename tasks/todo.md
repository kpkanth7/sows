# Tech-Intel — Action Plan

Goal: fix broken scheduled actions, harden data pipeline, widen free data sources, ship investor-grade features. Take project from "okay" to "brilliant".

Order = dependency order. Do Phase 0 first (stops the bleeding), then 1→4.

---

## Phase 0 — Stop the bleeding (today, ~2-3h)

Fixes for failing actions + silent bugs. Highest value, lowest effort.

- [x] **0.1** Split `ingest_stocks.yml` into 3 jobs gated by `github.event.schedule` (reliable; replaced broken `run_attempt` hack). Cron: tier1 `*/15`, tier2 `0 * * * *`, tier3 `0 */2 * * *`. Market-hours guard (Mon-Fri 9-16 ET) added to all three.
- [x] **0.2** `scripts/db.py` `check_quota` now returns `False` on exception (fail-safe).
- [x] **0.3** `scripts/db.py` `log_api_call` now upserts row if missing (works on fresh DB).
- [x] **0.4** `keepalive()` SQL function already present in `supabase/schema.sql` (lines ~357). NOTE: must re-run schema in Supabase SQL Editor if not yet applied.
- [x] **0.5** Added `health_checks` table to schema + `record_health()` helper in `db.py` + wired into all 11 job entrypoints (ok/error per run).
- [x] **0.6** `ingest_and_process.yml`: `continue-on-error: true` on steps 2-6b, 8, 9. News(1) + LLM(7) stay hard-fail.
- [x] **0.7** RLS already in schema (ENABLE + read-only policies all tables). Added public-read policy for new `health_checks`. NOTE: verify applied in live Supabase.

**Review checkpoint** → re-run `supabase/schema.sql` in Supabase SQL Editor (adds health_checks + confirms RLS/keepalive), push, confirm actions green before Phase 1.

---

## Phase 1 — Code cleanup & correctness (this week, ~3-4h)

- [ ] **1.1** Delete dead `frontend/src/services/api.js` (calls v1 FastAPI `127.0.0.1:8000`, unused)
- [ ] **1.2** Move v1 `backend/` to `legacy/` branch or delete from main (confuses architecture)
- [ ] **1.3** `frontend/src/lib/supabase.js` — throw on missing env var instead of placeholder fallback (silent broken client)
- [ ] **1.4** Extract duplicated `generate_llm_content` from `ingest_youtube.py` + `run_llm_batch.py` into `scripts/llm.py`
- [ ] **1.5** `ingest_stocks.py:107` — actually save the `company_news` it fetches (wasted API call right now)
- [ ] **1.6** Push Jaccard dedup (`ingest_news.py`) into Postgres: add `pg_trgm` GIN index on title + normalized `title_hash` column. Kills O(N²) scan.
- [ ] **1.7** Single source of truth for company synonyms (currently dup in `db.py` + `companies_config.py`)
- [ ] **1.8** Add 5 critical-path tests: dedup, entity extraction, quota check, buzz calc, LLM JSON parse

---

## Phase 2 — Data quality & batching (this week, ~4-6h)

Widen sources + use free quotas fully.

- [ ] **2.1** Add **HackerNews Algolia** ingestor, poll every 15-30min (unlimited, real-time, breaking software news lands here first)
- [ ] **2.2** Add **GDELT 2.0** ingestor (free global news firehose, pre-computed sentiment + entities)
- [ ] **2.3** Add **SEC EDGAR** 8-K/10-K ingestor (free, no key) → material events stream (mergers, lawsuits, exec changes)
- [ ] **2.4** Add **arXiv** ingestor for AI paper releases (leading indicator)
- [ ] **2.5** Expand Finnhub usage (same key, more endpoints): `/calendar/earnings`, `/stock/insider-transactions`, `/stock/recommendation`, `/stock/upgrade-downgrade`, `/news-sentiment`
- [ ] **2.6** Switch Reddit to RSS (`/r/X/.rss`) — unlimited, no 403s, drop 6s sleep
- [ ] **2.7** Switch YouTube to `videos.list?id=A,B,C` batched (1 unit/50 vids vs 100 units/search) — 100× quota saving
- [ ] **2.8** Switch GitHub to GraphQL — one call for trending+stars+releases vs N+1 REST
- [ ] **2.9** LLM provider rotation (Gemini 2.5-flash / Groq / Cerebras / OpenRouter) to multiply free daily ceiling 3-5×
- [ ] **2.10** Add backup stock sources: Twelve Data (800/day) + Tiingo (1000/hr) as fallback chain after Finnhub→yfinance
- [ ] **2.11** Tune ingestion schedule per source (see table below)

**Recommended schedule:**

| Source | Schedule | Note |
|---|---|---|
| Stocks T1 | 15min market hrs / 1hr off | pre/post-market moves |
| Stocks T2 | 30min market hrs | |
| Stocks T3 | 2hr market hrs | cheap |
| HackerNews | 15-30min | unlimited |
| TheNewsAPI | 3hr | use full 100/day |
| GDELT | 1hr | free |
| Bluesky | 2hr | cheap signal |
| Reddit | 6hr | RSS |
| YouTube | 6hr | unit-expensive |
| GitHub trending | 6hr | |
| SEC EDGAR | 1hr | material events |
| LLM batch | after each ingest via `workflow_run` | use full quota |

---

## Phase 3 — Investor product features (this month)

The differentiators. This is what makes it "brilliant" not "another aggregator".

- [ ] **3.1** **Material events stream** — SEC 8-Ks surfaced as feed cards ("$AAPL exec departure, 8-K filed 2h ago")
- [ ] **3.2** **Earnings countdown** widget per company + post-earnings sentiment delta
- [ ] **3.3** **Real Hype-vs-Reality chart** — NPM/PyPI downloads + GitHub stars trendline vs news-volume trendline. Replace weak `entities*10+|sentiment|*20` with z-score vs 30-day baseline.
- [ ] **3.4** **Insider trades panel** (Finnhub free)
- [ ] **3.5** **Controversy tracker** via CourtListener (free lawsuit API)
- [ ] **3.6** **Patent + arXiv tracker** = forward-looking R&D signal
- [ ] **3.7** **Daily investor digest** — LLM writes 1-paragraph "what an investor should know" from all signals
- [ ] **3.8** Rebuild **influencer trust decay** for real (current `update_influencer_trust.py` is a 69-line stub) or remove the claim
- [ ] **3.9** **Supabase Realtime** subscriptions → dashboard pushes new items, no polling

---

## Phase 4 — Polish & trust (ongoing)

- [ ] **4.1** Sentry (frontend+backend) + Logtail/BetterStack on Actions — free tiers, get alerts
- [ ] **4.2** `/status` page: every API's last-run + quota usage. Trust signal for visiting investors.
- [ ] **4.3** React error boundaries + skeleton loaders
- [ ] **4.4** Move inline styles → CSS modules / Tailwind
- [ ] **4.5** SEO meta + OG cards per company page
- [ ] **4.6** Mobile breakpoints
- [ ] **4.7** Rewrite README to match reality (claims "40+ influencers, 100+ companies"; config has ~60 companies, single-digit influencer lists)

---

## Verify locally first (before any push)

- [ ] Backend: `cd repo-root && python -m scripts.ingest_news 2>&1 | tail -30` (run from root, needs `.env`)
- [ ] Frontend: confirm `frontend/.env.local` has `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`; `npm run dev`, check console for 401s
- [ ] All scripts via `python -m scripts.X` (consistent imports, `PYTHONPATH` matches workflow)

---

## Review section

### Phase 0 — done 2026-05-28
**Changed:**
- `.github/workflows/ingest_stocks.yml` — rewritten: 3 jobs gated by `github.event.schedule`, market-hours guard, manual dispatch per tier.
- `.github/workflows/ingest_and_process.yml` — `continue-on-error` on 7 non-critical steps.
- `scripts/db.py` — `check_quota` fail-safe; `log_api_call` upsert; new `record_health()`.
- `scripts/*.py` (11 files) — entrypoints wrapped to record ok/error health.
- `supabase/schema.sql` — added `health_checks` table + RLS + public-read policy.

**Verified:** `py_compile` all 12 scripts OK; YAML parse OK.

**NOT verified (needs live env):** actual Supabase writes, action runs. Requires:
1. Re-run `supabase/schema.sql` in Supabase SQL Editor (creates `health_checks`).
2. Push branch, confirm Actions tab green.
3. Local smoke: `python -m scripts.ingest_news` from repo root with `.env`.

**Note:** Discovered RLS, `keepalive()`, and quota seed rows already existed in schema — 0.4/0.7 were file-complete; only live-apply pending.
