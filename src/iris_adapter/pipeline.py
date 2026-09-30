from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime

from iris_adapter.adapters.base import SourceAdapter
from iris_adapter.geometry import normalize_geometry
from iris_adapter.models import CanonicalRecord
from iris_adapter.validation import validate_record


def run_pipeline(
    adapter: SourceAdapter,
    *,
    load: Callable[[list[CanonicalRecord]], None],
    fetched_at: datetime | None = None,
) -> int:
    """Prepare and validate the entire batch before calling the loader."""
    timestamp = datetime.now(UTC) if fetched_at is None else fetched_at

    if (
        not isinstance(timestamp, datetime)
        or timestamp.utcoffset() is None
    ):
        raise ValueError("fetched_at must be a timezone-aware datetime")

    timestamp = timestamp.astimezone(UTC)
    records: list[CanonicalRecord] = []

    for raw_record in adapter.extract():
        record = adapter.normalize(raw_record, fetched_at=timestamp)
        validate_record(record)

        record = replace(
            record,
            fetched_at=record.fetched_at.astimezone(UTC),
            geom=normalize_geometry(
                record.geom,
                source_crs=adapter.source_crs,
            ),
        )
        records.append(record)

    load(records)
    return len(records)