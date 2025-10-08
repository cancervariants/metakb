const API_BASE = '/cv-api/api/v2'

/**
 * Retrieve MetaKB version
 *
 * @returns version value
 */
export const fetchVersion = async (): string => {
  const controller = new AbortController()
  const res = await fetch(`${API_BASE}/service-info`, {
    headers: { 'Content-Type': 'application/json' },
    signal: controller.signal,
  })
  if (!res.ok) throw new Error(`Request failed: ${res.status}`)
  const data = await res.json()
  return data.version
}
