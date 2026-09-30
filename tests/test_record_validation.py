from datetime import UTC, date, datetime

import pytest

from iris_adapter.models import CanonicalRecord
from iris_adapter.validation import validate_record
from dataclasses import replace


@pytest.fixture
def record():
    return CanonicalRecord(
        country_code="DE",
        region_code="NW",
        source_id="fixture-sites",
        source_record_id="site-001",
        source_date=date(2026, 9, 1),
        fetched_at=datetime(2026, 9, 29, tzinfo=UTC),
        attributes={"name": "Synthetic site 01"},
        geom=None,
    )


def test_accepts_valid_record_identity(record):
    validate_record(record)


@pytest.mark.parametrize("field", ["source_id", "source_record_id"])
@pytest.mark.parametrize("value", [None, "", " ", 123])
def test_rejects_invalid_identifiers(record, field, value):
    record = replace(record, **{field: value})

    with pytest.raises(ValueError, match=field):
        validate_record(record)


def test_record_validation_rejects_invalid_country(record):
    record = replace(record, country_code="ZZ")

    with pytest.raises(ValueError, match="country_code"):
        validate_record(record)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "2026-09-01",
        123,
        datetime(2026, 9, 1, tzinfo=UTC),
    ],
)
def test_rejects_invalid_source_date(record, value):
    record = replace(record, source_date=value)

    with pytest.raises(ValueError, match="source_date"):
        validate_record(record)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "2026-09-29T00:00:00Z",
        date(2026, 9, 29),
        datetime(2026, 9, 29),
    ],
)
def test_rejects_invalid_fetched_at(record, value):
    record = replace(record, fetched_at=value)

    with pytest.raises(ValueError, match="fetched_at"):
        validate_record(record)


def test_accepts_unknown_region(record):
    record = replace(record, region_code=None)
    validate_record(record)


@pytest.mark.parametrize("value", ["", " ", 123])
def test_rejects_invalid_region(record, value):
    record = replace(record, region_code=value)

    with pytest.raises(ValueError, match="region_code"):
        validate_record(record)


def test_accepts_empty_attributes(record):
    record = replace(record, attributes={})
    validate_record(record)


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        {"observed_on": date(2026, 9, 1)},
        {"score": float("nan")},
        {"score": float("inf")},
    ],
)
def test_rejects_invalid_attributes(record, value):
    record = replace(record, attributes=value)

    with pytest.raises(ValueError, match="attributes"):
        validate_record(record)