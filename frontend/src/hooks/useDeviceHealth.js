import { useEffect, useState } from 'react'
import client from '../api/client'
import useAuth from '../hooks/useAuth.js'

/**
 * Hook personalizado para obtener el estado de salud de los dispositivos.
 *
 * Consulta el endpoint /api/health/devices y gestiona los estados de carga y error.
 * Requiere que la autenticación esté lista.
 *
 * @returns {Object} { devices: Array, loading: Boolean, error: Error }
 */
export default function useDeviceHealth() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { token, authReady } = useAuth()

  useEffect(() => {
    const load = async () => {
      // Evitar fetch si la autenticación no está lista
      if (!authReady || !token) {
        return
      }
      setLoading(true)
      setError(null)
      try {
        const res = await client.get('/health/devices')
        setDevices(res.data || [])
      } catch (e) {
        setError(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [authReady, token])

  // Considerar cargando mientras se espera la autenticación
  return { devices, loading: loading || (!authReady || !token), error }
}
