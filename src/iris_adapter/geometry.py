import json

from shapely import from_geojson, to_geojson
from shapely.errors import GEOSException


_COORDINATE_DEPTH = {
    "Point": 0,
    "MultiPoint": 1,
    "LineString": 1,
    "MultiLineString": 2,
    "Polygon": 2,
    "MultiPolygon": 3,
}


def _validate_coordinates(coordinates: object, depth: int) -> None:
    """Check coordinate nesting and two-dimensional lon/lat values."""
    if not isinstance(coordinates, (list, tuple)) or not coordinates:
        raise ValueError("geom coordinates must be non-empty arrays")

    if depth > 0:
        for part in coordinates:
            _validate_coordinates(part, depth - 1)
        return

    if len(coordinates) != 2 or any(
        type(value) not in (int, float) for value in coordinates
    ):
        raise ValueError("geom positions must contain exactly two numbers")

    longitude, latitude = coordinates

    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise ValueError("geom coordinates must be finite and within lon/lat bounds")


def normalize_geometry(
    geom: object,
    *,
    source_crs: str | None,
) -> dict[str, object] | None:
    """Return valid 2D GeoJSON geometry in WGS84 lon/lat order."""
    if geom is None:
        return None

    if source_crs != "EPSG:4326":
        raise ValueError("source_crs must explicitly be EPSG:4326")

    if not isinstance(geom, dict):
        raise ValueError("geom must be a GeoJSON geometry dictionary")

    geometry_type = geom.get("type")

    if (
        not isinstance(geometry_type, str)
        or geometry_type not in _COORDINATE_DEPTH
    ):
        raise ValueError("geom has an unsupported geometry type")

    if "crs" in geom:
        raise ValueError("geom must declare its CRS through source_crs")

    _validate_coordinates(
        geom.get("coordinates"),
        _COORDINATE_DEPTH[geometry_type],
    )

    try:
        geometry = from_geojson(json.dumps(geom, allow_nan=False))
    except (GEOSException, TypeError, ValueError) as exc:
        raise ValueError("geom is malformed") from exc

    if geometry.is_empty or not geometry.is_valid:
        raise ValueError("geom must be non-empty and geometrically valid")

    return json.loads(to_geojson(geometry))