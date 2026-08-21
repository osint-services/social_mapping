export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

export function buildSearchUrl({ place, radiusMiles, query, sources, limit = 100 }, apiBase = API_BASE) {
  const params = new URLSearchParams({
    place: place.trim(),
    radius_miles: String(radiusMiles),
    sources: sources.join(','),
    limit: String(limit),
  })
  if (query.trim()) params.set('query', query.trim())
  return `${apiBase}/map/search?${params}`
}

export async function searchMap(options, fetcher = fetch) {
  const response = await fetcher(buildSearchUrl(options))
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof payload.detail === 'string' ? payload.detail : payload.detail?.message
    throw new Error(detail || `Search failed (${response.status})`)
  }
  return payload
}
