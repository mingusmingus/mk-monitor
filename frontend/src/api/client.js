// Cliente HTTP base (Axios) para consumir el backend Flask.
// Base URL en dev: http://localhost:5000/api
// TODO: permitir inyección del token desde AuthContext si se prefiere.
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api'
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
