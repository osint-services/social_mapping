import asyncio

import httpx
import pytest

from social_mapping.providers.x import XProvider, normalize_x_response


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


def test_recent_search_uses_bearer_token_and_requested_fields(monkeypatch):
    def provider(request):
        assert request.url.host == "api.x.com"
        assert request.url.path == "/2/tweets/search/recent"
        assert request.headers["Authorization"] == "Bearer fixture-token"
        assert request.url.params["query"] == "fixture has:geo -is:retweet"
        assert request.url.params["max_results"] == "10"
        assert request.url.params["expansions"] == "geo.place_id,author_id"
        assert "geo" in request.url.params["tweet.fields"].split(",")
        return httpx.Response(200, json={"data": [
            {"id": "1", "geo": {"coordinates": {"coordinates": [-0.12, 51.5]}}},
            {"id": "2", "text": "no coordinates"},
        ]})

    client_class = httpx.AsyncClient

    def make_client(**kwargs):
        assert kwargs["timeout"] == 9
        return client_class(transport=httpx.MockTransport(provider), **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", make_client)
    rows = asyncio.run(XProvider("fixture-token", timeout=9).search(
        latitude=51.5, longitude=-0.1, radius_miles=5, query=" fixture ", limit=1,
    ))
    assert [row["id"] for row in rows] == ["x:1"]


def test_recent_search_reports_rate_limit_without_exposing_provider_body(monkeypatch):
    transport = httpx.MockTransport(lambda _: httpx.Response(429, text="raw provider details"))
    client_class = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client_class(transport=transport, **kwargs))
    with pytest.raises(RuntimeError, match=r"^X recent search returned HTTP 429\.$"):
        asyncio.run(XProvider("fixture-token").search(
            latitude=51.5, longitude=-0.1, radius_miles=5, query=None, limit=10,
        ))
