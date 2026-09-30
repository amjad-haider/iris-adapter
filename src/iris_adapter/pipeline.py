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

    for position, raw_record in enumerate(adapter.extract(), start=1):
        label = f"record {position}"

        try:
            record = adapter.normalize(raw_record, fetched_at=timestamp)
            label = f"record {position} ({record.source_record_id!r})"
            validate_record(record)

            record = replace(
                record,
                fetched_at=record.fetched_at.astimezone(UTC),
                geom=normalize_geometry(
                    record.geom,
                    source_crs=adapter.source_crs,
                ),
            )
        except KeyError as exc:
            raise ValueError(f"{label}: missing field {exc}") from exc
        except ValueError as exc:
            raise ValueError(f"{label}: {exc}") from exc

        records.append(record)


    load(records)
    return len(records)