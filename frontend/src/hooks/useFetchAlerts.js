import { useCallback, useEffect, useState } from 'react'
import { getAlerts } from '../api/alertApi.js'
import useAuth from '../hooks/useAuth.js'

// Hook para obtener alertas con filtros, manejando loading/error.
// Gating estricto por authReady + token.
// DEBUG: logs con prefijo [Hook] (remover tras estabilizar).
export default function useFetchAlerts(initialFilters = {}) {
  const [alerts, setAlerts] = useState([])
  const [filters, setFilters] = useState(initialFilters)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { token, authReady } = useAuth()

  const fetchAlerts = useCallback(async (signal) => {
    if (!authReady || !token) {
      console.debug('[Hook] useFetchAlerts skip (authReady/token no listos)')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await getAlerts(filters, signal)
      if (!signal?.aborted) {
        setAlerts(res.data || [])
      }
    } catch (e) {
      if (e.name !== 'AbortError' && !signal?.aborted) {
        setError(e)
      }
    } finally {
      if (!signal?.aborted) {
        setLoading(false)
      }
    }
  }, [filters, authReady, token])

  useEffect(() => {
    const abortController = new AbortController()
    fetchAlerts(abortController.signal)
    return () => abortController.abort()
  }, [fetchAlerts])

  return { alerts, loading: loading || (!authReady || !token), error, refetch: fetchAlerts, setFilters }
}