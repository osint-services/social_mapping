from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sqlite3
import time
from typing import Any
import unicodedata

import httpx


class PlaceNotFoundError(LookupError):
    pass


class NominatimGeocoder:
    _rate_lock = asyncio.Lock()
    _last_request_at = 0.0

    def __init__(
        self,
        *,
        base_url: str,
        user_agent: str,
        cache_path: str,
        refresh_days: int = 30,
        min_interval_seconds: float = 1,
        timeout: float = 15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.cache_path = cache_path
        self.refresh_days = refresh_days
        self.min_interval_seconds = min_interval_seconds
        self.timeout = timeout
        self._prepare_cache()

    @staticmethod
    def normalize_query(query: str) -> str:
        normalized = unicodedata.normalize("NFKC", query).strip().casefold()
        return " ".join(normalized.split())

    def _prepare_cache(self) -> None:
        path = Path(self.cache_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS geocoder_cache (
                    query TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    refreshed_at TEXT NOT NULL
                )"""
            )

    def _cached(self, normalized_query: str) -> dict[str, Any] | None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.refresh_days)
        with sqlite3.connect(self.cache_path) as connection:
            row = connection.execute(
                "SELECT payload, refreshed_at FROM geocoder_cache WHERE query = ?", (normalized_query,)
            ).fetchone()
        if not row or datetime.fromisoformat(row[1]) < cutoff:
            return None
        return json.loads(row[0])

    def _store(self, normalized_query: str, payload: dict[str, Any]) -> None:
        refreshed_at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.cache_path) as connection:
            connection.execute(
                """INSERT INTO geocoder_cache(query, payload, refreshed_at) VALUES (?, ?, ?)
                ON CONFLICT(query) DO UPDATE SET payload=excluded.payload, refreshed_at=excluded.refreshed_at""",
                (normalized_query, json.dumps(payload), refreshed_at),
            )

    async def resolve(self, query: str) -> dict[str, Any]:
        normalized = self.normalize_query(query)
        if not normalized:
            raise PlaceNotFoundError("place cannot be empty")
        cached = self._cached(normalized)
        if cached:
            return {**cached, "cached": True}

        async with self._rate_lock:
            elapsed = time.monotonic() - self.__class__._last_request_at
            if elapsed < self.min_interval_seconds:
                await asyncio.sleep(self.min_interval_seconds - elapsed)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={"q": query, "format": "jsonv2", "limit": 1},
                    headers={"User-Agent": self.user_agent},
                )
                self.__class__._last_request_at = time.monotonic()
                response.raise_for_status()
                rows = response.json()
        if not rows:
            raise PlaceNotFoundError(f"place not found: {query}")
        first = rows[0]
        payload = {
            "latitude": float(first["lat"]),
            "longitude": float(first["lon"]),
            "label": first.get("display_name", query),
            "provider": "nominatim",
            "cached": False,
        }
        self._store(normalized, payload)
        return payload
