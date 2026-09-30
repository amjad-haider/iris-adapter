import os
from dataclasses import replace
from datetime import UTC, date, datetime
from uuid import uuid4
from pathlib import Path

import psycopg
import pytest
from psycopg.errors import CheckViolation

from iris_adapter.loading import PostgresLoader
from iris_adapter.models import CanonicalRecord
from iris_adapter.adapters.csv_points import CsvPointAdapter
from iris_adapter.pipeline import run_pipeline


@pytest.fixture
def database_case():
    dsn = os.getenv("IRIS_DATABASE_URL")
    if not dsn:
        pytest.skip("Set IRIS_DATABASE_URL to run database tests")

    source_id = f"pytest-{uuid4().hex}"

    try:
        yield dsn, source_id
    finally:
        with psycopg.connect(dsn, connect_timeout=5) as connection:
            connection.execute(
                """
                DELETE FROM staging.records
                WHERE country_code IN ('DE', 'AT') AND source_id = %s
                """,
                (source_id,),
            )


def make_record(source_id, record_id):
    return CanonicalRecord(
        country_code="DE",
        region_code="NW",
        source_id=source_id,
        source_record_id=record_id,
        source_date=date(2026, 9, 1),
        fetched_at=datetime(2026, 9, 29, tzinfo=UTC),
        attributes={"name": "Original site"},
        geom=None,
    )


def read_rows(dsn, source_id):
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        return connection.execute(
            """
            SELECT source_record_id, attributes
            FROM staging.records
            WHERE country_code = %s AND source_id = %s
            ORDER BY source_record_id
            """,
            ("DE", source_id),
        ).fetchall()


def test_repeat_import_updates_without_duplicates(database_case):
    dsn, source_id = database_case
    loader = PostgresLoader(dsn)
    original = make_record(source_id, "record-001")

    loader.load([original])

    updated = replace(
        original,
        attributes={"name": "Updated site"},
    )
    loader.load([updated])

    assert read_rows(dsn, source_id) == [
        ("record-001", {"name": "Updated site"})
    ]


def test_database_error_rolls_back_entire_batch(database_case):
    dsn, source_id = database_case
    loader = PostgresLoader(dsn)
    original = make_record(source_id, "record-001")

    loader.load([original])

    updated = replace(
        original,
        attributes={"name": "Should be rolled back"},
    )
    new_record = make_record(source_id, "record-002")
    invalid_record = make_record(source_id, "")

    with pytest.raises(CheckViolation):
        loader.load([updated, new_record, invalid_record])

    assert read_rows(dsn, source_id) == [
        ("record-001", {"name": "Original site"})
    ]


def read_spatial_rows(dsn, source_id):
    with psycopg.connect(dsn, connect_timeout=5) as connection:
        return connection.execute(
            """
            SELECT
                country_code,
                source_record_id,
                ST_SRID(geom),
                ST_X(geom),
                ST_Y(geom),
                attributes
            FROM staging.records
            WHERE country_code IN ('DE', 'AT')
              AND source_id = %s
            ORDER BY country_code, source_record_id
            """,
            (source_id,),
        ).fetchall()


def test_spatial_adapter_preserves_srid_and_country_isolation(database_case):
    dsn, source_id = database_case
    loader = PostgresLoader(dsn)

    adapter = CsvPointAdapter(
        Path(__file__).resolve().parents[1] / "fixtures" / "points.csv",
        source_id=source_id,
        source_date=date(2026, 9, 1),
    )

    count = run_pipeline(
        adapter,
        load=loader.load,
        fetched_at=datetime(2026, 9, 29, tzinfo=UTC),
    )

    assert count == 2

    expected = [
        (
            "AT", "point-001", 4326, 16.37, 48.21,
            {"name": "Synthetic location AT"},
        ),
        (
            "DE", "point-001", 4326, 7.46, 51.51,
            {"name": "Synthetic location DE"},
        ),
    ]
    assert read_spatial_rows(dsn, source_id) == expected

    updated_german_record = replace(
        make_record(source_id, "point-001"),
        attributes={"name": "Updated German location"},
        geom={"type": "Point", "coordinates": [7.47, 51.52]},
    )
    loader.load([updated_german_record])

    assert read_spatial_rows(dsn, source_id) == [
        expected[0],
        (
            "DE", "point-001", 4326, 7.47, 51.52,
            {"name": "Updated German location"},
        ),
    ]