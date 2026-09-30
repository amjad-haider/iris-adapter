import json
from datetime import UTC, date, datetime
from pathlib import Path

from iris_adapter.adapters.csv_points import CsvPointAdapter
from iris_adapter.pipeline import run_pipeline
from iris_adapter.serialization import write_jsonl


def test_pipeline_exports_normalized_records_as_jsonl(tmp_path):
    adapter = CsvPointAdapter(
        Path(__file__).resolve().parents[1] / "fixtures" / "points.csv",
        source_id="fixture-points",
        source_date=date(2026, 9, 1),
    )
    output = tmp_path / "normalized.jsonl"

    count = run_pipeline(
        adapter,
        load=lambda records: write_jsonl(records, output),
        fetched_at=datetime(2026, 9, 29, tzinfo=UTC),
    )

    lines = output.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines]

    assert count == len(rows) == 2
    assert rows[0] == {
        "country_code": "DE",
        "region_code": "NW",
        "source_id": "fixture-points",
        "source_record_id": "point-001",
        "source_date": "2026-09-01",
        "fetched_at": "2026-09-29T00:00:00+00:00",
        "attributes": {"name": "Synthetic location DE"},
        "geom": {
            "type": "Point",
            "coordinates": [7.46, 51.51],
        },
    }
    assert rows[1]["country_code"] == "AT"