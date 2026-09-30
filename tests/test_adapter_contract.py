
from collections.abc import Iterable
from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import Mock

import pytest

from iris_adapter.adapters.base import SourceAdapter
from iris_adapter.models import CanonicalRecord
from iris_adapter.pipeline import run_pipeline


FETCHED_AT = datetime(2026, 9, 29, tzinfo=UTC)


class InMemoryParcelAdapter(SourceAdapter):
    """A second source with its own field names and polygon geometry."""

    source_crs = "EPSG:4326"

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def extract(self) -> Iterable[dict[str, Any]]:
        yield from self.rows

    def normalize(
        self,
        raw_record: dict[str, Any],
        *,
        fetched_at: datetime,
    ) -> CanonicalRecord:
        return CanonicalRecord(
            country_code=raw_record["land"],
            region_code=raw_record["bundesland"],
            source_id="parcels-test",
            source_record_id=raw_record["parcel_no"],
            source_date=date(2026, 8, 15),
            fetched_at=fetched_at,
            attributes={"area_m2": raw_record["area_m2"]},
            geom=raw_record["shape"],
        )


PARCEL = {
    "parcel_no": "parcel-001",
    "land": "DE",
    "bundesland": "NW",
    "area_m2": 1200,
    "shape": {
        "type": "Polygon",
        "coordinates": [[[8, 49], [9, 49], [9, 50], [8, 49]]],
    },
}


def test_second_adapter_runs_through_shared_pipeline():
    loader = Mock()

    count = run_pipeline(
        InMemoryParcelAdapter([PARCEL]),
        load=loader,
        fetched_at=FETCHED_AT,
    )

    assert count == 1
    [record] = loader.call_args.args[0]
    assert record.country_code == "DE"
    assert record.source_record_id == "parcel-001"
    assert record.attributes == {"area_m2": 1200}
    assert record.geom == PARCEL["shape"]


def test_second_adapter_gets_shared_country_validation():
    loader = Mock()
    invalid = {**PARCEL, "land": "XX"}

    with pytest.raises(ValueError, match="country_code"):
        run_pipeline(
            InMemoryParcelAdapter([invalid]),
            load=loader,
            fetched_at=FETCHED_AT,
        )

    loader.assert_not_called()


def test_adapter_missing_normalize_cannot_be_instantiated():
    class IncompleteAdapter(SourceAdapter):
        def extract(self) -> Iterable[dict[str, Any]]:
            return []

    with pytest.raises(TypeError, match="normalize"):
        IncompleteAdapter()