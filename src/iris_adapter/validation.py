import pycountry


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