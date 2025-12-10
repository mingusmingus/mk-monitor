import React, { useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'

// Icons (Feather Icons inspired SVGs)
const Icons = {
  Dashboard: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>,
  Devices: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>,
  Alerts: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>,
  Noc: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>,
  Subscription: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>,
  Logout: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
}

export default function Sidebar({ isOpen, onClose }) {
  const items = [
    { to: '/', label: 'Dashboard', icon: Icons.Dashboard },
    { to: '/devices', label: 'Equipos', icon: Icons.Devices },
    { to: '/alerts', label: 'Alertas', icon: Icons.Alerts },
    { to: '/noc', label: 'NOC', icon: Icons.Noc },
    { to: '/subscription', label: 'Suscripción', icon: Icons.Subscription }
  ]

  // Close on ESC
  useEffect(() => {
    const handleEsc = (e) => {
      if (isOpen && e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isOpen, onClose])

  return (
    <>
      {/* Mobile Backdrop */}
      <div 
        className={`sidebar-backdrop ${isOpen ? 'visible' : ''}`} 
        onClick={onClose}
        aria-hidden="true"
        style={{
            position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)',
            backdropFilter: 'blur(4px)', zIndex: 90, opacity: isOpen ? 1 : 0,
            pointerEvents: isOpen ? 'auto' : 'none', transition: 'opacity 0.3s'
        }}
      />
      
      <aside
        className={`sidebar ${isOpen ? 'open' : ''}`}
        style={{ zIndex: 100 }}
      >
        <div className="sidebar-brand" style={{ marginBottom: 0 }}>
          <span style={{ color: 'var(--color-accent-primary)' }}>mk</span>-monitor
        </div>

        <nav className="sidebar-nav">
            <div style={{ textTransform: 'uppercase', fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 600, padding: '0 12px 8px' }}>
                Menu
            </div>
          {items.map((i) => (
            <NavLink
              key={i.to}
              to={i.to}
              end={i.to === '/'}
              onClick={onClose}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              {i.icon && <i.icon />}
              {i.label}
            </NavLink>
          ))}
        </nav>

        {/* Footer actions for mobile specifically if needed, otherwise handled in header */}
      </aside>
    </>
  )
}
