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

- [x] **2.1** **DONE 2026-05-29.** Dedicated HN poller: `scripts/ingest_hackernews.py` (reuses dedup-aware `fetch_hn`) + `ingest_hackernews.yml` cron `*/20` 24/7. Repo made PUBLIC → unlimited Actions minutes (private 2000/mo couldn't afford it). Security-scanned history clean before flip.
- [x] **2.2** **DONE 2026-05-29.** `scripts/ingest_gdelt.py` (DOC API ArtList, broad tech query, entity-filtered against ALL_COMPANIES, TextBlob sentiment, dedup-aware via save_news, 429 retry). New consolidated `ingest_firehoses.yml` hourly workflow (will also host 2.3 SEC + 2.4 arXiv). Live API verified (429 from local IP — handled gracefully).
- [x] **2.3** **DONE 2026-05-29.** `scripts/ingest_sec.py` polls SEC "current filings" Atom feed for 8-K (material events), entity-matches against ALL_COMPANIES, saves at credibility tier 1 (regulatory). Wired into `ingest_firehoses.yml`. **⚠️ Requires new repo secret `SEC_USER_AGENT`** (SEC fair-access policy requires UA with contact email — 403 without). Format: `"AppName your-email@example.com"`. Set via `gh secret set SEC_USER_AGENT`. Script no-ops with warning if unset.
- [x] **2.4** **DONE 2026-05-29.** `scripts/ingest_arxiv.py` pulls latest cs.AI/cs.LG/cs.CL/cs.CV/cs.RO submissions; entity-matches title+abstract; saves as source_type=research, tier 2. Wired into `ingest_firehoses.yml`. Live-tested: 100 entries fetched, 16/50 mentioned tracked companies.

**Carry-forward bug surfaced 2026-05-29 (affects all news/papers sources):** Short generic-word company names (`Modal`, `Notion`, `Linear`, `Unity`, `Together`) false-positive via `extract_entities` word-boundary match — e.g. "tri-Modal-Dynamics" ≠ Modal Labs. Fix needs context-aware match (require "Inc"/"Labs"/sector co-mention OR multi-word canonical for ambiguous names) OR maintain a deny-list. → Phase 4 cleanup.
- [x] **2.5** **DONE 2026-05-29.** `scripts/ingest_finnhub_extras.py` pulls 4 endpoints: earnings_calendar (1 global call), insider_transactions, recommendation_trends, upgrade/downgrade (per public ticker). Quota-gated, 1.1s call spacing. 4 new tables (earnings_calendar, insider_transactions, analyst_recommendations, upgrade_downgrade) with RLS + public-read + unique constraints for idempotent upserts. New daily workflow `ingest_finnhub_extras.yml` at 22:30 UTC (post US close). Foreign tickers swallowed (Finnhub free US-only). News-sentiment endpoint skipped (redundant with TextBlob). **⚠️ RE-RUN `supabase/schema.sql`** (4 new tables). Unblocks 3.2 (earnings widget) + 3.4 (insider panel).
- [x] **2.6** **DONE 2026-05-29.** Reddit ingestor rewritten to use `/r/{sub}/hot/.rss` (feedparser). Dropped 6s sleep, no 403/429. **Trade-off:** RSS doesn't expose `score`/`num_comments` → removed the `score>30` gate that promoted Reddit posts into `news_items`; Reddit now feeds `community_signals` only (softer signal stream). Live-tested r/MachineLearning: 25 entries, 2 matched.
- [x] **2.7** **DONE 2026-05-29.** Real waste identified: `channels().list` was fetched per-channel each run (~27 units/run) to resolve the uploads playlist ID — but config already stores it (UC→UU swap done at config time). Dropped the dynamic lookup; uses `channel['playlist_id']` directly. Saves ~27 YouTube quota units per run (~50% of cost). Plan's "videos.list batched" not relevant here — current code never hit a search() N+1, just a redundant per-channel call.
- [x] **2.8** **DONE 2026-05-29.** Per-org `/orgs/X/events` REST loop (~80 calls + 80s sleeps) replaced with batched GraphQL: aliases every tracked `github_org` (87 orgs → 2 batches of 50) into single round-trips via the `RepositoryOwner` interface (handles both orgs + users in one query). Each owner returns 3 most-recently-pushed repos with the latest release. Trending search kept as 1 REST call (already efficient). Cost: ~2 GraphQL calls vs ~80 REST. `rateLimit.cost` logged per call.
- [x] **2.9** **DONE 2026-05-29.** `scripts/llm.py` generalized to a rotating provider chain. Default order: groq → cerebras → openrouter → gemini. `LLM_PROVIDER` env moves a provider to the front of the chain. Missing API keys silently skip. OpenAI-compatible providers (groq/cerebras/openrouter) share one `_call_openai_compatible` helper. **Add new optional secrets**: `CEREBRAS_API_KEY`, `OPENROUTER_API_KEY` (`gh secret set …`). 5 critical-path tests still pass. Doubles free daily LLM ceiling immediately; 3-4× when both new keys set.
- [x] **2.10** **DONE 2026-05-29 (partial coverage).** Two fixes: (a) bumped pin `yfinance==0.2.40` → `yfinance>=0.2.54` (0.2.40 was returning non-JSON / `Expecting value`); (b) added Stooq CSV fallback (free, no key) as final step after finnhub→yfinance, with yfinance→stooq suffix mapping (`.HK→.hk`, `.KS→.kr`, `.NS→.in`, etc.). Local test: Stooq covers ~3/8 sample foreign tickers (some HK ✓, US ✓; KR/IN/AX/some HK gaps). Net win vs prior null. Twelve Data/Tiingo (need keys) deferred — Stooq+yfinance-bump fills most cases. Verify via CI run.
- [x] **2.11** **DONE 2026-05-29 (substantially).** Effective cadence now: T1 `*/15`, T2 `*/30` (bumped from hourly), T3 `*/2h` market hrs; HN `*/20` 24/7 (2.1); GDELT/SEC/arXiv hourly (2.2-2.4); Finnhub extras daily 22:30 UTC (2.5); Reddit/YouTube/GitHub/Bluesky/ProductHunt/HF + LLM batch every 6h via `ingest_and_process`. Further per-source extraction (e.g. Bluesky→2h own workflow, TheNewsAPI→3h) is cosmetic — minutes are unlimited (public repo), and dedup makes re-runs cheap. Defer per-source splits to whenever a source genuinely needs faster cadence.
- [x] **2.12** **Global company expansion — DONE 2026-05-29.** 54 → **120** tech-only (5 T1 / 37 T2 / 78 T3), 77 public / 43 private, 0 dups. Regions: US, China, India, Europe, Korea, Japan, SE Asia, LatAm, Australia, Canada, Taiwan, Middle East. Added `region` to every config entry + `companies.region` col (idempotent ALTER) + index. Fixed two latent bugs: (a) `ingest_stocks` never wrote `last_valuation`/`valuation_source` → IPO Watch valuations were never populated from config; now written. (b) existing rows never got descriptive updates → refactored to reconcile ticker/is_private/sector/is_ai_company/github_org/region/valuation from config every run (poll_tier excluded — owned by buzz promotions). Valuations web-researched current: Anthropic $965B, OpenAI $852B, Databricks $134B, Cursor $29.3B, ElevenLabs $11B, Mistral $14B, Scale $29B, Stripe $91.5B, SSI $32B, Canva $42B, Figure AI $39B, Moonshot $20B, DeepSeek ~$45B. State changes: Figma→public (FIG), xAI→merged into SpaceX (valuation None). ⚠️ RE-RUN schema.sql (region col).
  - ~~Original sub-plan below~~ (kept for reference):
  - 🇨🇳 China: Alibaba (BABA), Tencent (TCEHY), Baidu (BIDU), PDD, BYD, SMIC, Xiaomi, Meituan, Kuaishou, Horizon Robotics.
  - 🇮🇳 India: Infosys (INFY), TCS, Wipro (WIT), HCLTech, Freshworks (FRSH), Zoho (private), Reliance Jio (private), Persistent.
  - 🇩🇪/🇪🇺 Europe: SAP, Siemens, Infineon (IFNNY), ASML (NL), Spotify (SE), Nokia, Ericsson, Mistral (have), Aleph Alpha (private DE), Helsing (private DE).
  - 🌏 Other: Samsung (KR), Sony (JP), Naver (KR), Sea Ltd (SG), MercadoLibre (AR), TSMC (have), Rakuten (JP).
  - ⚠️ Private valuations MUST be sourced/correct (current list has some stale dates). Add `region` + `country` columns to `companies` for Market Map grouping/filtering.
  - 🐎 Dark-horse criteria (curated for now, auto in 3.11): punching-above-weight / under-watched + accelerating.
- [x] **2.13** **DONE 2026-05-29.** Schema: added `relevance` + `buzz_v2` cols on `news_items` + `idx_news_buzz_v2 DESC NULLS LAST` index. LLM prompt extended to emit `relevance` (0-100 investor-care rating). New `compute_buzz_v2()` in `run_llm_batch`: `0.5*relevance + 0.2*source_credibility + 0.15*hn_engagement + 0.15*recency_decay`, ×1.2 if any T1 mega-cap mentioned, capped at 100. Frontend `NewsSection.jsx` orders by `buzz_v2 desc NULLS LAST` then `ingested_at desc`. Unit-spot-checked: hot T1 fresh ≈ 100, cold obscure 2-day-old ≈ 17. **⚠️ RE-RUN `supabase/schema.sql`** (relevance + buzz_v2 cols). Old rows have NULL buzz_v2 until LLM batch re-processes them.

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

- [x] **3.1** **Material events stream — DONE 2026-05-30.** Chose pill-inside-News over top-of-page strip (per user: "good info but not enough to be above News"). Changes:
  - `NewsSection.jsx`: added `Filings` pill; new `SOURCE_FILTER` map branches the query to `.eq('source','sec_edgar')` instead of `.eq('category', …)`.
  - `NewsCard.jsx`: gold `SEC 8-K` badge + `NEW TICKER` blue tag when SEC + no tracked entity match (surprise-ticker visual cue).
  - `ingest_sec.py`: added tech-keyword whitelist (`TECH_KEYWORDS` + `_has_tech_keyword`) so unmatched 8-Ks still save when title contains AI/ML/cloud/chip/semi/SaaS/robotics/etc terms. Tracked-co 8-Ks always save; mortgage-trust/small-fund noise dropped.
  - Tests still 5/5 green. Live verification deferred to next SEC ingest run (hourly cron).
- [x] **3.2** **Earnings countdown + sentiment delta — DONE 2026-05-30.** Surfaced inside existing `Earnings` pill in News & Signals (per user — reuses real estate rather than new dashboard section). Changes:
  - Schema: `earnings_calendar` gained `sentiment_pre`, `sentiment_post`, `sentiment_delta` cols (idempotent `ADD COLUMN IF NOT EXISTS`). **⚠️ RE-RUN `supabase/schema.sql`**.
  - New `scripts/compute_earnings_delta.py`: for each row whose T+7d window has closed (and delta IS NULL), computes avg news_items sentiment in [T-7,T-1] vs [T+1,T+7], writes pre/post/delta. Idempotent.
  - Wired into `supabase_keepalive.yml` (runs every 12h, continue-on-error). Also fixed prior latent bug: keepalive previously `pip install supabase` only, but `cleanup_old_data.py` imports `db.py` which needs `dotenv` etc → switched to `pip install -r scripts/requirements.txt`.
  - New `frontend/src/components/EarningsStrip.jsx`: 2-row strip (Upcoming Next 7d countdown · Past 7d sentiment delta chip + EPS beat/miss). Mounted in `NewsSection.jsx` only when activeCategory === 'Earnings'.
  - Verified: py_compile OK, 5/5 tests pass, frontend `npm run build` OK.
- [x] **3.3** **Real Hype-vs-Reality chart — DONE 2026-05-30.** New `HypeRealityChart.jsx` renders a 30-day dual z-score trendline in `CompanyDetailPanel` Overview tab (below the legacy flat-bar `HypeRealityMeter`, kept for back-compat across CompanyCard/ComparisonWidget). Signals:
  - Hype = daily count of `news_items` where `entity_names` contains the company name (last 30d).
  - Reality = max `stars_this_week` from `github_signals` per day (last 30d).
  - Each series z-scored vs its own 30-day mean+std so the lines share a common axis (`[-3, 3]`).
  - Verdict chip computed from the last-7d avg of each z-series: > +1 diff → Overhyped, < -1 → Underrated/High Traction, else Balanced.
  - Empty-state copy when both series are zero (new company / not enough history yet).
  - **NPM/PyPI deferred to 3.3b** — not currently ingested. Carry forward as own ingestor + schema + `companies.npm_package`/`pypi_package` config fields.
  - Verified: `npm run build` OK. Live verification deferred to next deploy.
- [x] **3.4** **Insider trades panel — DONE 2026-05-30.** Single shared `InsiderTradesPanel.jsx` powers two placements: (a) global `Insider Trades` tab inside `InvestorHub` (no companyId prop → cross-co), (b) per-company `Insider` tab inside `CompanyDetailPanel` (passes `company.id`). Filter: `|change| ≥ 10,000` shares (notable only — hides routine grant noise). Window: last 30d. Buy/sell arrow + green/red color from sign of `change`. Empty state when no qualifying rows. Built off existing `insider_transactions` table from Phase 2.5 (Finnhub Form 4). Verified: `npm run build` OK.
- [x] **3.5** **Controversy tracker (CourtListener) — DONE 2026-05-30.** New `scripts/ingest_courtlistener.py` polls Free Law Project's RECAP search API (v4) per public tracked company (7d lookback, 5/co cap). Writes hits into `news_items` as `source='courtlistener'`, `category='controversy'`, `source_credibility_tier=1` — auto-surfaces in existing Controversy News pill, zero new schema. Wired into `ingest_firehoses.yml` (hourly). New optional secret `COURTLISTENER_API_TOKEN` (free signup, 5000/hr quota; unauth fallback works but capped ~100/day — script warns when missing). `NewsCard.jsx`: red `LAWSUIT` badge with `Scale` icon when `source==='courtlistener'`. Verified: py_compile OK, 5/5 tests, `npm run build` OK. **⚠️ Action: set `COURTLISTENER_API_TOKEN` repo secret** (else low-quota fallback).
- [x] **3.6** **R&D / arXiv pill — DONE 2026-05-30 (minimal scope).** Added `Research` pill to NewsSection categories; `SOURCE_FILTER` extended with `'Research': 'arxiv'`. `NewsCard.jsx`: blue `arXiv` badge with `BookOpen` icon when `source==='arxiv'`. arXiv data already ingested via 2.4 (cs.AI/LG/CL/CV/RO). **Patents skipped per user choice** — USPTO PatentsView ingestor + per-co R&D drill-down deferred. Carry forward as 3.6b: `ingest_uspto.py` + extend pill filter to `source IN ('uspto','arxiv')` when shipped. Verified: `npm run build` OK.
- [x] **3.7** **Daily investor digest — DONE 2026-05-30.** New `scripts/generate_daily_digest.py` builds a prompt from last-24h signals: top 20 news by buzz_v2, SEC 8-Ks, notable insider trades (≥10K shares), upcoming earnings (next 7d), recent earnings (last 7d with sentiment_delta). LLM emits strict JSON `{summary, top_tickers}` — graceful fallback to frequency-based top tickers when JSON parse fails. Persists to new `daily_digests` table (PK=digest_date, UPSERT on re-run). New workflow `daily_digest.yml` runs 02:00 UTC daily after most ingestors stabilize. New `frontend/src/components/DailyDigestBanner.jsx` mounted in `App.jsx` above tab-content — collapsible hero card with summary + top-ticker gold chips. **⚠️ RE-RUN `supabase/schema.sql`** (new `daily_digests` table + RLS public-read policy). Verified: py_compile OK, 5/5 tests, YAML lint OK, `npm run build` OK. Live verification on next 02:00 UTC cron (or manual dispatch).
- [x] **3.8** **Influencer trust decay rebuild — DONE 2026-05-30.** Replaced 69-line naive word-overlap stub with: (a) LLM batch validator (6 claims/prompt) emitting strict JSON `{claim_id: CONFIRM|REFUTE|AMBIGUOUS}` over tier-1/2 news evidence in [made_at, +10d] window; (b) trust deltas CONFIRM +0.025 / REFUTE -0.040 / AMBIGUOUS skip, clamped to [0.05, 0.60]; (c) every-run time decay pulling every influencer 1% toward the 0.20 baseline (silent influencers drift home, high-trust requires fresh wins); (d) quota-gated — decay always runs even when the LLM chain is exhausted. Validation kicks in at 7d age (gives news time to surface). Updated both `ingest_and_process.yml` (step 8) and `run_llm_batch.yml` env blocks with the full LLM provider-chain secrets + PYTHONPATH; also normalized run_llm_batch.yml's broken `python -m scripts.X` invocation (bare imports incompatible) → `python scripts/X.py`. Verified: py_compile OK, 5/5 tests, YAML lint OK.
- [x] **3.9** **Supabase Realtime — DONE 2026-05-30.** `NewsSection.jsx` now opens a `supabase.channel('news_inserts')` subscription on `postgres_changes` INSERT for `news_items`. Handler mirrors `fetchNews`'s filter logic (SOURCE_FILTER source-eq for Filings/Research pills, else mapCategory → category-eq, else All), enforces the 3-day `ingested_at` window defensively, dedupes against current state by `id`, and `setNews(prev => [row, ...prev])` auto-prepends. Effect re-subscribes on `activeCategory` change so the closure sees the active filter; cleanup calls `supabase.removeChannel`. Scope is news_items only — stocks/companies/digests keep their existing refresh cadence. No toast/badge UX (auto-prepend chosen). Verified: `npm run build` OK.
- [x] **3.10** **Market Map redesign — DONE 2026-05-30.** Rewrote `CompanyDashboard.jsx`: flat `grid-cols-3` of `CompanyCard` → recharts `<Treemap>` (650px ResponsiveContainer). Tiles SIZED by effective value (`market_cap || last_valuation || 0`) — fixes the longstanding privates-shoved-to-end sort. Tiles COLORED by `change_pct_24h` via a dark-surface → green/red gradient with magnitude clamped at ±5%; null/zero → neutral gray so privates don't fake red. Custom `TreemapTile` renderer draws ticker label + signed % inside each tile, auto-hides label when width<60px or height<30px to avoid crowding. Three AND-combined filter rows added above the map: sector pills (derived from distinct `companies.sector`), region pills (derived from `companies.region`, populated in 2.12), and public/private toggle. Click handler on each tile preserves existing `CompanyDetailPanel` slide-over behavior. `CompanyCard.jsx` left untouched (still used by `ComparisonWidget`). Verified: `npm run build` OK.
- [x] **3.11** **Dark-Horse radar — DONE 2026-05-30 (backend layer).** Scope: tracked 120 only (user choice). Equal-weight 4-signal composite (user explicit: dilute single-source bias). New `scripts/compute_dark_horses.py` bulk-fetches last-30d signals (one query per source table, grouped in-memory) then scores each company on 4 sub-scores normalized to 0-100: (a) GH `stars_this_week` z-score recent-7d vs prior-23d, (b) news_items entity-mention daily count z-score same window, (c) analyst upgrade momentum `(ups - downs)` last 7d cohort-normalized, (d) insider buy ratio + stock 7d % momentum combined (50-centered). Composite = mean of 4. Reasons array auto-generated when a sub-score ≥ 70 (`GitHub stars surging`/`News volume spike`/`Analysts piling on`/`Insider + market confirm`). Truncate-and-insert top 20 into new `dark_horse_movers` table per run. Wired into `supabase_keepalive.yml` (12h cadence, continue-on-error). **⚠️ RE-RUN `supabase/schema.sql`** (new `dark_horse_movers` table + RLS). Verified: py_compile OK, 5/5 tests, YAML lint OK. UI panel deferred to 3.12 (mounts in InvestorHub).
- [x] **3.12** **InvestorHub overhaul — DONE 2026-05-30.**
  - 🐛 **Forecast enum fix**: expanded `run_llm_batch.update_company_briefs` prompt to emit the full 5-bucket enum (`strong_bullish|bullish|neutral|bearish|high_risk`) matching schema CHECK + InvestorHub queries. Per-bucket guidance added so the LLM uses the strong/risk buckets only when warranted.
  - 🐛 **Disputes time filter fix**: added `.gte('ingested_at', since72h)` to disputes query so the "last 72 hours" label is now accurate. Previously query had no time filter; old disputes leaked.
  - **3 new tabs in InvestorHub**: `Dark-Horse` (reads `dark_horse_movers` from 3.11 with rank, score, 4 component bars, reasons chips), `Material Events` (sec_edgar last 72h, tracked-first then surprise tickers from 3.1 keyword whitelist), `Daily Digest` (latest + past-6-day summaries from 3.7). Earnings/Insider/Forecasts/Influencers/Disputes tabs kept as-is. 7 tabs total.
  - **ComparisonWidget rewrite**: replaced flat hype/sentiment bars with 4 head-to-head metrics that update with selection — Valuation (market_cap||last_valuation), Buzz_v2 7d avg per entity, GitHub stars-this-week sum (7d), next earnings date — plus both ForecastBadges side-by-side. Green-highlights the winning value per row.
  - **Cadence**: user kept 6h schedule (chose not to bump to 3h — preserves LLM quota for digest/dispute/trust validation that depend on it).
  - Verified: py_compile OK, `npm run build` OK. Live verification on next LLM batch run (forecast enum) and next supabase_keepalive run (dark-horse already populated, scored 120 cos, #1=65.9).

---

## Phase 4 — Polish, deploy & trust

**Time budget total: ~18–24h** focused work (≈4–6 evenings). Items grouped by gate.

### Gate A — Ship (must do before share-able link, ~4–6h)

- [ ] **4.0** **Vercel deploy** (~1h). Connect GH repo → root dir `frontend/`, framework Vite. Set env: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (Production + Preview). Confirm Realtime websockets work on `*.vercel.app`. Add `frontend/.env.example` (committed, placeholder values). Smoke-test live URL.
- [ ] **4.0b** **Schema re-run gate** (~15min). One-shot run of `supabase/schema.sql` in Supabase SQL Editor. Pending tables/cols from Phase 2–3: `region` col (2.12), `relevance`+`buzz_v2` cols (2.13), 4 Finnhub-extras tables (2.5), `title_hash`+`match_similar_news` RPC (1.6), `earnings_calendar` sentiment cols (3.2), `daily_digests` (3.7), `dark_horse_movers` (3.11). Idempotent — safe to re-run.
- [ ] **4.0c** **Node20 deprecation pin** (~30min). Bump `actions/checkout@v4` → `@v4.2.0+` and `actions/setup-python@v5` → `@v5.2.0+` across all 10 workflow files. Deadline June 16, 2026. Verify all green after.
- [ ] **4.0d** **Bundle/build sanity** (~30min). `npm run build` → check `dist/` size. Lazy-load Recharts on tabs that need it if >500KB gzipped. Confirm no `console.log` in production bundle.
- [ ] **4.0e** **Vercel domain + robots** (~15min). Pick `*.vercel.app` subdomain (or attach custom). Add `frontend/public/robots.txt` (allow all, point to no sitemap yet). Set `<title>` + favicon in `index.html`.

### Gate B — Trust (errors don't crash UI, you see breakage, ~5–7h)

- [ ] **4.1** **Sentry** (~1.5h). Frontend (`@sentry/react`) + Python ingestors (`sentry-sdk`). Free tier 5K events/mo. Hook into Vercel + GH Actions secrets. Filter Realtime/network blips out. **Alert**: Slack/email webhook on `error` severity only.
- [ ] **4.2** **`/status` page** (~2h). New `frontend/src/pages/Status.jsx`. Reads `health_checks` table (already populated by every job) — green/yellow/red dot per job + last-run timestamp + 24h success rate. Add quota_log row counts. Public-read (RLS already allows). Trust signal for share link.
- [ ] **4.3** **Error boundaries + skeletons** (~1.5h). Wrap each top-level route + slide-over in `<ErrorBoundary>` (fall-through to one-line "tab failed, refresh"). Skeleton loaders on every section currently rendering `null` during fetch. No spinners.
- [ ] **4.4** **URL scheme guard** (from SECURITY.md borderline, ~20min). One-line `safeUrl(u)` helper rejecting non-`http(s)`; wire into `NewsCard`, `MaterialEventsPanel`, `InvestorHub`, `ConferenceCalendar` anchor `href`s.

### Gate C — Data quality (~3–4h)

- [ ] **4.5** **Entity-match false-positive fix** (Phase 2 carry-forward, ~1.5h). `Modal`/`Notion`/`Linear`/`Unity`/`Together` falsely match common English words. Options: (a) require context co-mention (`Inc`/`Labs`/sector term within N tokens) for flagged-ambiguous names, OR (b) maintain a deny-list of short-name false-positive patterns. Pick (a). Add `companies.requires_context: bool` config flag.
- [ ] **4.6** **`google.generativeai` → `google.genai`** (~45min). EOL package. Migrate import in `scripts/llm.py` `_call_gemini`. New SDK semantics differ slightly — diff against current call. Test against live Gemini quota.
- [ ] **4.7** **DB nightly export** (~45min). New `scripts/export_snapshot.py` dumps each main table to gzipped CSV in repo `backups/YYYY-MM-DD/` via a workflow (gitignored or pushed to a separate backup repo). Free disaster recovery. **Decision needed**: where to store (S3 free tier vs GH artifacts vs separate private backup repo).

### Gate D — Polish (UX delta, can ship live without, ~6–8h)

- [ ] **4.8** **Mobile breakpoints** (~2h). Audit every component at 375px width. Treemap (3.10) needs a fallback list view <640px. Slide-over panels become full-screen modals.
- [ ] **4.9** **Inline styles → Tailwind** (~2h). Codebase already mixes Tailwind classes + inline `style={{}}`. Migrate inline → Tailwind for consistency. Keep CSS vars (`--accent-green` etc) since they're theme-aware.
- [ ] **4.10** **SEO + OG cards** (~1h). Per-company OG image deferred; static OG card on root + dynamic `<title>` per opened company OK. Add `<meta>` tags in `index.html` + `react-helmet-async` for per-route titles.
- [ ] **4.11** **README rewrite** (~1h). Match reality: 120 companies (not 60 / "100+"), real influencer count, list every active workflow + cadence, link `/status` page, architecture diagram, no claims of features not yet shipped.
- [ ] **4.12** **Lighthouse pass** (~30min). Target ≥90 perf, ≥95 a11y. Fix contrast/aria/alt issues surfaced.

### Carry-forward (deferred, not blocking Phase 4 close)

- **3.3b** NPM/PyPI download ingestor + extend HypeRealityChart Reality signal (~3h)
- **3.6b** USPTO PatentsView ingestor + per-co R&D drill-down (~3h)
- **2.6b** Reconsider Reddit→news_items promotion if RSS adds engagement metadata later

### Phase 4 time estimate

| Gate | Effort | Calendar (1–2h/evening) |
|---|---|---|
| A — Ship | 4–6h | 2–3 evenings |
| B — Trust | 5–7h | 3 evenings |
| C — Data quality | 3–4h | 2 evenings |
| D — Polish | 6–8h | 3–4 evenings |
| **Total** | **18–24h** | **~2 weeks** at 2h/day, **~4 days** focused full-time |

Recommended order: A (deploy → real users possible) → B (errors visible → won't ship invisible breakage) → C (data clean) → D (cosmetic).

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
