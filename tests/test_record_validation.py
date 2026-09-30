from datetime import UTC, date, datetime

import pytest

from iris_adapter.models import CanonicalRecord
from iris_adapter.validation import validate_record


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
    setattr(record, field, value)

    with pytest.raises(ValueError, match=field):
        validate_record(record)


def test_record_validation_rejects_invalid_country(record):
    record.country_code = "ZZ"

    with pytest.raises(ValueError, match="country_code"):
        validate_record(record)