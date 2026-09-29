import json
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from iris_adapter.adapters.base import SourceAdapter
from iris_adapter.models import CanonicalRecord


class FixtureAdapter(SourceAdapter):
    """Read the non-spatial synthetic JSON fixture."""

    def __init__(
        self,
        path: Path,
        *,
        source_id: str,
        source_date: date,
    ) -> None:
        self.path = path
        self.source_id = source_id
        self.source_date = source_date

    def extract(self) -> Iterable[dict[str, Any]]:
        with self.path.open(encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list):
            raise ValueError("Fixture must contain a JSON array")

        for position, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                raise ValueError(
                    f"Fixture record {position} must be a JSON object"
                )
            yield record

    def normalize(
        self,
        raw_record: dict[str, Any],
        *,
        fetched_at: datetime,
    ) -> CanonicalRecord:
        return CanonicalRecord(
            country_code=raw_record.get("country"),
            region_code=raw_record.get("region"),
            source_id=self.source_id,
            source_record_id=raw_record["id"],
            source_date=self.source_date,
            fetched_at=fetched_at,
            attributes={"name": raw_record["name"]},
            geom=None,
        )