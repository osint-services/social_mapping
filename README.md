# Social Mapping

Social Mapping is the geospatial workspace for [OSINT Services](https://github.com/osint-services). It includes a FastAPI service and a standalone React/Leaflet client. The service combines explicitly located imported records with provider-supplied locations from X and returns one evidence-oriented GeoJSON response.

The project does not infer a person's location from profile text, a phone number, or another indirect signal. Every marker reports its source, location accuracy, provenance, timestamp when available, and distance from the investigator's chosen origin.

## Capabilities

- Search by a place resolved server-side through Nominatim, or by an exact latitude/longitude pair.
- Search imported platform datasets and X recent posts independently or together.
- Preserve exact X post coordinates and label X place-bounding-box centroids as `place` accuracy.
- Return partial results and provider-specific warnings when one provider is unavailable.
- Cache normalized place resolutions durably for 30 days and rate-limit Nominatim requests process-wide.
- Use the standalone browser client or the native Map workspace in [`whoisit`](https://github.com/osint-services/whoisit).
- Preserve the deprecated `/search/tweets` route through the next major release.

## Quick start

The API needs Python 3.11 or newer. The client needs Node.js 22.12 or newer and pnpm.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
GEOCODER_CACHE_PATH=.data/geocoder-cache.db uvicorn social_mapping.server:app --reload
```

In another terminal:

```bash
pnpm install
pnpm dev
```

Open `http://localhost:5173`. The client calls `http://localhost:8000` by default. Set `VITE_API_BASE_URL` to point it elsewhere.

For the complete credential-free demonstration, use the parent [`platform`](https://github.com/osint-services/platform) Compose stack and import `examples/datasets/geospatial-entities.json`. That sample contains synthetic London, Arlington, and Portland records.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATASET_SERVICE_URL` | `http://dataset_service:8000` | Platform dataset API base URL |
| `TWEEPY_BEARER_TOKEN` | unset | Existing X bearer token used for recent search |
| `X_BEARER_TOKEN` | unset | Optional alias when running this service alone |
| `NOMINATIM_BASE_URL` | `https://nominatim.openstreetmap.org` | Configurable geocoder base URL |
| `NOMINATIM_USER_AGENT` | project URL identifier | Required identifying server-side User-Agent |
| `GEOCODER_CACHE_PATH` | `/data/geocoder-cache.db` | Durable SQLite geocoder cache |
| `GEOCODER_CACHE_DAYS` | `30` | Cache refresh interval |
| `GEOCODER_MIN_INTERVAL_SECONDS` | `1` | Process-wide request spacing |
| `PROVIDER_TIMEOUT_SECONDS` | `15` | Upstream provider timeout |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Browser client's API base URL |

Do not put provider tokens in `VITE_*` variables. Those values are bundled into browser code.

## API

`GET /map/search` accepts exactly one location form:

- `place`, or
- both `latitude` and `longitude`

It also accepts `radius_miles`, optional `query`, comma-separated `sources=x,datasets`, and `limit`. Invalid or conflicting locations return `422`; an unresolved place returns `404`. A selected provider may fail without failing the request when another selected provider succeeds. If every selected provider fails, the service returns `503`.

```bash
curl --get http://localhost:8000/map/search \
  --data-urlencode 'place=London' \
  --data-urlencode 'radius_miles=25' \
  --data-urlencode 'sources=datasets,x'
```

See [docs/api.md](docs/api.md) for the response contract, health endpoints, provider behavior, and migration guidance.

## Development checks

```bash
pytest
pnpm test
pnpm build
pnpm audit --prod
```

Tests mock Nominatim and X. CI never consumes X credits or requires external provider availability. A live X smoke test is intentionally separate and credential-gated.

## Accuracy and responsible use

- A marker is an evidence record, not proof of a person's present location.
- Free-text profile locations are never converted into post coordinates.
- Phone records can appear only as associated identity metadata. They never create or imply a phone or device location.
- Place-centroid markers cover an area and are less precise than exact coordinates.
- Dataset coordinates are accepted only as an explicit valid pair and retain their import provenance.
- Respect platform terms, local law, data minimization, and the safety of people represented in results.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
