import { useCallback, useEffect, useState } from 'react'
import { getAlerts } from '../api/alertApi.js'
import useAuth from '../hooks/useAuth.js'

/**
 * Hook personalizado para consultar alertas.
 *
 * Permite filtrar alertas, refrescar datos y gestionar estados de carga.
 *
 * @param {Object} initialFilters - Filtros iniciales (estado, dispositivo, etc.).
 * @returns {Object} { alerts, loading, error, refetch, setFilters }
 */
export default function useFetchAlerts(initialFilters = {}) {
  const [alerts, setAlerts] = useState([])
  const [filters, setFilters] = useState(initialFilters)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { token, authReady } = useAuth()

  const fetchAlerts = useCallback(async () => {
    // Verificación estricta de autenticación
    if (!authReady || !token) {
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await getAlerts(filters)
      setAlerts(res.data || [])
    } catch (e) {
      setError(e)
    } finally {
      setLoading(false)
    }
  }, [filters, authReady, token])

  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  return { alerts, loading: loading || (!authReady || !token), error, refetch: fetchAlerts, setFilters }
}
