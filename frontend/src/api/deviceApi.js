// API de dispositivos (placeholders).
import client from './client'

export const listDevices = async () => {
  // return client.get('/devices')
  return { data: [] }
}

export const createDevice = async (payload) => {
  // return client.post('/devices', payload)
  return { data: { ...payload, id: 'temp' } }
}