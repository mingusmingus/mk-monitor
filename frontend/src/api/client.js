/**
 * Cliente HTTP Base (Axios) para la comunicación con el Backend.
 *
 * Gestiona:
 * - Inyección automática del token de autenticación.
 * - Manejo global de errores (401 Expirado, 402 Pago Requerido, 403 Suspendido).
 */
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api'
})

// Interceptor de Solicitud: Inyecta el token Bearer si existe
client.interceptors.request.use((config) => {
  const t = localStorage.getItem('auth_token')
  if (t) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${t}`
  }
  return config
})

// Helper para evitar rebotes de eventos en errores simultáneos
let lastHandledKey = null
const alreadyHandled = (key) => {
  if (lastHandledKey === key) return true
  lastHandledKey = key
  setTimeout(() => {
    lastHandledKey = null
  }, 500)
  return false
}

// Interceptor de Respuesta: Manejo centralizado de errores de estado
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error
    if (!response) return Promise.reject(error)

    const status = response.status
    const requestUrl = config?.url || ''
    const isAuthRoute = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register')
    const t = localStorage.getItem('auth_token')
    const authReady = window.__AUTH_READY === true

    // 401 Unauthorized: Sesión expirada o inválida
    if (status === 401) {
      const reason = response.data?.reason
      const message = response.data?.message || ''
      if (reason === 'expired' || /token expirado/i.test(message)) {
        if (!alreadyHandled('401-expired')) {
          window.dispatchEvent(new CustomEvent('auth:expired', { detail: { reason: 'expired' } }))
        }
        return Promise.reject(error)
      }
      if (isAuthRoute) {
        return Promise.reject(error)
      }
      if (!t) {
        return Promise.reject(error)
      }
      // Reintento en condiciones de carrera (race condition) al cargar la app
      if (!authReady) {
        if (!config.__retry401) {
          await new Promise(r => setTimeout(r, 120))
          config.__retry401 = true
          return client(config)
        }
      }

      if (!alreadyHandled('401-default')) {
        window.dispatchEvent(new CustomEvent('auth:expired'))
      }
      return Promise.reject(error)
    }

    // 402 Payment Required: Redirigir a suscripción/upsell
    if (status === 402) {
      if (!alreadyHandled('402')) {
        if (window.location.pathname !== '/subscription') {
          const url = new URL(window.location.origin + '/subscription')
            url.searchParams.set('upsell', '1')
          window.location.assign(url.toString())
        } else {
          window.dispatchEvent(new CustomEvent('subscription:upsell'))
        }
      }
      return Promise.reject(error)
    }

    // 403 Forbidden / 423 Locked: Tenant suspendido o restringido
    if (status === 403 || status === 423) {
      const tenantStatus = response.data?.tenant_status
      if (tenantStatus) {
        if (!alreadyHandled(String(status))) {
          window.dispatchEvent(new CustomEvent('tenant:status', { detail: { status: tenantStatus } }))
        }
      }
      return Promise.reject(error)
    }

    return Promise.reject(error)
  }
)

export default client
