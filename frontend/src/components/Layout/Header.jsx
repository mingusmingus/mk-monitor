import React from 'react'
import { useNavigate } from 'react-router-dom'
import ThemeToggle from './ThemeToggle.jsx'
import useAuth from '../../hooks/useAuth.js'

/**
 * Header Global.
 * Muestra el banner de estado del tenant (si está suspendido),
 * controles de tema, perfil de usuario y botón de cierre de sesión.
 *
 * Props:
 * - onMenuClick: Function (Callback para abrir menú en móvil).
 */
export default function Header({ onMenuClick }) {
  const { tenantStatus, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      {/* Banner de Suspensión */}
      {tenantStatus === 'suspendido' && (
        <div style={{ backgroundColor: 'var(--color-accent-danger)', color: 'white', padding: '8px 16px', textAlign: 'center', fontSize: '12px', fontWeight: 600 }}>
          [AVISO] Cuenta suspendida por pagos: modo solo lectura. Contacte a soporte para regularizar.
        </div>
      )}

      <header className="header">
        <div className="header-left">
          {/* Botón Hamburguesa (Móvil) */}
          <button 
            className="icon-btn hamburger-btn"
            onClick={onMenuClick}
            aria-label="Abrir menú"
            style={{
                background: 'transparent', border: 'none', cursor: 'pointer', padding: 8,
                color: 'var(--color-text-primary)', display: 'none' // Gestionado vía media queries CSS
            }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>

          {/* Área de Título / Breadcrumb */}
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Tenant: demo-tenant
            </span>
            {tenantStatus === 'suspendido' &&
                <span style={{ fontSize: '10px', color: 'var(--color-accent-danger)', fontWeight: 600 }}>
                    SUSPENDIDO
                </span>
            }
          </div>
        </div>

        <div className="header-right">
          <ThemeToggle />

          <div style={{ width: 1, height: 24, background: 'var(--color-border)' }}></div>

          <div className="user-profile" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--color-bg-tertiary)', display: 'grid', placeItems: 'center', fontSize: '12px', fontWeight: 600 }}>
                DT
            </div>
            <button
                onClick={onLogout}
                style={{
                    background: 'transparent', border: 'none', cursor: 'pointer',
                    color: 'var(--color-text-secondary)', fontSize: '13px', fontWeight: 500
                }}
            >
                Salir
            </button>
          </div>
        </div>
      </header>
    </>
  )
}
