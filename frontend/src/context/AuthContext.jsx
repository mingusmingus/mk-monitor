import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { login as apiLogin } from '../api/authApi.js'
import client from '../api/client.js'

/**
 * Contexto de Autenticación.
 *
 * Gestiona el estado global de la sesión del usuario, incluyendo:
 * - token (JWT)
 * - role (rol del usuario)
 * - tenantStatus (estado de pago de la cuenta)
 * - authReady (bandera de inicialización)
 * - expiredSession (estado para mostrar modal de re-login)
 */
export const AuthContext = createContext({
  token: null,
  role: null,
  tenantStatus: 'activo',
  authReady: false,
  expiredSession: false,
  login: async () => false,
  logout: () => {},
  markExpired: () => {},
  verify: async () => false
})

const TOKEN_KEY = 'auth_token'
// Claves legadas para migración transparente
const LEGACY_KEYS = ['access_token', 'token']

export function AuthProvider({ children }) {
  // Inicialización: Recuperar token de localStorage, migrando claves antiguas si es necesario
  const initialToken = (() => {
    const existing = localStorage.getItem(TOKEN_KEY)
    if (existing) return existing
    for (const k of LEGACY_KEYS) {
      const legacy = localStorage.getItem(k)
      if (legacy) {
        localStorage.setItem(TOKEN_KEY, legacy)
        LEGACY_KEYS.forEach(x => localStorage.removeItem(x))
        return legacy
      }
    }
    return null
  })()

  const [token, setToken] = useState(initialToken)
  const [role, setRole] = useState(() => localStorage.getItem('role') || null)
  const [tenantStatus, setTenantStatus] = useState(() => localStorage.getItem('tenant_status') || 'activo')
  const [authReady, setAuthReady] = useState(() => !!initialToken)
  const [expiredSession, setExpiredSession] = useState(false)

  // Sincronizar token con headers de axios y estado global
  useEffect(() => {
    if (token) {
      client.defaults.headers.common.Authorization = `Bearer ${token}`
      window.__AUTH_READY = true
    }
  }, [token])

  // Persistencia de Token
  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }, [token])

  // Persistencia de Rol
  useEffect(() => {
    if (role) localStorage.setItem('role', role)
    else localStorage.removeItem('role')
  }, [role])

  // Persistencia de Estado de Tenant
  useEffect(() => {
    if (tenantStatus) localStorage.setItem('tenant_status', tenantStatus)
  }, [tenantStatus])

  /**
   * Inicia sesión en el sistema.
   * @param {string} email
   * @param {string} password
   */
  const login = useCallback(async (email, password) => {
    try {
        const res = await apiLogin(email, password)
        const { token: jwt, role: userRole, tenant_status } = res.data || {}
        setToken(jwt || null)
        setRole(userRole || null)
        setTenantStatus(tenant_status || 'activo')
        if (jwt) {
          client.defaults.headers.common.Authorization = `Bearer ${jwt}`
          localStorage.setItem(TOKEN_KEY, jwt)
          window.__AUTH_READY = true
          setAuthReady(true)
          setExpiredSession(false)
          return true
        }
        return false
    } catch (e) {
        throw e
    }
  }, [])

  /**
   * Cierra la sesión del usuario y limpia el estado local.
   */
  const logout = useCallback(() => {
    setToken(null)
    setRole(null)
    setTenantStatus('activo')
    setAuthReady(false)
    setExpiredSession(false)
    window.__AUTH_READY = false
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem('role')
    localStorage.removeItem('tenant_status')
  }, [])

  /**
   * Marca la sesión actual como expirada.
   */
  const markExpired = useCallback(() => {
    setExpiredSession(true)
  }, [])

  /**
   * Verifica la validez del token actual con el backend.
   */
  const verify = useCallback(async () => {
    if (!token) return false
    try {
      const r = await client.get('/auth/me')
      return !!r.data?.ok
    } catch {
      return false
    }
  }, [token])

  // Listener: Actualización de estado del tenant desde interceptores HTTP
  useEffect(() => {
    function handleTenantStatus(e) {
      const status = e.detail?.status
      if (status) setTenantStatus(status)
    }
    window.addEventListener('tenant:status', handleTenantStatus)
    return () => window.removeEventListener('tenant:status', handleTenantStatus)
  }, [])

  // Listener: Expiración de sesión desde interceptores HTTP
  useEffect(() => {
    function handleExpired() {
      markExpired()
    }
    window.addEventListener('auth:expired', handleExpired)
    return () => window.removeEventListener('auth:expired', handleExpired)
  }, [markExpired])

  const value = useMemo(
    () => ({
      token,
      role,
      tenantStatus,
      authReady,
      expiredSession,
      login,
      logout,
      markExpired,
      verify
    }),
    [token, role, tenantStatus, authReady, expiredSession, login, logout, markExpired, verify]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
