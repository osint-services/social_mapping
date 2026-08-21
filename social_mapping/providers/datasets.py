from __future__ import annotations

from typing import Any

import httpx


class DatasetProvider:
    name = "datasets"

    def __init__(self, base_url: str, timeout: float = 15) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def search(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_miles: float,
        query: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "latitude": latitude,
            "longitude": longitude,
            "radius_miles": radius_miles,
            "limit": limit,
        }
        if query:
            params["query"] = query
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/datasets/search/geo", params=params)
            response.raise_for_status()
            payload = response.json()
        if payload.get("type") != "FeatureCollection":
            raise ValueError("dataset service returned an invalid GeoJSON response")
        return payload.get("features", [])
