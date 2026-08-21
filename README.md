# Social Mapping

Social Mapping is a React and Leaflet client for exploring social media posts on a map. The current search flow is designed for the companion [sm-service](https://github.com/KingAkeem/sm-service), which returns GeoJSON features for geographically searchable Twitter data.

## What it does

- Search the service by city or address and radius.
- Fly the map to the search origin.
- Display returned posts as map markers with property details in popups.
- Review the same results in an archive table.

The application expects the service response to contain an `origin` object with `latitude` and `longitude`, plus a `features` array whose geometries use GeoJSON `[longitude, latitude]` coordinates.

## Requirements

- Node.js 16 or newer
- A running instance of the companion search service

## Getting started

```bash
npm install
npm start
```

The development server runs at `http://localhost:3000`. By default, searches are sent to `http://localhost:5000`. To use another service URL, set `REACT_APP_API_BASE_URL` before starting the app:

```bash
REACT_APP_API_BASE_URL=https://example.test npm start
```

## Available scripts

| Command | Purpose |
| --- | --- |
| `npm start` | Run the development server |
| `npm test -- --watchAll=false` | Run the test suite once |
| `npm run build` | Create a production build |

## Notes

The project is intentionally a frontend prototype. The companion service owns geocoding, search, and data collection. Do not place service credentials in the React application; use the service configuration for those secrets.

## License

No license has been selected for this private repository yet. Add one before distributing the project outside its current ownership.
