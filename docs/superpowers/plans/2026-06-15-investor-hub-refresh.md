# Investor Hub Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild Investor Hub around live ranked signal data, repair the empty events pipeline, and upgrade head-to-head plus influencer views so they reflect fresh evidence instead of static defaults.

**Architecture:** Keep the tabbed `InvestorHub` surface, but replace simplistic client-side fetch and display logic with stronger backend-derived rankings plus adaptive comparison metrics. Reuse existing Supabase tables where possible, add lightweight data shaping in scripts, and keep the frontend split across focused components rather than one large file.

**Tech Stack:** React, Vite, Supabase JS client, Python ingestion/batch scripts, GitHub Actions scheduled workflows

---

### Task 1: Repair and expose upcoming events

**Files:**
- Modify: `/Users/pradhyumnakasula/Tech-Intel_project/.github/workflows/ingest_and_process.yml`
- Modify: `/Users/pradhyumnakasula/Tech-Intel_project/scripts/ingest_finnhub_extras.py`
- Modify: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/components/ConferenceCalendar.jsx`

- [ ] **Step 1: Inspect existing event sources and write the failing expectation**

Expectation: the 6-hour workflow should refresh at least one event-backed source used by `ConferenceCalendar.jsx`.

Run:

```bash
rg -n "events_calendar|earnings_calendar" .github/workflows scripts frontend/src/components/ConferenceCalendar.jsx
```

Expected: `ConferenceCalendar.jsx` reads `events_calendar`, while the scheduled workflow does not refresh it.

- [ ] **Step 2: Add a scheduled workflow step that refreshes event-like data**

Add a workflow step after stock/news ingestion for Finnhub extras so earnings and related catalyst data refresh every 6 hours:

```yaml
      - name: 5b. Ingest Finnhub Extras
        continue-on-error: true
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
          FINNHUB_API_KEY: ${{ secrets.FINNHUB_API_KEY }}
        run: python scripts/ingest_finnhub_extras.py
```

- [ ] **Step 3: Extend the frontend event panel to fall back across reliable sources**

Update `ConferenceCalendar.jsx` so it:

```jsx
Promise.all([
  supabase.from('events_calendar').select('*').gte('event_date', today).order('event_date', { ascending: true }).limit(8),
  supabase.from('earnings_calendar').select('company_id, earnings_date, eps_estimate, revenue_estimate, companies(name,ticker)').gte('earnings_date', today).order('earnings_date', { ascending: true }).limit(8),
])
```

Normalize those into one list with `type`, `label`, `date`, and `companyName`.

- [ ] **Step 4: Run a focused verification**

Run:

```bash
npm --prefix frontend run build
```

Expected: build passes and `ConferenceCalendar.jsx` compiles with normalized event rows.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ingest_and_process.yml scripts/ingest_finnhub_extras.py frontend/src/components/ConferenceCalendar.jsx
git commit -m "fix investor hub events pipeline"
```

### Task 2: Build stronger head-to-head metrics

**Files:**
- Modify: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/components/ComparisonWidget.jsx`
- Optional helper create: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/lib/investorHubMetrics.js`

- [ ] **Step 1: Write the failing metric inventory**

Document and verify the current weak metrics:

```bash
sed -n '1,260p' frontend/src/components/ComparisonWidget.jsx
```

Expected: only valuation, 7d buzz average, GitHub stars, next earnings, and forecast are materially compared.

- [ ] **Step 2: Add richer Supabase queries for comparison inputs**

Add data pulls for:

```jsx
const signalsWindow = isoDaysAgo(7);
const analystWindow = isoDaysAgo(30);
const insiderWindow = isoDaysAgo(30);
```

Query sources:

```jsx
supabase.from('news_items').select('entity_names,buzz_v2,sentiment_score,published_at').gte('published_at', signalsWindow)
supabase.from('analyst_recommendations').select('company_id,buy,hold,sell,strong_buy,strong_sell,period').gte('period', analystWindowDate)
supabase.from('insider_transactions').select('company_id,transaction_date,transaction_code,shares,transaction_price').gte('transaction_date', insiderWindowDate)
supabase.from('earnings_calendar').select('company_id,earnings_date').gte('earnings_date', today)
supabase.from('github_signals').select('company_id,stars_this_week,collected_at').gte('collected_at', signalsWindow)
```

- [ ] **Step 3: Compute adaptive comparison rows**

Implement rows similar to:

```jsx
[
  { key: 'valuation', label: 'Valuation', left: formatCurrency(...), right: formatCurrency(...), freshness: 'latest known' },
  { key: 'priceMove24h', label: '24H Move', left: formatPercentOrNA(...), right: formatPercentOrNA(...), freshness: 'market snapshot' },
  { key: 'signalIntensity7d', label: 'Signal Intensity (7D)', left: ..., right: ..., freshness: '7d rolling' },
  { key: 'analystMomentum30d', label: 'Analyst Momentum', left: ..., right: ..., freshness: '30d' },
  { key: 'insiderFlow30d', label: 'Insider Flow', left: ..., right: ..., freshness: '30d' },
  { key: 'githubMomentum7d', label: 'GitHub Momentum', left: ..., right: ..., freshness: '7d' },
  { key: 'nextCatalyst', label: 'Next Catalyst', left: ..., right: ..., freshness: 'forward' },
]
```

Public/private logic should return `N/A` only where a metric truly does not apply.

- [ ] **Step 4: Rebuild the right-rail rendering**

Render each metric row with:

