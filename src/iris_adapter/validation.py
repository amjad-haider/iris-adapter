import pycountry
from iris_adapter.models import CanonicalRecord
from datetime import date, datetime


def validate_country_code(country_code: object) -> None:
    """Reject missing or invalid uppercase ISO country codes."""

    if not isinstance(country_code, str):
        raise ValueError("country_code must be a string")

    if (
        len(country_code) != 2
        or country_code != country_code.upper()
        or pycountry.countries.get(alpha_2=country_code) is None
    ):
        raise ValueError(f"Invalid country_code: {country_code!r}")

def validate_record(record: CanonicalRecord) -> None:
    """Validate country, identifiers, and dates."""
    validate_country_code(record.country_code)

    for field in ("source_id", "source_record_id"):
        value = getattr(record, field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")

    if (
        not isinstance(record.source_date, date)
        or isinstance(record.source_date, datetime)
    ):
        raise ValueError("source_date must be a date without a time")

    if not isinstance(record.fetched_at, datetime):
        raise ValueError("fetched_at must be a datetime")

    if record.fetched_at.utcoffset() is None:
        raise ValueError("fetched_at must include timezone information")