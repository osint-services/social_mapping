# Changelog

All notable changes to Social Mapping are documented here.

## [1.0.0] - 2026-08-21

### Added

- FastAPI geospatial service with canonical `/map/search`, health, readiness, and OpenAPI documentation.
- Imported-dataset and X recent-search provider adapters with provider-level degradation reporting.
- Evidence-oriented GeoJSON models with origin, provenance, timestamps, confidence, distance, and location accuracy.
- Server-side Nominatim place resolution with durable 30-day caching, process-wide rate limiting, attribution, and configurable identity.
- Unit coverage for coordinate validation, radius filtering, X normalization, place centroids, provider failures, geocoder caching, GeoJSON, and the legacy route.
- Docker deployment and mocked CI checks.

### Changed

- Transferred the project to `osint-services/social_mapping` and changed the default branch to `main`.
- Replaced the deleted `sm-service` dependency with the repository's own API.
- Rebuilt the standalone client on Vite, React 19, and React Leaflet 5.
- Expanded the client with source filtering, provider warnings, accuracy badges, provenance, associated metadata, and a local result archive.
- Licensed the project under GPL-3.0-only.

### Security

- Removed the obsolete Create React App dependency tree and default generated assets.
- Excluded posts that lack provider-supplied geospatial evidence and prevented profile-location geocoding.
- Kept provider secrets exclusively in the server environment.

## [0.2.0] - 2026-08-21

- Refined the original frontend prototype and documented its now-retired companion-service flow.

[1.0.0]: https://github.com/osint-services/social_mapping/releases/tag/v1.0.0
[0.2.0]: https://github.com/osint-services/social_mapping/releases/tag/v0.2.0
