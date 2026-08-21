import { describe, expect, it, vi } from 'vitest'
import { buildSearchUrl, searchMap } from './api.js'

describe('map API', () => {
  it('builds a canonical search URL', () => {
    const url = new URL(buildSearchUrl({ place: ' London ', radiusMiles: 15, query: 'museum', sources: ['datasets'] }, 'http://api'))
    expect(url.pathname).toBe('/map/search')
    expect(url.searchParams.get('place')).toBe('London')
    expect(url.searchParams.get('radius_miles')).toBe('15')
    expect(url.searchParams.get('sources')).toBe('datasets')
  })

  it('surfaces API errors', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({ detail: 'place not found' }) })
    await expect(searchMap({ place: 'Missing', radiusMiles: 10, query: '', sources: ['datasets'] }, fetcher)).rejects.toThrow('place not found')
  })
})
