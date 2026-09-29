import pytest

from iris_adapter.validation import validate_country_code


@pytest.mark.parametrize("country_code", ["DE", "AT", "FR"])
def test_accepts_valid_country_codes(country_code):
    validate_country_code(country_code)


@pytest.mark.parametrize(
    "country_code",
    [None, "", " ", "ZZ", "D", "DEU", "de", " DE ", 123],
)
def test_rejects_invalid_country_codes(country_code):
    with pytest.raises(ValueError, match="country_code"):
        validate_country_code(country_code)