# API contract

## `GET /map/search`

Parameters:

| Name | Type | Rules |
| --- | --- | --- |
| `place` | string | Mutually exclusive with coordinates; resolved only as the search origin |
| `latitude` | number | Must be paired with longitude and fall between -90 and 90 |
| `longitude` | number | Must be paired with latitude and fall between -180 and 180 |
| `radius_miles` | number | Greater than 0 and no more than 1000; default 25 |
| `query` | string | Optional provider keyword filter |
| `sources` | CSV | `datasets`, `x`, or both; default `x,datasets` |
| `limit` | integer | 1 to 500; default 100 |

The response is a GeoJSON `FeatureCollection` with these top-level additions:

- `origin`: a GeoJSON point for the investigator's search origin.
- `providers`: status, result count, and warning for every selected provider.
- `metadata`: generation time, radius, query, selected sources, limit, and required attribution.

Every result feature includes `source`, `location_accuracy`, `location_source`, `confidence`, `distance_miles`, and `provenance`. Provider-specific identity fields and associated phone records are properties, not geometries.

## Compatibility endpoint

`GET /search/tweets?city=&distance=` delegates to `/map/search` with `sources=x`. It returns deprecation, sunset, and successor link headers. It will be removed in the next major release.

## Health

- `GET /map/healthz` reports process health.
- `GET /map/readyz` verifies that the durable geocoder cache can be opened. X is optional and reports `optional-unconfigured` without making readiness fail.

## Provider behavior

### Imported datasets

The service requests `/datasets/search/geo` from the platform dataset service. Records must already contain an explicit coordinate pair. Text locations are not geocoded by this provider. Associated phone rows may be shown in marker details but never become location evidence.

### X recent search

The service uses the existing `TWEEPY_BEARER_TOKEN`. It preserves exact post coordinates. When only an X place is supplied, it uses the centroid of the provider bounding box and labels the accuracy `place`. Posts without provider-supplied geospatial evidence are discarded, even when an author profile contains location text.

### Nominatim

Nominatim resolves only investigator-entered place text. Requests are server-side, have an identifying User-Agent, use a normalized durable cache refreshed after 30 days, and are spaced by at least one second across the process. There is no autocomplete request stream.

## Migration from 0.2

- Replace `REACT_APP_API_BASE_URL` with `VITE_API_BASE_URL`.
- Replace the removed `sm-service` with this repository's FastAPI app.
- Update client integrations from `/search/tweets` to `/map/search` and consume GeoJSON `origin`, `providers`, and `metadata`.
- Use a [supported Node.js version](../README.md#quick-start) for the Vite client.
