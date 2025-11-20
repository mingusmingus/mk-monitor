// Cliente HTTP base (Axios) para consumir el backend Flask.
// DEBUG: logs con prefijo [HTTP] (remover tras estabilizar).
import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api'
})

// Interceptor de request: leer SIEMPRE token fresco desde localStorage
client.interceptors.request.use((config) => {
  const t = localStorage.getItem('auth_token')
  if (t) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${t}`
  }
  console.debug('[HTTP] request', config.url, 'Auth?', !!t)
  return config
})

// Helper para evitar múltiples ejecuciones en ráfaga de ciertos status
let lastHandledKey = null
const alreadyHandled = (key) => {
  if (lastHandledKey === key) return true
  lastHandledKey = key
  setTimeout(() => {
    lastHandledKey = null
  }, 500)
  return false
}

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
        console.debug('[HTTP] 401 en ruta de auth, ignorado')
        return Promise.reject(error)
      }
      if (!t) {
        console.debug('[HTTP] 401 sin token (pre-auth), ignorar')
        return Promise.reject(error)
      }
      if (!authReady) {
        if (!config.__retry401) {
          console.debug('[HTTP] 401 con token pero authReady=false (race). Reintentando...')
          await new Promise(r => setTimeout(r, 120))
          config.__retry401 = true
          return client(config)
        }
        console.debug('[HTTP] 401 tras reintento race. Marcando expirado.')
      }
      console.warn('[HTTP] 401 definitivo. Disparando evento auth:expired')
      if (!alreadyHandled('401-default')) {
        window.dispatchEvent(new CustomEvent('auth:expired'))
      }
      return Promise.reject(error)
    }

    // 402: pago requerido -> redirigir a /subscription y abrir upsell
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

    // 403 / 423: tenant suspendido o restringido. Mantener sesión, actualizar bandera.
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
