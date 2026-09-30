import json
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

from iris_adapter.adapters.fixture import FixtureAdapter
from iris_adapter.pipeline import run_pipeline


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "sites.json"
)


def make_adapter(path):
    return FixtureAdapter(
        path,
        source_id="fixture-sites",
        source_date=date(2026, 9, 1),
    )


def test_pipeline_loads_complete_batch_in_utc():
    loader = Mock()
    fetched_at = datetime(
        2026, 9, 29, 2,
        tzinfo=timezone(timedelta(hours=2)),
    )

    count = run_pipeline(
        make_adapter(FIXTURE_PATH),
        load=loader,
        fetched_at=fetched_at,
    )

    loader.assert_called_once()
    records = loader.call_args.args[0]

    assert count == 20
    assert len(records) == 20
    assert all(record.geom is None for record in records)
    assert all(
        record.fetched_at == datetime(2026, 9, 29, tzinfo=UTC)
        and record.fetched_at.tzinfo is UTC
        for record in records
    )


def test_invalid_record_prevents_loading_entire_batch(tmp_path):
    rows = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    rows[1]["country"] = "ZZ"

    path = tmp_path / "invalid_sites.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    loader = Mock()

    with pytest.raises(ValueError, match="country_code"):
        run_pipeline(
            make_adapter(path),
            load=loader,
            fetched_at=datetime(2026, 9, 29, tzinfo=UTC),
        )

    loader.assert_not_called()


def test_pipeline_rejects_naive_timestamp():
    loader = Mock()

    with pytest.raises(ValueError, match="fetched_at"):
        run_pipeline(
            make_adapter(FIXTURE_PATH),
            load=loader,
            fetched_at=datetime(2026, 9, 29),
        )

    loader.assert_not_called()