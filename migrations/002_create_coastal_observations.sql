CREATE TABLE IF NOT EXISTS coastal_observations (
    id BIGSERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    wave_height_m DOUBLE PRECISION,
    sea_level_height_m DOUBLE PRECISION,
    sea_surface_temperature_c DOUBLE PRECISION,
    ocean_current_velocity_kmh DOUBLE PRECISION,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_coastal_observations_city_time
    ON coastal_observations (city, observed_at DESC);
