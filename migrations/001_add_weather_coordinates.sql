ALTER TABLE weather_data
    ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS pressure DOUBLE PRECISION;

CREATE INDEX IF NOT EXISTS idx_weather_data_city_timestamp
    ON weather_data (city, timestamp DESC);
