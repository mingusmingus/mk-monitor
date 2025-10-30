import { useCallback, useEffect, useState } from 'react'
import { getAlerts } from '../api/alertApi.js'

// Hook para obtener alertas con filtros, manejando loading/error.
export default function useFetchAlerts(initialFilters = {}) {
  const [alerts, setAlerts] = useState([])
  const [filters, setFilters] = useState(initialFilters)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchAlerts = useCallback(async () => {
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
  }, [filters])

  useEffect(() => {
    fetchAlerts()
  }, [fetchAlerts])

  return { alerts, loading, error, refetch: fetchAlerts, setFilters }
}