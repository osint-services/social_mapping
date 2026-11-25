from __future__ import annotations

from typing import Any

import httpx

from social_mapping.geo import centroid_from_bbox, feature, haversine_miles


def normalize_x_response(
    response: dict[str, Any],
    *,
    origin_latitude: float,
    origin_longitude: float,
    radius_miles: float,
) -> list[dict[str, Any]]:
    includes = response.get("includes") or {}
    places = {place["id"]: place for place in includes.get("places", [])}
    users = {user["id"]: user for user in includes.get("users", [])}
    results: list[dict[str, Any]] = []

    for post in response.get("data") or []:
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

    def __init__(self, bearer_token: str | None, timeout: float = 15) -> None:
        self.bearer_token = bearer_token
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
        if not self.bearer_token:
            raise RuntimeError("X provider is not configured")

        terms = [query.strip()] if query and query.strip() else []
        terms.extend(["has:geo", "-is:retweet"])
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    "https://api.x.com/2/tweets/search/recent",
                    headers={"Authorization": f"Bearer {self.bearer_token}"},
                    params={
                        "query": " ".join(terms),
                        "max_results": max(10, min(100, limit)),
                        "expansions": "geo.place_id,author_id",
                        "tweet.fields": "created_at,geo,author_id",
                        "place.fields": "geo,full_name,country",
                        "user.fields": "username,name",
                    },
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"X recent search returned HTTP {exc.response.status_code}.") from exc
        except httpx.RequestError as exc:
            raise RuntimeError("X recent search did not respond.") from exc

        try:
            return normalize_x_response(
                response.json(),
                origin_latitude=latitude,
                origin_longitude=longitude,
                radius_miles=radius_miles,
            )[:limit]
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("X returned invalid recent search data.") from exc
