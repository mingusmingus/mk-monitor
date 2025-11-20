import React, { useEffect, useState } from 'react'
import { Routes, Route, Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import DevicesPage from './pages/DevicesPage.jsx'
import DeviceDetailPage from './pages/DeviceDetailPage.jsx'
import AlertsPage from './pages/AlertsPage.jsx'
import SubscriptionPage from './pages/SubscriptionPage.jsx'
import NocActivityPage from './pages/NocActivityPage.jsx'
import Sidebar from './components/Layout/Sidebar.jsx'
import Header from './components/Layout/Header.jsx'
import useAuth from './hooks/useAuth'
import SignupPage from './pages/SignupPage.jsx'

// Envoltura de layout para páginas protegidas
function ProtectedLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  return (
    <div className="app">
      <Header onMenuClick={() => setMobileMenuOpen(true)} />
      <div className="app-body">
        <Sidebar isOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

// Requiere un token para permitir acceso.
function RequireAuth({ children }) {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) return <Navigate to="/login" replace state={{ from: location }} />
  return children
}

// Modal de sesión expirada
function SessionExpiredModal({ onConfirm }) {
  return (
    <div className="modal-overlay">
      <div 
        className="modal" 
        role="dialog" 
        aria-modal="true"
        aria-labelledby="session-expired-title"
        aria-describedby="session-expired-description"
      >
        <h2 id="session-expired-title">Sesión expirada</h2>
        <p id="session-expired-description">Tu sesión ha expirado. Por favor inicia sesión nuevamente.</p>
        <div className="row" style={{ justifyContent: 'flex-end', gap: 12 }}>
          <button className="btn" onClick={onConfirm} aria-label="Iniciar sesión nuevamente">
            Iniciar sesión
          </button>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const navigate = useNavigate()
  const { logout, expiredSession } = useAuth()

  // Listener legacy (otros motivos de logout forzado)
  useEffect(() => {
    function handleLogout(e) {
      const reason = e.detail?.reason
      logout()
      if (window.location.pathname !== '/login') {
        navigate('/login', { replace: true, state: { reason } })
      }
    }
    window.addEventListener('auth:logout', handleLogout)
    return () => window.removeEventListener('auth:logout', handleLogout)
  }, [logout, navigate])

  const onExpiredConfirm = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      {expiredSession && <SessionExpiredModal onConfirm={onExpiredConfirm} />}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route
          element={
            <RequireAuth>
              <ProtectedLayout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/devices" element={<DevicesPage />} />
          <Route path="/devices/:deviceId" element={<DeviceDetailPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/subscription" element={<SubscriptionPage />} />
          <Route path="/noc" element={<NocActivityPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}