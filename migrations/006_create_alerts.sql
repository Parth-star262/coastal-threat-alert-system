CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    dedupe_key TEXT NOT NULL UNIQUE,
    city TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence DOUBLE PRECISION,
    trigger TEXT NOT NULL,
    message TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    observed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_city_created
    ON alerts (city, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status_severity
    ON alerts (status, severity);
