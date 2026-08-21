from datetime import datetime, timedelta, timezone
import json
import sqlite3

import httpx
import pytest

from social_mapping.geocoder import NominatimGeocoder, PlaceNotFoundError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeClient:
    calls = []
    payload = [{"lat": "51.5072", "lon": "-0.1276", "display_name": "London, United Kingdom"}]

    def __init__(self, **_kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(self.payload)


@pytest.mark.asyncio
async def test_normalized_durable_cache_avoids_second_request(tmp_path, monkeypatch):
    FakeClient.calls = []
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    geocoder = NominatimGeocoder(
        base_url="https://geo.example",
        user_agent="test-agent",
        cache_path=str(tmp_path / "cache.db"),
        min_interval_seconds=0,
    )
    first = await geocoder.resolve("  LONDON  ")
    second = await geocoder.resolve("london")
    assert first["cached"] is False
    assert second["cached"] is True
    assert len(FakeClient.calls) == 1
    assert FakeClient.calls[0][1]["headers"]["User-Agent"] == "test-agent"


@pytest.mark.asyncio
async def test_stale_cache_is_refreshed(tmp_path, monkeypatch):
    FakeClient.calls = []
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    cache_path = tmp_path / "cache.db"
    geocoder = NominatimGeocoder(base_url="https://geo.example", user_agent="test", cache_path=str(cache_path), min_interval_seconds=0)
    stale = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
    with sqlite3.connect(cache_path) as connection:
        connection.execute("INSERT INTO geocoder_cache VALUES (?, ?, ?)", ("london", json.dumps({"latitude": 0}), stale))
    resolved = await geocoder.resolve("London")
    assert resolved["latitude"] == 51.5072
    assert len(FakeClient.calls) == 1


@pytest.mark.asyncio
async def test_place_not_found(tmp_path, monkeypatch):
    FakeClient.payload = []
    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
    geocoder = NominatimGeocoder(base_url="https://geo.example", user_agent="test", cache_path=str(tmp_path / "cache.db"), min_interval_seconds=0)
    with pytest.raises(PlaceNotFoundError):
        await geocoder.resolve("Missing")
    FakeClient.payload = [{"lat": "51.5072", "lon": "-0.1276", "display_name": "London"}]
