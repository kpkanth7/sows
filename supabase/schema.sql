-- ============================================================
-- Tech-Intel v2: Supabase Schema
-- Run this in Supabase SQL Editor to initialize the database.
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- ============================================================
-- COMPANIES
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    ticker          TEXT,                  -- NULL for private companies
    is_private      BOOLEAN NOT NULL DEFAULT false,
    sector          TEXT,
    logo_url        TEXT,
    description     TEXT,
    website         TEXT,
    founded_year    INT,

    -- Stock data (public companies)
    stock_price     NUMERIC(18,4),
    market_cap      BIGINT,               -- in USD
    change_pct_24h  NUMERIC(8,4),
    week_52_high    NUMERIC(18,4),
    week_52_low     NUMERIC(18,4),

    -- Private company valuation
    last_valuation  BIGINT,               -- in USD
    valuation_date  DATE,
    valuation_source TEXT,

    -- Geography (for Market Map grouping/filtering)
    region          TEXT,                 -- US / China / India / Europe / Korea / Japan / SE Asia / LatAm / Australia / Canada / Taiwan / Middle East

    -- Computed scores (updated by LLM batch)
    sentiment_score   NUMERIC(5,2) DEFAULT 50,  -- 0-100
    buzz_score        NUMERIC(5,2) DEFAULT 0,   -- 0-100
    hype_score        NUMERIC(5,2) DEFAULT 50,  -- media attention
    reality_score     NUMERIC(5,2) DEFAULT 50,  -- actual traction
    controversy_score NUMERIC(5,2) DEFAULT 0,   -- 0-100

    -- Investor signals (updated by LLM batch)
    forecast_direction TEXT CHECK (forecast_direction IN ('strong_bullish','bullish','neutral','bearish','high_risk')),
    forecast_confidence NUMERIC(5,2),           -- 0-100
    investor_brief  TEXT,

    -- Polling tier
    poll_tier       INT NOT NULL DEFAULT 3 CHECK (poll_tier IN (1,2,3)),

    -- Meta
    has_github      BOOLEAN DEFAULT false,
    github_org      TEXT,
    has_open_source BOOLEAN DEFAULT false,
    is_ai_company   BOOLEAN DEFAULT false,
    recent_event    TEXT,                 -- 'ipo', 'acquired', 'merger', 'funding' or NULL
    recent_event_date DATE,

    last_updated    TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker);
CREATE INDEX IF NOT EXISTS idx_companies_poll_tier ON companies(poll_tier);
CREATE INDEX IF NOT EXISTS idx_companies_buzz ON companies(buzz_score DESC);

-- Idempotent add for existing DBs (CREATE TABLE above is a no-op once table exists).
ALTER TABLE companies ADD COLUMN IF NOT EXISTS region TEXT;
CREATE INDEX IF NOT EXISTS idx_companies_region ON companies(region);

