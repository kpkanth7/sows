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

**Review checkpoint** → DONE. Schema re-run OK, pushed, `Ingest & Process` ran green (all 14 steps).

**ROOT CAUSE of "actions keep failing" found:** GitHub repo secrets were never set (empty `SUPABASE_URL` etc in CI) → every scheduled job crashed at `get_client()`. Local worked via `.env`. Fixed by bulk-loading secrets from `.env` (with `</dev/null` so `gh` doesn't eat loop stdin). Added Groq primary + Gemini fallback for LLM.

**Schema made idempotent:** all `CREATE INDEX` → `IF NOT EXISTS`; all policies prefixed `DROP POLICY IF EXISTS`. Re-runnable now.

**Carry to later:** bump `actions/checkout@v4`+`setup-python@v5` (Node20 deprecation, June 2026) → Phase 4. Dead `LLM_API_KEY` in `.env` (code ignores) → reconcile Phase 1.

---

## Phase 1 — Code cleanup & correctness (this week, ~3-4h)

- [x] **1.1** Delete dead `frontend/src/services/api.js` (calls v1 FastAPI `127.0.0.1:8000`, unused) — confirmed zero importers, `git rm`.
- [x] **1.2** Deleted v1 `backend/` from main + dead Kafka runners `run_consumers.py`/`run_ingestors.py` (only importers, no workflow used them). Recoverable via git history.
- [x] **1.3** `frontend/src/lib/supabase.js` — throw on missing env var instead of placeholder fallback (silent broken client).
- [x] **1.4** Extract duplicated `generate_llm_content` from `ingest_youtube.py` + `run_llm_batch.py` into `scripts/llm.py`. Both import it; removed dead `genai`/`httpx` imports.
- [x] **1.5** `ingest_stocks.py` — now saves Finnhub `company_news` (was fetched + discarded) via `ingest_news.save_news` (dedup-aware). source=finnhub, tier 2, top 10/ticker.
- [x] **1.6** Postgres dedup: added `pg_trgm` ext + `title_hash` col + GIN trgm index + `match_similar_news()` RPC in schema. `save_news` now: exact-url check → indexed `title_hash` check → trigram RPC narrows candidates, then precise word-Jaccard on small set (no more full-table fetch). ⚠️ MUST re-run `supabase/schema.sql` in Supabase SQL Editor before this works. Old rows have NULL title_hash (trigram RPC still covers them); optional backfill later.
- [x] **1.7** ~~Single source of truth for company synonyms~~ — STALE PREMISE: `COMPANY_SYNONYMS` lives only in `db.py`; `companies_config.py` has none. Nothing to dedup. No-op.
- [x] **1.8** Added `pytest` + `tests/` (conftest puts scripts/ on path) — 5 critical-path tests: buzz calc, dedup (Jaccard+title_hash), entity extraction (name+synonym), quota check (fake client), LLM JSON-fence parse. Also extracted `strip_json_fence()` into `llm.py` (was dup'd 3×). **5/5 pass.**

- [x] **1.9** **90-day retention (news + stocks).** New `scripts/cleanup_old_data.py` prunes `news_items` (ingested_at) + `stock_snapshots` (captured_at) older than `RETENTION_DAYS=90`; records health. Wired as `continue-on-error` step in `supabase_keepalive.yml` (runs every 12h). Compile + import + YAML verified. Live delete NOT yet run (needs env). Note: `community_signals`/`influencer_signals` also grow — add to TARGETS later if needed.

**Bugs found during Phase 1 (carry forward):**
- 🐛 Forecast enum mismatch: LLM emits only `bullish|bearish|neutral` but `InvestorHub.jsx` queries `strong_bullish`/`high_risk` → those buckets always empty. → Phase 3.
- 🐛 Disputes tab label says "last 72 hours" but query has NO time filter (`InvestorHub.jsx:48-51`). → Phase 3/4.
- ⚠️ `google.generativeai` package EOL (deprecation warning). Migrate to `google.genai`. → Phase 4.

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
- [ ] **2.12** **Global company expansion (Tier 2/3).** Grow ~54 → ~100-120, diverse by region + sector, not just top-N by cap. Mix steady anchors + dark horses. Decided 2026-05-29.
  - 🇨🇳 China: Alibaba (BABA), Tencent (TCEHY), Baidu (BIDU), PDD, BYD, SMIC, Xiaomi, Meituan, Kuaishou, Horizon Robotics.
  - 🇮🇳 India: Infosys (INFY), TCS, Wipro (WIT), HCLTech, Freshworks (FRSH), Zoho (private), Reliance Jio (private), Persistent.
  - 🇩🇪/🇪🇺 Europe: SAP, Siemens, Infineon (IFNNY), ASML (NL), Spotify (SE), Nokia, Ericsson, Mistral (have), Aleph Alpha (private DE), Helsing (private DE).
  - 🌏 Other: Samsung (KR), Sony (JP), Naver (KR), Sea Ltd (SG), MercadoLibre (AR), TSMC (have), Rakuten (JP).
  - ⚠️ Private valuations MUST be sourced/correct (current list has some stale dates). Add `region` + `country` columns to `companies` for Market Map grouping/filtering.
  - 🐎 Dark-horse criteria (curated for now, auto in 3.11): punching-above-weight / under-watched + accelerating.
- [ ] **2.13** **Better-Buzz v2 (LLM relevance ranking).** Current `calc_buzz = entities*10 + |sentiment|*20` is NOT relevance. Add `relevance` (0-100, "how much a tech investor should care") to the LLM batch prompt (already paying for the call). New `buzz_v2 = 0.5*relevance + 0.2*source_credibility + 0.15*hn_engagement + 0.15*recency_decay`, entity-tier weighted. Store on `news_items`. Feed + Market Map order by `buzz_v2 desc` (currently newest-first). Decided 2026-05-29.

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
- [ ] **3.10** **Market Map redesign** (`CompanyDashboard.jsx`). Today: flat 54-card `grid-cols-3`, sorted by `market_cap` (privates null→dumped last) → crowded, gets worse at 100+. Decided 2026-05-29. Plan:
  - Treemap layout — tiles sized by market_cap (public) / last_valuation (private). Literal "map". Color by `change_pct` (green/red) or forecast_direction.
  - Grouping + filters: by sector AND region (needs `region`/`country` cols from 2.12). Pills: All / Public / Private + sector + region dropdowns + search box.
  - Density: show top-N by buzz_v2, "show more" expander instead of dumping all. Compact-row toggle.
  - Fix sort: privates ranked by valuation, not shoved to end.
- [ ] **3.11** **Dark-Horse radar** (auto-discovery). Job scans free signals for under-watched accelerators: GitHub star-velocity spikes, HN/Reddit mention surges, SEC 8-K filers, Finnhub `recommendation`+`upgrade-downgrade`, NPM/PyPI download surges → auto-surface tickers. New InvestorHub "Dark-Horse Movers" section. The genuine differentiator. Decided 2026-05-29.
- [ ] **3.12** **InvestorHub overhaul** (`InvestorHub.jsx`). Decided 2026-05-29.
  - 🐛 FIX FIRST (structural): forecast enum mismatch — LLM emits only `bullish|bearish|neutral` but UI queries `strong_bullish`/`high_risk` → tabs can't populate. Align prompt enum ↔ DB CHECK ↔ UI query.
  - 🐛 Disputes "72h" label but no time filter → add `gte(ingested_at, 72h)`.
  - Head-to-head upgrade (`ComparisonWidget`): beyond price → side-by-side buzz_v2 trend + GitHub momentum + valuation + forecast + earnings date. Make it decision-useful.
  - New free-data sections: Dark-Horse Movers (3.11) · Earnings Countdown (3.2) · Insider Trades (3.4) · Material Events / 8-K (3.1) · Daily Digest (3.7).
  - Cadence note: forecasts/briefs/buzz refresh every 6h today; move news+LLM to ~3h for fresher intel.

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

### Phase 1 — done 2026-05-29
**Changed:**
- Deleted: `frontend/src/services/api.js` (dead v1 API client), `backend/` (entire v1 FastAPI/Kafka app), `scripts/run_consumers.py` + `scripts/run_ingestors.py` (dead Kafka runners). Verified zero importers; all 11 ingest scripts still import.
- `frontend/src/lib/supabase.js` — throws on missing env vars (was silent placeholder client).
- New `scripts/llm.py` — single `generate_llm_content()` (was dup'd in run_llm_batch + ingest_youtube) + new `strip_json_fence()` (was dup'd 3×). Both consumers import it; removed dead `genai`/`httpx` imports.
- `scripts/ingest_stocks.py` — now SAVES Finnhub `company_news` (was fetched + discarded) via dedup-aware `save_news`; source=finnhub, tier 2, ≤10/ticker.
- `scripts/ingest_news.py` — `save_news` rewritten: exact-url → indexed `title_hash` → trigram RPC candidates → precise word-Jaccard. Kills O(N²) full-table scan. New `compute_title_hash()`.
- `supabase/schema.sql` — `pg_trgm` ext, `news_items.title_hash` col, trgm GIN index, `match_similar_news()` RPC.
- `scripts/requirements.txt` — added `pytest`.
- New `tests/` — 5 critical-path unit tests (conftest puts scripts/ on path).

**Verified:** `py_compile` all touched scripts OK; all scripts import OK; `pytest tests/` → **5/5 pass**.

**NOT verified (needs live env):**
1. **Re-run `supabase/schema.sql` in Supabase SQL Editor** — REQUIRED for 1.6 (pg_trgm + title_hash + RPC). Until then `save_news` RPC call will error.
2. Live ingest run confirming Finnhub news + trigram dedup write correctly.
3. Frontend build with real env (supabase.js now throws if missing).

**Bugs found (carried forward, not fixed here):**
- 🐛 Forecast enum mismatch (LLM emits `bullish|bearish|neutral`; UI queries `strong_bullish`/`high_risk` → empty buckets). → Phase 3.
- 🐛 Disputes tab "72 hours" label but no time filter in query. → Phase 3/4.
- ⚠️ `google.generativeai` EOL → migrate to `google.genai`. → Phase 4.

**Stale plan item:** 1.7 (synonym dedup) was a false premise — synonyms only live in `db.py`. No-op.
