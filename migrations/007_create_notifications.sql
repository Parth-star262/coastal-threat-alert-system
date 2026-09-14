CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    alert_id BIGINT NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    channel TEXT NOT NULL,
    recipient TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (alert_id, channel)
);

CREATE INDEX IF NOT EXISTS idx_notifications_alert
    ON notifications (alert_id, created_at DESC);