-- ============================================================
-- STOCK SNAPSHOTS (time-series)
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_snapshots (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id  UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    price       NUMERIC(18,4),
    market_cap  BIGINT,
    change_pct  NUMERIC(8,4),
    volume      BIGINT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stock_snapshots_company_time ON stock_snapshots(company_id, captured_at DESC);

-- ============================================================
-- NEWS ITEMS
-- ============================================================
CREATE TABLE IF NOT EXISTS news_items (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title               TEXT NOT NULL,
    summary             TEXT,                -- LLM-generated summary
    url                 TEXT UNIQUE NOT NULL,
    url_hash            TEXT UNIQUE NOT NULL, -- MD5 of URL for fast dedup

    -- Source metadata
    source              TEXT NOT NULL,        -- 'hackernews', 'rss_techcrunch', 'reddit', etc.
    source_type         TEXT NOT NULL CHECK (source_type IN ('news','research','community','influencer','code')),
    source_credibility_tier INT NOT NULL DEFAULT 3 CHECK (source_credibility_tier IN (1,2,3,4)),

    -- Content
    category            TEXT CHECK (category IN ('ai','release','ma','ipo','controversy','conference','opensource','earnings','other')),
    entity_names        JSONB DEFAULT '[]',   -- array of company/tech names mentioned
    sentiment           NUMERIC(4,2),         -- -1.0 to 1.0
    buzz_score          NUMERIC(5,2) DEFAULT 0,

    -- Dispute tracking
    is_disputed         BOOLEAN DEFAULT false,
    dispute_claim_a     TEXT,
    dispute_confidence_a NUMERIC(5,2),
    dispute_sources_a   JSONB DEFAULT '[]',
    dispute_claim_b     TEXT,
    dispute_confidence_b NUMERIC(5,2),
    dispute_sources_b   JSONB DEFAULT '[]',
    dispute_brief       TEXT,               -- LLM reconciliation brief

    -- Extras
    image_url           TEXT,
    author              TEXT,
    hn_score            INT,
    hn_comments         INT,

    -- Processing flags
    llm_processed       BOOLEAN DEFAULT false,
    dispute_checked     BOOLEAN DEFAULT false,

    published_at        TIMESTAMPTZ,
    ingested_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_news_ingested ON news_items(ingested_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_category ON news_items(category);
CREATE INDEX IF NOT EXISTS idx_news_buzz ON news_items(buzz_score DESC);
CREATE INDEX IF NOT EXISTS idx_news_disputed ON news_items(is_disputed) WHERE is_disputed = true;
CREATE INDEX IF NOT EXISTS idx_news_entities ON news_items USING GIN(entity_names);
CREATE INDEX IF NOT EXISTS idx_news_llm_unprocessed ON news_items(llm_processed) WHERE llm_processed = false;

-- Trigram near-dup detection (replaces O(N^2) Python Jaccard scan).
-- title_hash = MD5 of normalized, stop-word-stripped, sorted title words (exact-after-normalize dedup).
-- GIN trigram index narrows near-dup candidates server-side; app does final Jaccard on the small candidate set.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
ALTER TABLE news_items ADD COLUMN IF NOT EXISTS title_hash TEXT;
CREATE INDEX IF NOT EXISTS idx_news_title_hash ON news_items(title_hash);
CREATE INDEX IF NOT EXISTS idx_news_title_trgm ON news_items USING GIN (title gin_trgm_ops);

-- Returns recent news whose title is trigram-similar to p_title (indexed, fast).
-- p_threshold kept loose; the application applies the precise word-Jaccard cutoff on these candidates.
CREATE OR REPLACE FUNCTION match_similar_news(
    p_title TEXT,
    p_since TIMESTAMPTZ,
    p_threshold REAL DEFAULT 0.3
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    source_credibility_tier INT,
    hn_score INT,
    hn_comments INT,
    entity_names JSONB
)
LANGUAGE sql STABLE AS $$
    SELECT n.id, n.title, n.source_credibility_tier, n.hn_score, n.hn_comments, n.entity_names
    FROM news_items n
    WHERE n.published_at >= p_since
      AND similarity(n.title, p_title) >= p_threshold
    ORDER BY similarity(n.title, p_title) DESC
    LIMIT 20;
$$;

-- ============================================================
-- CLAIMS (for influencer trust tracking + dispute engine)
-- ============================================================
CREATE TABLE IF NOT EXISTS claims (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    news_item_id        UUID REFERENCES news_items(id) ON DELETE SET NULL,
    entity_name         TEXT NOT NULL,        -- company or tech being claimed about
    claim_text          TEXT NOT NULL,
    claim_type          TEXT,                 -- 'benchmark_best', 'acquisition', 'ipo', 'controversy', etc.
    source_name         TEXT NOT NULL,
    source_type         TEXT NOT NULL,
    credibility_weight  NUMERIC(4,3) NOT NULL DEFAULT 0.5,
    made_at             TIMESTAMPTZ NOT NULL,
    validated           BOOLEAN,              -- NULL = pending, TRUE = confirmed, FALSE = refuted
    validated_at        TIMESTAMPTZ,
    validated_by        TEXT                  -- source that confirmed/refuted
);

CREATE INDEX IF NOT EXISTS idx_claims_entity ON claims(entity_name);
CREATE INDEX IF NOT EXISTS idx_claims_validated ON claims(validated) WHERE validated IS NULL;
CREATE INDEX IF NOT EXISTS idx_claims_made_at ON claims(made_at DESC);

-- ============================================================
-- INFLUENCERS
-- ============================================================
CREATE TABLE IF NOT EXISTS influencers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    platform        TEXT NOT NULL CHECK (platform IN ('youtube','bluesky','reddit','twitter')),
    channel_id      TEXT,                  -- YouTube channel ID or Bluesky handle
    category        TEXT,                  -- 'ai_ml', 'tech_general', 'startup', 'finance', 'dev'
    subscriber_count BIGINT,
    trust_score     NUMERIC(4,3) DEFAULT 0.200,  -- 0.050 to 0.600
    total_claims    INT DEFAULT 0,
    correct_claims  INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    last_checked    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INFLUENCER SIGNALS
-- ============================================================
CREATE TABLE IF NOT EXISTS influencer_signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    influencer_id   UUID NOT NULL REFERENCES influencers(id) ON DELETE CASCADE,
    platform        TEXT NOT NULL,
    entity_name     TEXT,
    signal_type     TEXT,                  -- 'positive', 'negative', 'neutral', 'hype'
    content_title   TEXT,
    content_url     TEXT,
    engagement_score NUMERIC(10,2),        -- views/likes/upvotes normalized
    view_count      BIGINT,
    like_count      INT,
    published_at    TIMESTAMPTZ,
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inf_signals_entity ON influencer_signals(entity_name);
CREATE INDEX IF NOT EXISTS idx_inf_signals_published ON influencer_signals(published_at DESC);

-- ============================================================
-- COMMUNITY SIGNALS (Reddit, HN)
-- ============================================================
CREATE TABLE IF NOT EXISTS community_signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source          TEXT NOT NULL,          -- 'reddit_r_technology', 'hackernews', etc.
    entity_name     TEXT,
    post_title      TEXT,
    post_url        TEXT UNIQUE,
    post_score      INT,
    comment_count   INT,
    sentiment       NUMERIC(4,2),
    captured_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_community_entity ON community_signals(entity_name);
CREATE INDEX IF NOT EXISTS idx_community_captured ON community_signals(captured_at DESC);

-- ============================================================
-- GITHUB SIGNALS
-- ============================================================
CREATE TABLE IF NOT EXISTS github_signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_name       TEXT NOT NULL,
    company_id      UUID REFERENCES companies(id) ON DELETE SET NULL,
    repo_url        TEXT,
    stars           INT,
    forks           INT,
    stars_this_week INT,
    open_issues     INT,
    language        TEXT,
    latest_release  TEXT,
    release_date    TIMESTAMPTZ,
    is_trending     BOOLEAN DEFAULT false,
    captured_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_github_company ON github_signals(company_id);
CREATE INDEX IF NOT EXISTS idx_github_trending ON github_signals(is_trending) WHERE is_trending = true;
CREATE INDEX IF NOT EXISTS idx_github_stars ON github_signals(stars DESC);

-- ============================================================
-- AI BENCHMARKS
-- ============================================================
CREATE TABLE IF NOT EXISTS benchmarks (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id              UUID REFERENCES companies(id) ON DELETE CASCADE,
    model_name              TEXT NOT NULL,
    benchmark_name          TEXT NOT NULL,   -- 'MMLU', 'HumanEval', 'MATH', 'GPQA', etc.
    score                   NUMERIC(8,4),
    score_unit              TEXT DEFAULT '%', -- '%' or 'pass@1' etc.
    source_url              TEXT,
    source_credibility_tier INT DEFAULT 2,
    is_disputed             BOOLEAN DEFAULT false,
    dispute_brief           TEXT,
    is_self_reported        BOOLEAN DEFAULT true,
    captured_at             TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_benchmarks_company ON benchmarks(company_id);
CREATE INDEX IF NOT EXISTS idx_benchmarks_name ON benchmarks(benchmark_name);

-- ============================================================
-- EVENTS CALENDAR
-- ============================================================
CREATE TABLE IF NOT EXISTS events_calendar (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_name      TEXT NOT NULL,
    company_ids     JSONB DEFAULT '[]',      -- array of company UUIDs
    company_names   JSONB DEFAULT '[]',      -- denormalized for fast display
    event_date      DATE NOT NULL,
    event_type      TEXT CHECK (event_type IN ('conference','earnings','ipo','product_launch','acquisition','funding')),
    description     TEXT,
    url             TEXT,
    is_upcoming     BOOLEAN, -- Computed on frontend or updated via worker
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_date ON events_calendar(event_date);

-- ============================================================
-- COMPANY POLL CONFIG (tier management)
-- ============================================================
CREATE TABLE IF NOT EXISTS company_poll_config (
    company_id          UUID PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
    base_tier           INT NOT NULL DEFAULT 3,
    current_tier        INT NOT NULL DEFAULT 3,
    promoted_at         TIMESTAMPTZ,
    promotion_expires   TIMESTAMPTZ,
    buzz_spike_count    INT DEFAULT 0,       -- how many times promoted
    last_news_volume_6h INT DEFAULT 0,
    avg_news_volume_6h  NUMERIC(6,2) DEFAULT 1,
    last_sentiment_delta NUMERIC(6,2) DEFAULT 0
);

-- ============================================================
-- API QUOTA LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS api_quota_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_name     TEXT NOT NULL UNIQUE,
    calls_today     INT DEFAULT 0,
    daily_limit     INT NOT NULL,
    calls_this_min  INT DEFAULT 0,
    per_min_limit   INT,
    last_reset      DATE DEFAULT CURRENT_DATE,
    last_updated    TIMESTAMPTZ DEFAULT NOW()
);

-- Insert initial quota records
INSERT INTO api_quota_log (source_name, calls_today, daily_limit, calls_this_min, per_min_limit) VALUES
    ('finnhub', 0, 86400, 0, 60),
    ('alpha_vantage', 0, 25, 0, 5),
    ('thenewsapi', 0, 100, 0, NULL),
    ('youtube', 0, 10000, 0, NULL),
    ('reddit', 0, 144000, 0, 100),
    ('stackexchange', 0, 10000, 0, 30),
    ('github', 0, 5000, 0, NULL),
    ('gemini', 0, 1000, 0, 15),
    ('devto', 0, 86400, 0, 1),
    ('arxiv', 0, 28800, 0, NULL)
ON CONFLICT (source_name) DO NOTHING;

-- ============================================================
-- HEALTH CHECKS (last-run status per ingest/process job)
-- ============================================================
CREATE TABLE IF NOT EXISTS health_checks (
    job_name        TEXT PRIMARY KEY,
    status          TEXT NOT NULL,          -- 'ok' | 'error' | 'partial'
    detail          TEXT,                   -- short error/summary string
    last_run        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_last_run ON health_checks(last_run DESC);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE influencers ENABLE ROW LEVEL SECURITY;
ALTER TABLE influencer_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE benchmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE events_calendar ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_poll_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_quota_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_checks ENABLE ROW LEVEL SECURITY;

-- Public READ-ONLY policies (anon key can SELECT only)
DROP POLICY IF EXISTS "public_read_companies" ON companies;
CREATE POLICY "public_read_companies"         ON companies          FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_stock_snapshots" ON stock_snapshots;
CREATE POLICY "public_read_stock_snapshots"   ON stock_snapshots    FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_news_items" ON news_items;
CREATE POLICY "public_read_news_items"        ON news_items         FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_influencers" ON influencers;
CREATE POLICY "public_read_influencers"       ON influencers        FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_inf_signals" ON influencer_signals;
CREATE POLICY "public_read_inf_signals"       ON influencer_signals FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_community" ON community_signals;
CREATE POLICY "public_read_community"         ON community_signals  FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_github" ON github_signals;
CREATE POLICY "public_read_github"            ON github_signals     FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_benchmarks" ON benchmarks;
CREATE POLICY "public_read_benchmarks"        ON benchmarks         FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_events" ON events_calendar;
CREATE POLICY "public_read_events"            ON events_calendar    FOR SELECT USING (true);
DROP POLICY IF EXISTS "public_read_health_checks" ON health_checks;
CREATE POLICY "public_read_health_checks"     ON health_checks      FOR SELECT USING (true);
-- claims and poll_config and quota_log are internal — no public read
DROP POLICY IF EXISTS "no_public_claims" ON claims;
CREATE POLICY "no_public_claims"              ON claims             FOR SELECT USING (false);
DROP POLICY IF EXISTS "no_public_poll_config" ON company_poll_config;
CREATE POLICY "no_public_poll_config"         ON company_poll_config FOR SELECT USING (false);
DROP POLICY IF EXISTS "no_public_quota_log" ON api_quota_log;
CREATE POLICY "no_public_quota_log"           ON api_quota_log      FOR SELECT USING (false);

-- NOTE: INSERT/UPDATE/DELETE are only done by GitHub Actions using the
-- service_role key which bypasses RLS entirely. The anon key has NO write access.

-- ============================================================
-- KEEPALIVE FUNCTION (called by GitHub Actions every 12hr)
-- ============================================================
CREATE OR REPLACE FUNCTION keepalive()
RETURNS TEXT AS $$
BEGIN
    RETURN 'alive at ' || NOW()::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- USEFUL VIEWS
-- ============================================================

-- Latest stock price per company
CREATE OR REPLACE VIEW v_company_latest_stock AS
SELECT DISTINCT ON (company_id)
    c.id, c.name, c.ticker, c.is_private,
    s.price, s.market_cap, s.change_pct, s.captured_at
FROM companies c
LEFT JOIN stock_snapshots s ON s.company_id = c.id
ORDER BY company_id, s.captured_at DESC;

-- Top buzz news (last 24 hours)
CREATE OR REPLACE VIEW v_top_news_24h AS
SELECT * FROM news_items
WHERE ingested_at > NOW() - INTERVAL '24 hours'
ORDER BY buzz_score DESC
LIMIT 100;

-- Disputed news items
CREATE OR REPLACE VIEW v_disputed_news AS
SELECT * FROM news_items
WHERE is_disputed = true
ORDER BY ingested_at DESC;

-- Companies needing tier promotion check
CREATE OR REPLACE VIEW v_promotion_candidates AS
SELECT c.id, c.name, pc.current_tier, pc.last_news_volume_6h,
       pc.avg_news_volume_6h, pc.last_sentiment_delta, pc.promotion_expires
FROM companies c
JOIN company_poll_config pc ON pc.company_id = c.id
WHERE pc.promotion_expires IS NULL OR pc.promotion_expires < NOW();
