CREATE TABLE IF NOT EXISTS storm_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    alert_level TEXT,
    title TEXT NOT NULL,
    description TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    event_time TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    link TEXT,
    source TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_storm_events_time
    ON storm_events (event_time DESC);
