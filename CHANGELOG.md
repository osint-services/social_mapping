# Changelog

All notable changes to Social Mapping are documented here.

## [0.2.0] - 2026-08-21

### Added

- Setup and usage documentation for the React client and companion search service.
- `REACT_APP_API_BASE_URL` configuration for choosing the search service endpoint.

### Changed

- Start the map at a world view until a search result provides a location.
- Use stable archive table row IDs and collect columns across all returned features.
- Improve page title, metadata, and installable app manifest branding.
- Improve search validation and report non-successful service responses.
- Use an effect for map movement so rendering remains side-effect free.

### Fixed

- Convert GeoJSON `[longitude, latitude]` coordinates to Leaflet `[latitude, longitude]` positions.
- Replace the default Create React App smoke test with an assertion for the actual navigation.

[0.2.0]: https://github.com/KingAkeem/SocialMapping/releases/tag/v0.2.0
