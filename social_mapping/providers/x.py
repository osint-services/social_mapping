from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import tweepy

from social_mapping.geo import centroid_from_bbox, feature, haversine_miles


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data
    return {key: item for key, item in vars(value).items() if not key.startswith("_")}


def normalize_x_response(
    response: Any,
    *,
    origin_latitude: float,
    origin_longitude: float,
    radius_miles: float,
) -> list[dict[str, Any]]:
    includes = _as_dict(response).get("includes") or getattr(response, "includes", {}) or {}
    places = {_as_dict(place).get("id"): _as_dict(place) for place in includes.get("places", [])}
    users = {_as_dict(user).get("id"): _as_dict(user) for user in includes.get("users", [])}
    rows = _as_dict(response).get("data") or getattr(response, "data", None) or []
    results: list[dict[str, Any]] = []

    for raw in rows:
        post = _as_dict(raw)
        geo = post.get("geo") or {}
        coordinates = geo.get("coordinates") or {}
        raw_coordinates = coordinates.get("coordinates") if isinstance(coordinates, dict) else None
        accuracy = "exact"
        location_source = "x_coordinates"

        if raw_coordinates and len(raw_coordinates) >= 2:
            longitude, latitude = map(float, raw_coordinates[:2])
        else:
            place_id = geo.get("place_id")
            place = places.get(place_id, {})
            bbox = (place.get("geo") or {}).get("bbox")
            if not bbox:
                continue
            latitude, longitude = centroid_from_bbox(bbox)
            accuracy = "place"
            location_source = "x_place_centroid"

        distance = haversine_miles(origin_latitude, origin_longitude, latitude, longitude)
        if distance > radius_miles:
            continue
        author = users.get(post.get("author_id"), {})
        created_at = post.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.astimezone(timezone.utc).isoformat()
        post_id = str(post.get("id", "unknown"))
        results.append(
            feature(
                feature_id=f"x:{post_id}",
                latitude=latitude,
                longitude=longitude,
                properties={
                    "source": "x",
                    "record_type": "post",
                    "title": f"@{author.get('username', 'unknown')}",
                    "text": post.get("text", ""),
                    "url": f"https://x.com/{author.get('username', 'i')}/status/{post_id}",
                    "timestamp": created_at,
                    "location_accuracy": accuracy,
                    "location_source": location_source,
                    "confidence": 1.0 if accuracy == "exact" else 0.75,
                    "distance_miles": round(distance, 3),
                    "provenance": {
                        "provider": "x_recent_search",
                        "post_id": post_id,
                        "author_id": post.get("author_id"),
                        "provider_geospatial_evidence": True,
                    },
                },
            )
        )
    return results


class XProvider:
    name = "x"

    def __init__(self, bearer_token: str | None) -> None:
        self.bearer_token = bearer_token

    async def search(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_miles: float,
        query: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        if not self.bearer_token:
            raise RuntimeError("X provider is not configured")
        return await asyncio.to_thread(
            self._search_sync,
            latitude=latitude,
            longitude=longitude,
            radius_miles=radius_miles,
            query=query,
            limit=limit,
        )

    def _search_sync(
        self,
        *,
        latitude: float,
        longitude: float,
        radius_miles: float,
        query: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        client = tweepy.Client(bearer_token=self.bearer_token, wait_on_rate_limit=False)
        terms = [query.strip()] if query and query.strip() else []
        terms.extend(["has:geo", "-is:retweet"])
        response = client.search_recent_tweets(
            query=" ".join(terms),
            max_results=max(10, min(100, limit)),
            expansions=["geo.place_id", "author_id"],
            tweet_fields=["created_at", "geo", "author_id"],
            place_fields=["geo", "full_name", "country"],
            user_fields=["username", "name"],
        )
        return normalize_x_response(
            response,
            origin_latitude=latitude,
            origin_longitude=longitude,
            radius_miles=radius_miles,
        )[:limit]
