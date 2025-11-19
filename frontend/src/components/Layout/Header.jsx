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
        <div style={{
          background: '#7f1d1d',
          color: '#fff',
          padding: '12px 16px',
          textAlign: 'center',
          fontWeight: '600',
          borderBottom: '2px solid #991b1b'
        }}>
          ⚠️ Cuenta suspendida por pagos: modo solo lectura. Contacta soporte para regularizar.
        </div>
      )}
      <header className="header">
        <div className="header-left">
          {/* Botón Hamburger (visible solo en mobile) */}
          <button 
            className="btn icon-btn hamburger-btn" 
            onClick={onMenuClick}
            aria-label="Abrir menú"
            style={{ marginRight: 8, padding: 6 }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>

          <strong>Tenant:</strong> demo-tenant
          {tenantStatus === 'suspendido' && <span className="badge badge-danger">Suspendido</span>}
        </div>
        <div className="header-right">
          <ThemeToggle />
          <button className="btn" onClick={onLogout}>Salir</button>
        </div>
      </header>
    </>
  )
}