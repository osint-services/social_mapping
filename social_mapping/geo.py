from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any


def validate_coordinates(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_miles = 3958.7613
    lat1_r, lon1_r, lat2_r, lon2_r = map(radians, (lat1, lon1, lat2, lon2))
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    value = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    return 2 * earth_radius_miles * asin(sqrt(value))


def centroid_from_bbox(bbox: list[float] | tuple[float, ...]) -> tuple[float, float]:
    if len(bbox) != 4:
        raise ValueError("place bounding box must contain four coordinates")
    west, south, east, north = (float(value) for value in bbox)
    return ((south + north) / 2, (west + east) / 2)


def feature(
    *,
    feature_id: str,
    latitude: float,
    longitude: float,
    properties: dict[str, Any],
) -> dict[str, Any]:
    validate_coordinates(latitude, longitude)
    return {
        "type": "Feature",
        "id": feature_id,
        "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
        "properties": properties,
    }
