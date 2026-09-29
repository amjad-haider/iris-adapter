from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from iris_adapter.adapters.fixture import FixtureAdapter
from iris_adapter.validation import validate_country_code


FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "sites.json"
)
FETCHED_AT = datetime(2026, 9, 29, tzinfo=UTC)


@pytest.fixture
def adapter():
    return FixtureAdapter(
        FIXTURE_PATH,
        source_id="fixture-sites",
        source_date=date(2026, 9, 1),
    )


def test_fixture_records_are_normalized(adapter):
    records = [
        adapter.normalize(raw, fetched_at=FETCHED_AT)
        for raw in adapter.extract()
    ]

    assert len(records) == 20

    first = records[0]
    assert first.source_record_id == "site-001"
    assert first.region_code == "NW"
    assert first.attributes == {"name": "Synthetic site 01"}

    for record in records:
        assert record.country_code == "DE"
        assert record.source_id == "fixture-sites"
        assert record.source_date == date(2026, 9, 1)
        assert record.fetched_at == FETCHED_AT
        assert record.geom is None
        validate_country_code(record.country_code)


def test_missing_country_is_rejected(adapter):
    raw = {
        "id": "invalid-001",
        "region": "NW",
        "name": "Record without a country",
    }

    record = adapter.normalize(raw, fetched_at=FETCHED_AT)

    with pytest.raises(ValueError, match="country_code"):
        validate_country_code(record.country_code)