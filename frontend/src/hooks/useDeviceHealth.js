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
    const abortController = new AbortController()
    const load = async () => {
      if (!authReady || !token) {
        console.debug('[Hook] useDeviceHealth skip (authReady/token no listos)')
        return
      }
      setLoading(true)
      setError(null)
      try {
        const res = await client.get('/health/devices', { signal: abortController.signal })
        if (!abortController.signal.aborted) {
          setDevices(res.data || [])
        }
      } catch (e) {
        if (e.name !== 'AbortError' && !abortController.signal.aborted) {
          setError(e)
        }
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false)
        }
      }
    }
    load()
    return () => abortController.abort()
  }, [authReady, token])

  return { devices, loading: loading || (!authReady || !token), error }
}
