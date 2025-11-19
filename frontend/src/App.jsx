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
import useAuth from './hooks/useAuth';
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

// Requiere un token para permitir acceso. TODO: refinar por roles.
function RequireAuth({ children }) {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) return <Navigate to="/login" replace state={{ from: location }} />
  return children
}

export default function App() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  // Listener global para eventos de logout disparados por el interceptor (401)
  useEffect(() => {
    function handleLogout(e) {
      const reason = e.detail?.reason
      logout()
      if (window.location.pathname !== '/login') {
        navigate('/login', { replace: true, state: { reason } })
        // Mensaje simple; idealmente reemplazar por sistema de toast centralizado
        alert('Tu sesión expiró.')
      }
    }
    window.addEventListener('auth:logout', handleLogout)
    return () => window.removeEventListener('auth:logout', handleLogout)
  }, [logout, navigate])

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {/* Nueva ruta pública de registro */}
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
  )
}