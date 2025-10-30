// API de dispositivos (placeholders).
import client from './client'

// GET /api/devices -> app.routes.device_routes.list_devices
export const getDevices = () => client.get('/devices')

// POST /api/devices -> app.routes.device_routes.create_device
// Si el backend responde 402 con { upsell: true }, propagamos una Error con flag.
export const createDevice = async (payload) => {
  try {
    const res = await client.post('/devices', payload)
    return res
  } catch (err) {
    if (err?.response?.status === 402) {
      const e = new Error(err.response?.data?.message || 'Upsell requerido')
      e.upsell = true
      e.payload = err.response?.data
      throw e
    }
    throw err
  }
}