import { useMemo, useState } from 'react'
import MapView from './MapView.jsx'
import { associatedPhoneLabel, searchMap } from './api.js'

const EMPTY_COLLECTION = { features: [], providers: {}, metadata: {} }

function Badge({ children, tone = 'neutral' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}

function ResultCard({ item, onArchive }) {
  const details = item.properties || {}
  return (
    <article className="result-card">
      <div className="result-title">
        <strong>{details.title || details.name || 'Mapped record'}</strong>
        <button type="button" className="text-button" onClick={() => onArchive(item)}>Archive</button>
      </div>
      {details.text && <p>{details.text}</p>}
      <div className="badges">
        <Badge tone="source">{details.source}</Badge>
        <Badge>{details.location_accuracy || 'unknown accuracy'}</Badge>
        {details.distance_miles != null && <Badge>{details.distance_miles} mi</Badge>}
      </div>
      {details.associated_phones?.length > 0 && (
        <p className="metadata">Associated phones: {details.associated_phones.map(associatedPhoneLabel).join(', ')}</p>
      )}
      <details>
        <summary>Provenance</summary>
        <pre>{JSON.stringify(details.provenance || {}, null, 2)}</pre>
      </details>
    </article>
  )
}

export default function App() {
  const [place, setPlace] = useState('London')
  const [radiusMiles, setRadiusMiles] = useState(25)
  const [query, setQuery] = useState('')
  const [sources, setSources] = useState(['datasets', 'x'])
  const [collection, setCollection] = useState(EMPTY_COLLECTION)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [view, setView] = useState('results')
  const [archive, setArchive] = useState(() => {
    try { return JSON.parse(localStorage.getItem('social-mapping-archive') || '[]') }
    catch { return [] }
  })

  const warnings = useMemo(
    () => Object.entries(collection.providers || {}).filter(([, status]) => status.warning),
    [collection.providers],
  )

  function toggleSource(source) {
    setSources((current) => current.includes(source) ? current.filter((value) => value !== source) : [...current, source])
  }

  async function submit(event) {
    event.preventDefault()
    setError('')
    if (!sources.length) {
      setError('Select at least one source.')
      return
    }
    setLoading(true)
    try {
      setCollection(await searchMap({ place, radiusMiles, query, sources }))
      setView('results')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  function archiveResult(item) {
    const next = [item, ...archive.filter((saved) => saved.id !== item.id)].slice(0, 100)
    setArchive(next)
    localStorage.setItem('social-mapping-archive', JSON.stringify(next))
  }

  const visible = view === 'archive' ? archive : collection.features
  return (
    <main className="app-shell">
      <header className="masthead">
        <div>
          <p className="eyebrow">OSINT Services</p>
          <h1>Social Mapping</h1>
          <p>Map only provider-supplied coordinates and explicitly located dataset evidence.</p>
        </div>
        <div className="provider-summary" aria-label="Provider status">
          {Object.entries(collection.providers || {}).map(([name, status]) => (
            <Badge key={name} tone={status.status === 'ok' ? 'ok' : 'warning'}>{name}: {status.status}</Badge>
          ))}
        </div>
      </header>
      <form className="search-panel" onSubmit={submit}>
        <label>Place<input value={place} onChange={(event) => setPlace(event.target.value)} required /></label>
        <label>Radius (miles)<input type="number" min="1" max="1000" value={radiusMiles} onChange={(event) => setRadiusMiles(event.target.value)} required /></label>
        <label>Keyword<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Optional" /></label>
        <fieldset>
          <legend>Sources</legend>
          {['datasets', 'x'].map((source) => (
            <label className="check" key={source}><input type="checkbox" checked={sources.includes(source)} onChange={() => toggleSource(source)} /> {source}</label>
          ))}
        </fieldset>
        <button className="primary" disabled={loading}>{loading ? 'Searching…' : 'Search map'}</button>
      </form>
      {error && <div role="alert" className="alert error">{error}</div>}
      {warnings.map(([name, status]) => <div key={name} className="alert warning">{name}: {status.warning}</div>)}
      <section className="workspace">
        <MapView origin={collection.origin} features={collection.features} />
        <aside className="results">
          <div className="result-tabs">
            <button className={view === 'results' ? 'active' : ''} onClick={() => setView('results')}>Results ({collection.features.length})</button>
            <button className={view === 'archive' ? 'active' : ''} onClick={() => setView('archive')}>Archive ({archive.length})</button>
          </div>
          <div className="result-list">
            {visible.length ? visible.map((item) => <ResultCard key={item.id} item={item} onArchive={archiveResult} />) : (
              <div className="empty-state">Search a place to view evidence-backed map results.</div>
            )}
          </div>
        </aside>
      </section>
      <footer>OpenStreetMap and Nominatim attribution applies. Coordinates describe evidence records, never a person or device's current location.</footer>
    </main>
  )
}
