import { useEffect } from 'react'
import L from 'leaflet'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'

const markerIcon = L.divIcon({ className: 'evidence-marker', html: '<span></span>', iconSize: [22, 22], iconAnchor: [11, 11] })
const originIcon = L.divIcon({ className: 'origin-marker', html: '<span></span>', iconSize: [28, 28], iconAnchor: [14, 14] })

function Reframe({ origin, features }) {
  const map = useMap()
  useEffect(() => {
    if (!origin?.geometry?.coordinates) return
    const points = [origin, ...features]
      .map((item) => item?.geometry?.coordinates)
      .filter(Boolean)
      .map(([longitude, latitude]) => [latitude, longitude])
    if (points.length === 1) map.setView(points[0], 10)
    else if (points.length > 1) map.fitBounds(points, { padding: [40, 40], maxZoom: 13 })
  }, [features, map, origin])
  return null
}

function MarkerDetails({ item }) {
  const details = item.properties || {}
  return (
    <div className="popup">
      <strong>{details.title || details.name || 'Mapped record'}</strong>
      {details.text && <p>{details.text}</p>}
      <dl>
        <dt>Source</dt><dd>{details.source}</dd>
        <dt>Accuracy</dt><dd>{details.location_accuracy || 'unknown'}</dd>
        {details.distance_miles != null && <><dt>Distance</dt><dd>{details.distance_miles} mi</dd></>}
      </dl>
      {details.associated_phones?.length > 0 && (
        <p>Associated phone records: {details.associated_phones.map((phone) => phone.phone || phone).join(', ')}</p>
      )}
      {details.url && <a href={details.url} target="_blank" rel="noreferrer">Open source</a>}
    </div>
  )
}

export default function MapView({ origin, features }) {
  const initial = origin?.geometry?.coordinates || [-0.1276, 51.5072]
  return (
    <MapContainer center={[initial[1], initial[0]]} zoom={4} className="map" scrollWheelZoom>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Reframe origin={origin} features={features} />
      {origin?.geometry && (
        <Marker position={[origin.geometry.coordinates[1], origin.geometry.coordinates[0]]} icon={originIcon}>
          <Popup><strong>Search origin</strong><br />{origin.properties?.label}</Popup>
        </Marker>
      )}
      {features.map((item) => (
        <Marker key={item.id} position={[item.geometry.coordinates[1], item.geometry.coordinates[0]]} icon={markerIcon}>
          <Popup><MarkerDetails item={item} /></Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
