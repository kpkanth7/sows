# Investor Hub Refresh Design

## Goal

Rebuild the Investor Hub so its content is materially live, data-backed, and decision-useful. The redesign must preserve the tabbed workspace, remove duplicated sections, fix empty `Upcoming Events`, improve `Head-to-Head` with fresher metrics, and replace stale default-feeling forecast and influencer surfaces with ranked evidence-driven panels.

## Decisions Locked

- Keep the Investor Hub as a tabbed workspace.
- Remove `Consensus & Disputes` from Investor Hub.
- Keep `Head-to-Head` open to any two tracked companies.
- Use the `Signal Desk` layout direction rather than a denser terminal-style command center.

## User Problems Being Solved

1. `Upcoming Events` is always empty and does not reflect real catalysts.
2. `Head-to-Head` uses weak metrics that feel static and unreliable.
3. `Forecasts & Radar` feels unchanged, generic, and disconnected from recent signals.
4. `Influencer Trust Index` appears static and does not show movement or evidence.
5. `Consensus & Disputes` duplicates `News & Signals` and adds little value here.

## Product Structure

The tab list remains, but the content is rationalized:

- `Forecasts & Radar`
- `Influencer Trust`
- `Insider Trades`
- `Dark Horse`
- `Material Events`
- `Daily Digest`

The right rail remains and contains:

- `Upcoming Events`
- `Head-to-Head`

## Forecasts & Radar

The current bucket model (`Best Bets`, `Risk Radar`, `IPO Watch`) should be removed. It reads as a static label system instead of a computed market view.

Replace it with ranked modules built from recent stored signals:

- `Momentum Leaders`
- `Risk Build-Up`
- `Catalysts Ahead`
- `Private Watchlist`

Each row or card must explain why the company is there. Supported reasons include:

- elevated recent news volume
- positive or negative sentiment swing
- analyst upgrade/downgrade movement
- insider buy/sell imbalance
- GitHub acceleration where relevant
- upcoming catalyst proximity
- strong dark-horse score

This tab should surface change and recency, not only a direction label and confidence score.

## Influencer Trust

The trust UI should stop looking like a static leaderboard. It should expose recent motion and supporting context:

- current trust score
- change versus prior score / recent delta
- total validated claims
- correct claim rate
- most recent activity time
- entities covered recently
- recent creator signal excerpts or summaries

This section should prioritize "what changed" and "why this creator matters now".

## Upcoming Events

`Upcoming Events` should be driven by real stored data, not a dead table. The panel should include the nearest catalysts from:

- `events_calendar`
- `earnings_calendar`
- any other event-like tracked records already present and reliable

Each event should show:

- company
- event type
- date / relative time
- source or category label

If a source table is empty because the pipeline never refreshes it, that pipeline must be wired into scheduled execution.

## Head-to-Head

`Head-to-Head` remains any tracked company versus any tracked company, but the comparison surface changes from weak static metrics to fresher evidence:

- valuation / market cap
- 24h move for public companies when available
- recent signal intensity
- analyst momentum in recent window
- insider activity in recent window
- GitHub momentum where applicable
- next earnings or nearest catalyst
- forecast direction and confidence

Every metric shown should also imply freshness. Private companies must not display fake public-market metrics; the widget should adapt by omitting or downgrading non-applicable rows.

## Data and Pipeline Requirements

The redesign requires backend work in addition to frontend work.

Known hard issue already confirmed:

- `ConferenceCalendar.jsx` reads `events_calendar`, but the main scheduled workflow does not populate or refresh that table.

Required backend improvements:

- wire event ingestion / refresh into the scheduled workflow
- inspect how existing event-like data is stored and aggregate it for UI use
- compute stronger head-to-head metrics from current tables rather than using only valuation, buzz average, GitHub stars, and next earnings
- replace simple forecast-direction filtering with ranked composite outputs for the forecasts tab
- expose useful influencer movement data instead of only raw trust values

## UI and Interaction Requirements

- The new layout should preserve the current page architecture and visual language.
- The right rail should remain useful even when one data source is temporarily sparse.
- Evidence and recency should be visible in small doses without overwhelming the user.
- Avoid placeholder copy that sounds synthesized or generic.
- Remove stale-feeling controls that do not map to real computed outputs.

## Verification Requirements

- Verify the event feed renders at least one upcoming item when source data exists.
- Verify `Head-to-Head` metrics differ appropriately across public/public, public/private, and private/private comparisons.
- Verify forecast modules reorder when underlying signal data changes.
- Verify influencer trust section shows deltas or other proof of update rather than only absolute scores.
- Verify localhost renders the refreshed Investor Hub without broken loading or empty-state regressions.
