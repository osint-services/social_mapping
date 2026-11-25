from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from social_mapping.config import settings
from social_mapping.geocoder import NominatimGeocoder, PlaceNotFoundError
from social_mapping.geo import feature, validate_coordinates
from social_mapping.providers import DatasetProvider, XProvider


app = FastAPI(
    title="Social Mapping API",
    version="1.0.1",
    description="GeoJSON search across imported OSINT datasets and provider-supplied X locations.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_geocoder() -> NominatimGeocoder:
    return NominatimGeocoder(
        base_url=settings.nominatim_base_url,
        user_agent=settings.nominatim_user_agent,
        cache_path=settings.geocoder_cache_path,
        refresh_days=settings.geocoder_cache_days,
        min_interval_seconds=settings.geocoder_min_interval_seconds,
        timeout=settings.provider_timeout_seconds,
    )


def get_providers() -> dict[str, Any]:
    return {
        "datasets": DatasetProvider(settings.dataset_service_url, settings.provider_timeout_seconds),
        "x": XProvider(settings.x_bearer_token, settings.provider_timeout_seconds),
    }


def parse_sources(value: str) -> list[str]:
    selected = list(dict.fromkeys(part.strip().lower() for part in value.split(",") if part.strip()))
    if not selected:
        raise HTTPException(status_code=422, detail="at least one source is required")
    invalid = set(selected) - {"x", "datasets"}
    if invalid:
        raise HTTPException(status_code=422, detail=f"unsupported sources: {', '.join(sorted(invalid))}")
    return selected


async def run_search(
    *,
    place: str | None,
    latitude: float | None,
    longitude: float | None,
    radius_miles: float,
    query: str | None,
    sources: str,
    limit: int,
) -> dict[str, Any]:
    has_place = bool(place and place.strip())
    has_latitude = latitude is not None
    has_longitude = longitude is not None
    if has_place and (has_latitude or has_longitude):
        raise HTTPException(status_code=422, detail="use place or a latitude/longitude pair, not both")
    if has_latitude != has_longitude:
        raise HTTPException(status_code=422, detail="latitude and longitude must be provided together")
    if not has_place and not (has_latitude and has_longitude):
        raise HTTPException(status_code=422, detail="provide place or a latitude/longitude pair")

    selected = parse_sources(sources)

    if has_place:
        try:
            resolved = await get_geocoder().resolve(place or "")
        except PlaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"place resolver failed: {exc}") from exc
        origin_latitude = resolved["latitude"]
        origin_longitude = resolved["longitude"]
        origin_label = resolved["label"]
        origin_source = resolved["provider"]
        origin_cached = resolved["cached"]
    else:
        origin_latitude = float(latitude)
        origin_longitude = float(longitude)
        try:
            validate_coordinates(origin_latitude, origin_longitude)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        origin_label = f"{origin_latitude:.5f}, {origin_longitude:.5f}"
        origin_source = "coordinates"
        origin_cached = False

    providers = get_providers()

    async def invoke(name: str) -> tuple[str, list[dict[str, Any]] | Exception]:
        try:
            rows = await providers[name].search(
                latitude=origin_latitude,
                longitude=origin_longitude,
                radius_miles=radius_miles,
                query=query,
                limit=limit,
            )
            return name, rows
        except Exception as exc:
            return name, exc

    outcomes = await asyncio.gather(*(invoke(name) for name in selected))
    provider_status: dict[str, Any] = {}
    combined: list[dict[str, Any]] = []
    successful = 0
    for name, outcome in outcomes:
        if isinstance(outcome, Exception):
            provider_status[name] = {"status": "unavailable", "count": 0, "warning": str(outcome)}
        else:
            successful += 1
            combined.extend(outcome)
            provider_status[name] = {"status": "ok", "count": len(outcome), "warning": None}
    if not successful:
        raise HTTPException(status_code=503, detail={"message": "no selected provider is available", "providers": provider_status})

    combined.sort(key=lambda row: row.get("properties", {}).get("distance_miles", float("inf")))
    combined = combined[:limit]
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "type": "FeatureCollection",
        "origin": feature(
            feature_id="origin",
            latitude=origin_latitude,
            longitude=origin_longitude,
            properties={
                "label": origin_label,
                "location_source": origin_source,
                "cached": origin_cached,
            },
        ),
        "features": combined,
        "providers": provider_status,
        "metadata": {
            "generated_at": generated_at,
            "radius_miles": radius_miles,
            "query": query,
            "sources": selected,
            "limit": limit,
            "attribution": {
                "basemap": "OpenStreetMap contributors",
                "geocoder": "Nominatim / OpenStreetMap contributors" if has_place else None,
            },
        },
    }


@app.get("/map/search")
async def map_search(
    place: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    radius_miles: float = Query(25, gt=0, le=1000),
    query: str | None = Query(None, max_length=512),
    sources: str = "x,datasets",
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    return await run_search(
        place=place,
        latitude=latitude,
        longitude=longitude,
        radius_miles=radius_miles,
        query=query,
        sources=sources,
        limit=limit,
    )


@app.get("/search/tweets", deprecated=True)
async def legacy_tweet_search(
    response: Response,
    city: str,
    distance: float = Query(25, gt=0, le=1000),
    query: str | None = Query(None, max_length=512),
    limit: int = Query(100, ge=1, le=100),
) -> dict[str, Any]:
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Wed, 01 Jul 2027 00:00:00 GMT"
    response.headers["Link"] = '</map/search>; rel="successor-version"'
    return await run_search(
        place=city,
        latitude=None,
        longitude=None,
        radius_miles=distance,
        query=query,
        sources="x",
        limit=limit,
    )


@app.get("/map/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/map/readyz")
def readyz() -> dict[str, Any]:
    try:
        geocoder = get_geocoder()
        geocoder._prepare_cache()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"geocoder cache is not writable: {exc}") from exc
    return {
        "status": "ready",
        "providers": {
            "datasets": "configured",
            "x": "configured" if settings.x_bearer_token else "optional-unconfigured",
        },
    }
