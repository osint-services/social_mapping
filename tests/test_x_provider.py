from social_mapping.providers.x import normalize_x_response


def test_normalizes_exact_and_place_coordinates_and_excludes_unlocated_posts():
    response = {
        "data": [
            {"id": "1", "author_id": "u1", "text": "exact", "geo": {"coordinates": {"type": "Point", "coordinates": [-0.12, 51.5]}}, "created_at": "2026-01-01T00:00:00Z"},
            {"id": "2", "author_id": "u1", "text": "place", "geo": {"place_id": "p1"}},
            {"id": "3", "author_id": "u1", "text": "profile location is not evidence"},
        ],
        "includes": {
            "users": [{"id": "u1", "username": "investigator"}],
            "places": [{"id": "p1", "geo": {"bbox": [-0.2, 51.4, 0.0, 51.6]}}],
        },
    }
    features = normalize_x_response(response, origin_latitude=51.5, origin_longitude=-0.1, radius_miles=20)
    assert [item["id"] for item in features] == ["x:1", "x:2"]
    assert features[0]["properties"]["location_accuracy"] == "exact"
    assert features[0]["geometry"]["coordinates"] == [-0.12, 51.5]
    assert features[1]["properties"]["location_accuracy"] == "place"
    assert features[1]["geometry"]["coordinates"] == [-0.1, 51.5]


def test_filters_results_outside_radius():
    response = {"data": [{"id": "1", "geo": {"coordinates": {"coordinates": [-122.67, 45.52]}}}]}
    assert normalize_x_response(response, origin_latitude=51.5, origin_longitude=-0.1, radius_miles=10) == []
