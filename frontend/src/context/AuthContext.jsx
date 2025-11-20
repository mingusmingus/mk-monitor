import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { login as apiLogin } from '../api/authApi.js'
import client from '../api/client.js'

/**
 * Contexto de autenticación.
 * - token (JWT)
 * - role
 * - tenantStatus
 * - authReady (evita race de primeras llamadas protegidas)
 * - expiredSession (modal para expiración y confirmación)
 * DEBUG: logs con prefijo [Auth] (remover tras estabilizar).
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
// Claves legacy que podemos migrar
const LEGACY_KEYS = ['access_token', 'token']

export function AuthProvider({ children }) {
  // Migración: si existe clave legacy y falta nueva -> mover.
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

  // Aplicar header si token inicial ya existe
  useEffect(() => {
    if (token) {
      client.defaults.headers.common.Authorization = `Bearer ${token}`
      window.__AUTH_READY = true
    }
  }, [token])

  // Persistencias
  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }, [token])

  useEffect(() => {
    if (role) localStorage.setItem('role', role)
    else localStorage.removeItem('role')
  }, [role])

  useEffect(() => {
    if (tenantStatus) localStorage.setItem('tenant_status', tenantStatus)
  }, [tenantStatus])

  const login = useCallback(async (email, password) => {
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
      console.debug('[Auth] login ok, token prefix:', jwt.slice(0, 16))
      return true
    }
    return false
  }, [])

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
    console.debug('[Auth] logout')
  }, [])

  const markExpired = useCallback(() => {
    console.warn('[Auth] sesión marcada como expirada')
    setExpiredSession(true)
  }, [])

  const verify = useCallback(async () => {
    if (!token) return false
    try {
      const r = await client.get('/auth/me')
      return !!r.data?.ok
    } catch {
      return false
    }
  }, [token])

  // Listener para actualización del estado del tenant
  useEffect(() => {
    function handleTenantStatus(e) {
      const status = e.detail?.status
      if (status) setTenantStatus(status)
    }
    window.addEventListener('tenant:status', handleTenantStatus)
    return () => window.removeEventListener('tenant:status', handleTenantStatus)
  }, [])

  // Listener para expiración disparada por interceptor HTTP
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
