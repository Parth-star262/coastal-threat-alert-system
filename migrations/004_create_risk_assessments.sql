CREATE TABLE IF NOT EXISTS risk_assessments (
    city TEXT PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    factors JSONB NOT NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_risk_assessments_level
    ON risk_assessments (risk_level);
