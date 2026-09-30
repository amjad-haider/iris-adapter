import pycountry
from iris_adapter.models import CanonicalRecord


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
    """Validate country and record identifiers."""
    validate_country_code(record.country_code)

    for field in ("source_id", "source_record_id"):
        value = getattr(record, field)

        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")