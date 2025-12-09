import React from 'react'
import { useNavigate } from 'react-router-dom'
import ThemeToggle from './ThemeToggle.jsx'
import useAuth from '../../hooks/useAuth.js'

// Header con tenant (placeholder), logout y ThemeToggle.
// Si tenant suspendido, muestra un banner visible.
export default function Header({ onMenuClick }) {
  const { tenantStatus, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      {/* Banner de suspensión (ALTA prioridad) */}
      {tenantStatus === 'suspendido' && (
        <div className="banner-suspended">
          ⚠️ Cuenta suspendida por pagos: modo solo lectura. Contacta soporte para regularizar.
        </div>
      )}
      <header className="header">
        <div className="header-left">
          {/* Botón Hamburger (visible solo en mobile) */}
          <button 
            className="icon-btn hamburger-btn"
            onClick={onMenuClick}
            aria-label="Abrir menú"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>

          <span className="small muted">Tenant:</span>
          <span className="bold">demo-tenant</span>
          {tenantStatus === 'suspendido' && <span className="badge badge-critical">Suspendido</span>}
        </div>
        <div className="header-right">
          <ThemeToggle />
          <button className="btn btn-ghost" onClick={onLogout}>Salir</button>
        </div>
      </header>
    </>
  )
}
