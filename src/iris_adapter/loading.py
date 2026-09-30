import json

import psycopg
from psycopg.types.json import Jsonb

from iris_adapter.models import CanonicalRecord


_UPSERT_SQL = """
INSERT INTO staging.records (
    country_code,
    region_code,
    source_id,
    source_record_id,
    source_date,
    fetched_at,
    attributes,
    geom
)
VALUES (
    %s, %s, %s, %s, %s, %s, %s,
    ST_SetSRID(ST_GeomFromGeoJSON(%s::text), 4326)
)
ON CONFLICT (country_code, source_id, source_record_id)
DO UPDATE SET
    region_code = EXCLUDED.region_code,
    source_date = EXCLUDED.source_date,
    fetched_at = EXCLUDED.fetched_at,
    attributes = EXCLUDED.attributes,
    geom = EXCLUDED.geom
"""


class PostgresLoader:
    """Store a previously validated canonical batch in one transaction."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def load(self, records: list[CanonicalRecord]) -> None:
        if not records:
            return

        parameters = [
            (
                record.country_code,
                record.region_code,
                record.source_id,
                record.source_record_id,
                record.source_date,
                record.fetched_at,
                Jsonb(record.attributes),
                (
                    json.dumps(record.geom, allow_nan=False)
                    if record.geom is not None
                    else None
                ),
            )
            for record in records
        ]

        with psycopg.connect(self.dsn, connect_timeout=5) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(_UPSERT_SQL, parameters)