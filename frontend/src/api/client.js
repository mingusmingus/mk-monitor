// Cliente HTTP base (Axios) para consumir el backend Flask.
// Base URL en dev: http://localhost:5000/api
// TODO: permitir inyección del token desde AuthContext si se prefiere.
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api'
})

// Interceptor de request: agrega el token si existe
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Helper para evitar múltiples ejecuciones en ráfaga
let lastStatusHandled = null
const alreadyHandled = (status) => {
  if (lastStatusHandled === status) return true
  lastStatusHandled = status
  setTimeout(() => {
    // Resetea el status para permitir manejar futuros eventos
    lastStatusHandled = null
  }, 500)
  return false
}

// Interceptor de respuesta para manejar estados de auth / subscripción
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error
    if (!response) return Promise.reject(error) // Network error o cancelación
    const status = response.status
    const path = window.location.pathname

    // 401: expira sesión -> logout global y redirige a /login
    if (status === 401) {
      if (!alreadyHandled(status)) {
        if (path !== '/login') {
          window.dispatchEvent(
            new CustomEvent('auth:logout', { detail: { reason: 'expired' } })
          )
        }
      }
      return Promise.reject(error)
    }

    // 402: pago requerido -> redirigir a /subscription y abrir upsell
    if (status === 402) {
      if (!alreadyHandled(status)) {
        if (path !== '/subscription') {
          const url = new URL(window.location.origin + '/subscription')
          url.searchParams.set('upsell', '1')
          window.location.assign(url.toString())
        } else {
          // Ya estamos en /subscription, disparar evento para abrir modal
          window.dispatchEvent(new CustomEvent('subscription:upsell'))
        }
      }
      return Promise.reject(error)
    }

    // 403 / 423: tenant suspendido o restringido. Mantener sesión, actualizar bandera.
    if (status === 403 || status === 423) {
      const tenantStatus = response.data?.tenant_status
      // TODO: manejar tenantStatus (por ejemplo, mostrar un aviso en la UI o disparar un evento global)
      // window.dispatchEvent(new CustomEvent('tenant:status', { detail: { status: tenantStatus } }))
      return Promise.reject(error)
    }

    // Otros errores -> los pasa tal cual al caller
    return Promise.reject(error)
  }
)

export default client
