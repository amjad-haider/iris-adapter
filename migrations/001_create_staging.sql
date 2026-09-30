CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.records (
    country_code TEXT NOT NULL
        CHECK (country_code ~ '^[A-Z]{2}$'),

    region_code TEXT
        CHECK (region_code IS NULL OR btrim(region_code) <> ''),

    source_id TEXT NOT NULL
        CHECK (btrim(source_id) <> ''),

    source_record_id TEXT NOT NULL
        CHECK (btrim(source_record_id) <> ''),

    source_date DATE NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,

    attributes JSONB NOT NULL
        CHECK (jsonb_typeof(attributes) = 'object'),

    geom geometry(Geometry, 4326),

    PRIMARY KEY (country_code, source_id, source_record_id),

    CONSTRAINT records_geom_valid CHECK (
        geom IS NULL
        OR (NOT ST_IsEmpty(geom) AND ST_IsValid(geom))
    )
);

CREATE INDEX IF NOT EXISTS records_geom_idx
    ON staging.records USING GIST (geom);