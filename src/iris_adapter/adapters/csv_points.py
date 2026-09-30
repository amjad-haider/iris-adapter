import csv
from collections.abc import Iterable
from datetime import date, datetime
from pathlib import Path
from typing import Any

from iris_adapter.adapters.base import SourceAdapter
from iris_adapter.models import CanonicalRecord


class CsvPointAdapter(SourceAdapter):
    """Read CSV locations declared as WGS84 longitude/latitude."""

    source_crs = "EPSG:4326"

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
        with self.path.open(encoding="utf-8", newline="") as file:
            yield from csv.DictReader(file)

    def normalize(
        self,
        raw_record: dict[str, Any],
        *,
        fetched_at: datetime,
    ) -> CanonicalRecord:
        try:
            longitude = float(raw_record["longitude"])
            latitude = float(raw_record["latitude"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "longitude and latitude must be supplied as numbers"
            ) from exc

        return CanonicalRecord(
            country_code=raw_record.get("iso_country"),
            region_code=raw_record.get("admin_region") or None,
            source_id=self.source_id,
            source_record_id=raw_record["location_id"],
            source_date=self.source_date,
            fetched_at=fetched_at,
            attributes={"name": raw_record["label"]},
            geom={
                "type": "Point",
                "coordinates": [longitude, latitude],
            },
        )