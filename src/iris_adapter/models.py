from dataclasses import dataclass
from datetime import date, datetime

@dataclass
class CanonicalRecord:
    """Record structure produced by source adapters."""

    country_code: str
    region_code: str | None
    source_id: str
    source_record_id: str       # help to identify database records using combination of country, source and record ID
    source_date: date
    fetched_at: datetime        # to get the timestamp when the data was fetched
    attributes: dict[str, object]
    geom:  dict[str,object] | None