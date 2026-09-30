import pytest

from iris_adapter.geometry import normalize_geometry


@pytest.mark.parametrize(
    "geom",
    [
        {"type": "Point", "coordinates": [8.4, 49.4]},
        {
            "type": "Polygon",
            "coordinates": [
                [[8, 49], [9, 49], [9, 50], [8, 49]]
            ],
        },
    ],
)
def test_accepts_valid_geometry(geom):
    result = normalize_geometry(geom, source_crs="EPSG:4326")
    assert result == geom


def test_preserves_missing_geometry():
    assert normalize_geometry(None, source_crs=None) is None


@pytest.mark.parametrize("source_crs", [None, "EPSG:3857"])
def test_rejects_unknown_or_unsupported_crs(source_crs):
    geom = {"type": "Point", "coordinates": [8.4, 49.4]}

    with pytest.raises(ValueError, match="source_crs"):
        normalize_geometry(geom, source_crs=source_crs)


@pytest.mark.parametrize(
    "geom",
    [
        {},
        {"type": "Point", "coordinates": []},
        {"type": "Point", "coordinates": [181, 49]},
        {"type": "Point", "coordinates": [8, 91]},
        {"type": "Point", "coordinates": [8, 49, 100]},
        {"type": "Point", "coordinates": ["8", 49]},
        {"type": "Point", "coordinates": [True, 49]},
        {"type": "Point", "coordinates": [float("nan"), 49]},
        {"type": "Point", "coordinates": [float("inf"), 49]},
        {
            "type": "Polygon",
            "coordinates": [
                [[8, 49], [9, 50], [9, 49], [8, 50], [8, 49]]
            ],
        },
    ],
)
def test_rejects_invalid_geometry(geom):
    with pytest.raises(ValueError, match="geom"):
        normalize_geometry(geom, source_crs="EPSG:4326")