```jsx
<div className="comparison-row">
  <span>{leftDisplay}</span>
  <span>{label}</span>
  <span>{rightDisplay}</span>
  <small>{freshness}</small>
</div>
```

Include a short evidence line under the forecast block.

- [ ] **Step 5: Run verification**

Run:

```bash
npm --prefix frontend run build
```

Expected: build passes and the widget compiles with the adaptive metric set.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ComparisonWidget.jsx frontend/src/lib/investorHubMetrics.js
git commit -m "improve investor hub comparison metrics"
```

### Task 3: Replace default-feeling Forecasts & Radar

**Files:**
- Modify: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/components/InvestorHub.jsx`
- Create: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/components/investorhub/ForecastsRadarPanel.jsx`
- Optional create: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/lib/investorHubMetrics.js`

- [ ] **Step 1: Extract the current forecasts tab responsibilities**

Inspect:

```bash
sed -n '1,260p' frontend/src/components/InvestorHub.jsx
```

Expected: current tab uses `bestBets`, `risks`, and `ipos` buckets based mostly on forecast labels and valuation ordering.

- [ ] **Step 2: Replace simple buckets with ranked modules**

Create `ForecastsRadarPanel.jsx` that accepts:

```jsx
{
  momentumLeaders,
  riskBuildUp,
  catalystsAhead,
  privateWatchlist,
}
```

Each module renders 4-8 ranked rows with score, direction, and `why it is here`.

- [ ] **Step 3: Compute ranked modules from existing fetched data**

Implement lightweight composite logic from already available rows plus extra queries if needed:

```jsx
const score = (
  forecastConfidenceWeight +
  buzzWeight +
  sentimentWeight +
  analystWeight +
  insiderWeight +
  githubWeight +
  catalystWeight
);
```

Generate explanation chips from the dominant drivers rather than static prose.

- [ ] **Step 4: Make Dark Horse visible in the forecasts flow**

Either:

```jsx
<section>
  <h4>Dark Horse Movers</h4>
  ...
</section>
```

inside `ForecastsRadarPanel`, or a clearly linked ranked preview fed from `dark_horse_movers`.

- [ ] **Step 5: Run verification**

Run:

```bash
npm --prefix frontend run build
```

Expected: build passes and `Forecasts & Radar` compiles without the old `Best Bets / Risk Radar / IPO Watch` controls.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/InvestorHub.jsx frontend/src/components/investorhub/ForecastsRadarPanel.jsx frontend/src/lib/investorHubMetrics.js
git commit -m "refresh investor forecasts radar"
```

### Task 4: Rebuild Influencer Trust around movement and evidence

**Files:**
- Modify: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/components/InvestorHub.jsx`
- Create: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/components/investorhub/InfluencerTrustPanel.jsx`

- [ ] **Step 1: Confirm current trust UI limitations**

Inspect:

```bash
sed -n '240,360p' frontend/src/components/InvestorHub.jsx
```

Expected: the UI is a mostly static table sorted by `trust_score` with little update context.

- [ ] **Step 2: Expand the query shape**

Fetch supporting fields and recent creator signals:

```jsx
supabase.from('influencers').select('*').order('trust_score', { ascending: false }).limit(20)
supabase.from('influencer_signals').select('source_name,entity_name,content_title,published_at,summary').gte('published_at', isoDaysAgo(7)).order('published_at', { ascending: false }).limit(100)
```

- [ ] **Step 3: Derive movement-friendly rows**

For each influencer derive:

```jsx
{
  trustScore,
  validationRate,
  claimsValidated,
  lastActiveAt,
  recentEntities,
  recentTitles,
}
```

If historical trust deltas are unavailable, compute "recency" and "coverage activity" so the table still signals motion honestly instead of faking change.

- [ ] **Step 4: Render the new panel**

Render:

```jsx
<div className="trust-card">
  <header>name + trust tier</header>
  <div>validated claims / hit rate / last active</div>
  <div>recent entities</div>
  <div>recent creator signal excerpt</div>
</div>
```

Use cards or rows, but emphasize current relevance, not only raw trust.

- [ ] **Step 5: Run verification**

Run:

```bash
npm --prefix frontend run build
```

Expected: build passes and the Influencer Trust tab compiles with the new panel.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/InvestorHub.jsx frontend/src/components/investorhub/InfluencerTrustPanel.jsx
git commit -m "improve influencer trust panel"
```

### Task 5: Remove consensus/disputes and integrate the refreshed layout

**Files:**
- Modify: `/Users/pradhyumnakasula/Tech-Intel_project/frontend/src/components/InvestorHub.jsx`

- [ ] **Step 1: Remove the obsolete tab and data fetch**

Delete the `Consensus & Disputes` tab button, associated state branch, and dispute fetch logic from `InvestorHub.jsx`.

- [ ] **Step 2: Wire the new focused panels**

Mount:

```jsx
<ForecastsRadarPanel ... />
<InfluencerTrustPanel ... />
```

Keep existing `InsiderTradesPanel`, `DarkHorseMoversPanel`, `MaterialEventsPanel`, and `DigestPanel`.

- [ ] **Step 3: Run full frontend verification**

Run:

```bash
npm --prefix frontend run build
```

Expected: full production build passes.

- [ ] **Step 4: Run localhost preview**

Run:

```bash
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173
```

Expected: Vite serves successfully and Investor Hub renders locally.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/InvestorHub.jsx
git commit -m "remove investor disputes tab"
```
