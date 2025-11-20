import { useEffect, useState } from 'react'
import client from '../api/client'
import useAuth from '../hooks/useAuth.js'

// Hook para leer salud de dispositivos desde /api/health/devices.
// Gating por authReady + token.
// DEBUG: logs con prefijo [Hook] (remover tras estabilizar).
export default function useDeviceHealth() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const { token, authReady } = useAuth()

  useEffect(() => {
    const load = async () => {
      if (!authReady || !token) {
        console.debug('[Hook] useDeviceHealth skip (authReady/token no listos)')
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

  return { devices, loading: loading || (!authReady || !token), error }
}
