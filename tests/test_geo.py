import pytest

from social_mapping.geo import centroid_from_bbox, haversine_miles, validate_coordinates


def test_coordinate_validation():
    validate_coordinates(51.5, -0.12)
    with pytest.raises(ValueError, match="latitude"):
        validate_coordinates(91, 0)
    with pytest.raises(ValueError, match="longitude"):
        validate_coordinates(0, -181)


def test_distance_and_place_centroid():
    latitude, longitude = centroid_from_bbox([-0.2, 51.4, 0.0, 51.6])
    assert latitude == pytest.approx(51.5)
    assert longitude == pytest.approx(-0.1)
    assert haversine_miles(51.5, -0.1, latitude, longitude) == pytest.approx(0)
