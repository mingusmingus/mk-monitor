import React, { useEffect } from 'react'
import { NavLink } from 'react-router-dom'

// Sidebar de navegación responsive.
export default function Sidebar({ isOpen, onClose }) {
  const items = [
    { to: '/', label: 'Dashboard' },
    { to: '/devices', label: 'Equipos' },
    { to: '/alerts', label: 'Alertas' },
    { to: '/noc', label: 'NOC' },
    { to: '/subscription', label: 'Suscripción' }
  ]

  // Cerrar con ESC
  useEffect(() => {
    const handleEsc = (e) => {
      if (isOpen && e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isOpen, onClose])

  return (
    <>
      {/* Backdrop oscuro para mobile */}
      <div 
        className={`sidebar-backdrop ${isOpen ? 'visible' : ''}`} 
        onClick={onClose}
        aria-hidden="true"
      />
      
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="row space-between" style={{ marginBottom: 'var(--spacing-3)' }}>
          <div className="sidebar-brand" style={{ margin: 0 }}>mk-monitor</div>
          {/* Botón cerrar solo visible en mobile dentro del drawer */}
          <button 
            className="btn icon-btn close-sidebar-btn" 
            onClick={onClose}
            aria-label="Cerrar menú"
          >
            ✕
          </button>
        </div>

        <nav className="sidebar-nav" role="navigation" aria-label="Navegación principal">
          {items.map((i) => (
            <NavLink
              key={i.to}
              to={i.to}
              end={i.to === '/'}
              onClick={onClose} // Cierra el drawer al navegar
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              {i.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}
