import { useEffect, useState } from 'react'
import client from '../api/client'

// Hook para leer salud de dispositivos desde /api/health/devices.
export default function useDeviceHealth() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    const load = async () => {
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
  }, [])

  return { devices, loading, error }
}
