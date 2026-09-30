from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from iris_adapter.adapters.csv_points import CsvPointAdapter
from iris_adapter.pipeline import run_pipeline


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "points.csv"
)
FETCHED_AT = datetime(2026, 9, 29, tzinfo=UTC)


def make_adapter(path):
    return CsvPointAdapter(
        path,
        source_id="fixture-points",
        source_date=date(2026, 9, 1),
    )


def test_csv_adapter_uses_shared_pipeline():
    loader = Mock()

    count = run_pipeline(
        make_adapter(FIXTURE_PATH),
        load=loader,
        fetched_at=FETCHED_AT,
    )

    loader.assert_called_once()
    records = loader.call_args.args[0]

    assert count == 2
    assert [
        (record.country_code, record.source_record_id, record.region_code)
        for record in records
    ] == [
        ("DE", "point-001", "NW"),
        ("AT", "point-001", "9"),
    ]

    assert [record.geom for record in records] == [
        {"type": "Point", "coordinates": [7.46, 51.51]},
        {"type": "Point", "coordinates": [16.37, 48.21]},
    ]

    assert records[0].attributes == {"name": "Synthetic location DE"}
    assert all(
        record.source_id == "fixture-points"
        and record.source_date == date(2026, 9, 1)
        and record.fetched_at == FETCHED_AT
        for record in records
    )


def test_invalid_csv_coordinates_prevent_loading(tmp_path):
    path = tmp_path / "invalid_points.csv"
    path.write_text(
        "location_id,iso_country,admin_region,label,longitude,latitude\n"
        "point-001,DE,NW,Invalid location,181,51.51\n",
        encoding="utf-8",
    )
    loader = Mock()

    with pytest.raises(ValueError, match="geom"):
        run_pipeline(
            make_adapter(path),
            load=loader,
            fetched_at=FETCHED_AT,
        )

    loader.assert_not_called()