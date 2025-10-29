// Cliente HTTP base (Axios) para consumir el backend Flask.
// Configura baseURL desde variables de entorno de Vite (VITE_API_URL) y adjunta JWT si existe.
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default client
