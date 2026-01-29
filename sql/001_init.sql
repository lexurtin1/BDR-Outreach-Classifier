-- Schema initialization for lead_engine

CREATE TABLE IF NOT EXISTS source_registry (
    source_id       SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    type            TEXT NOT NULL,
    base_url        TEXT,
    cadence         TEXT,
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_events (
    event_id        BIGSERIAL PRIMARY KEY,
    source_id       INTEGER NOT NULL REFERENCES source_registry(source_id) ON DELETE CASCADE,
    pulled_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_json    JSONB NOT NULL,
    checksum        TEXT NOT NULL,
    UNIQUE (source_id, checksum)
);
CREATE INDEX IF NOT EXISTS idx_raw_events_source_time ON raw_events(source_id, pulled_at DESC);

CREATE TABLE IF NOT EXISTS signals (
    signal_id       BIGSERIAL PRIMARY KEY,
    source_id       INTEGER NOT NULL REFERENCES source_registry(source_id) ON DELETE CASCADE,
    signal_time     TIMESTAMPTZ,
    geo             TEXT NOT NULL,
    theme_hint      TEXT,
    signal_type     TEXT NOT NULL, -- contract | grant | macro
    value_num       NUMERIC,
    org_name        TEXT,
    title           TEXT NOT NULL,
    summary         TEXT,
    evidence_url    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_signals_source_time ON signals(source_id, signal_time DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_signals_theme ON signals(theme_hint);

CREATE TABLE IF NOT EXISTS insights (
    insight_id          BIGSERIAL PRIMARY KEY,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    theme               TEXT NOT NULL,
    headline            TEXT NOT NULL,
    why_now             TEXT NOT NULL,
    servicenow_angle    TEXT NOT NULL,
    target_suggestions  JSONB NOT NULL,
    evidence_links      JSONB NOT NULL,
    confidence          NUMERIC
);
CREATE INDEX IF NOT EXISTS idx_insights_created ON insights(created_at DESC);
