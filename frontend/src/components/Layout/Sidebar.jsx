import React from 'react'
import { NavLink } from 'react-router-dom'

// Sidebar de navegación del dashboard (simple, profesional).
export default function Sidebar() {
  const items = [
    { to: '/', label: 'Dashboard' },
    { to: '/devices', label: 'Equipos' },
    { to: '/alerts', label: 'Alertas' },
    { to: '/noc', label: 'NOC' },
    { to: '/subscription', label: 'Suscripción' }
  ]
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">mk-monitor</div>
      <nav className="sidebar-nav">
        {items.map((i) => (
          <NavLink
            key={i.to}
            to={i.to}
            end={i.to === '/'}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            {i.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
