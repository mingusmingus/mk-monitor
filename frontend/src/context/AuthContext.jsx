import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { login as apiLogin } from '../api/authApi.js'

// Contexto de autenticación.
// Guarda token JWT, role y tenantStatus. Persiste en localStorage.
export const AuthContext = createContext({})

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('access_token') || null)
  const [role, setRole] = useState(() => localStorage.getItem('role') || null)
  const [tenantStatus, setTenantStatus] = useState(() => localStorage.getItem('tenant_status') || 'activo')

  useEffect(() => {
    if (token) localStorage.setItem('access_token', token)
    else localStorage.removeItem('access_token')
  }, [token])

  useEffect(() => {
    if (role) localStorage.setItem('role', role)
    else localStorage.removeItem('role')
  }, [role])

  useEffect(() => {
    if (tenantStatus) localStorage.setItem('tenant_status', tenantStatus)
  }, [tenantStatus])

  const login = useCallback(async (email, password) => {
    // Llama a backend /api/auth/login y guarda credenciales
    // Backend: app.routes.auth_routes.login
    const res = await apiLogin(email, password)
    const { token: jwt, role: userRole, tenant_status } = res.data || {}
    setToken(jwt || null)
    setRole(userRole || null)
    setTenantStatus(tenant_status || 'activo')
    return true
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setRole(null)
    setTenantStatus('activo')
    localStorage.removeItem('access_token')
    localStorage.removeItem('role')
    localStorage.removeItem('tenant_status')
  }, [])

  const value = useMemo(
    () => ({
      token,
      role,
      tenantStatus,
      login,
      logout
    }),
    [token, role, tenantStatus, login, logout]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
