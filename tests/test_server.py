from fastapi.testclient import TestClient

from social_mapping import server


class FakeGeocoder:
    async def resolve(self, query):
        if query == "Missing":
            raise server.PlaceNotFoundError("place not found: Missing")
        return {"latitude": 51.5, "longitude": -0.1, "label": "London", "provider": "nominatim", "cached": True}


class Provider:
    def __init__(self, result=None, error=None):
        self.result = result or []
        self.error = error

    async def search(self, **_kwargs):
        if self.error:
            raise self.error
        return self.result


client = TestClient(server.app)


def setup_function():
    server.get_geocoder = lambda: FakeGeocoder()


def test_rejects_conflicting_and_unpaired_locations():
    assert client.get("/map/search", params={"place": "London", "latitude": 1, "longitude": 2}).status_code == 422
    assert client.get("/map/search", params={"latitude": 1}).status_code == 422
    assert client.get("/map/search").status_code == 422


def test_returns_404_for_unresolved_place():
    response = client.get("/map/search", params={"place": "Missing", "sources": "datasets"})
    assert response.status_code == 404


def test_geojson_partial_provider_response(monkeypatch):
    mapped = {
        "type": "Feature",
        "id": "dataset:1",
        "geometry": {"type": "Point", "coordinates": [-0.1, 51.5]},
        "properties": {"source": "datasets", "distance_miles": 0},
    }
    monkeypatch.setattr(server, "get_providers", lambda: {"datasets": Provider([mapped]), "x": Provider(error=RuntimeError("X provider is not configured"))})
    response = client.get("/map/search", params={"place": "London", "sources": "datasets,x"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["id"] == "dataset:1"
    assert payload["providers"]["datasets"]["status"] == "ok"
    assert payload["providers"]["x"]["status"] == "unavailable"


def test_all_provider_failures_return_503(monkeypatch):
    monkeypatch.setattr(server, "get_providers", lambda: {"datasets": Provider(error=RuntimeError("offline")), "x": Provider(error=RuntimeError("offline"))})
    response = client.get("/map/search", params={"place": "London", "sources": "datasets,x"})
    assert response.status_code == 503


def test_legacy_route_is_deprecated(monkeypatch):
    monkeypatch.setattr(server, "get_providers", lambda: {"datasets": Provider(), "x": Provider()})
    response = client.get("/search/tweets", params={"city": "London", "distance": 5})
    assert response.status_code == 200
    assert response.headers["deprecation"] == "true"
    assert response.json()["metadata"]["sources"] == ["x"]


def test_health_and_readiness(tmp_path, monkeypatch):
    class ReadyGeocoder:
        def _prepare_cache(self):
            return None

    monkeypatch.setattr(server, "get_geocoder", lambda: ReadyGeocoder())
    assert client.get("/map/healthz").status_code == 200
    assert client.get("/map/readyz").status_code == 200
