import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import useAuth from '../hooks/useAuth.js'
import Input from '../components/ui/Input.jsx'
import Button from '../components/ui/Button.jsx'
import ThemeToggle from '../components/Layout/ThemeToggle.jsx'

/**
 * LoginPage (Rediseñado)
 *
 * Pantalla de inicio de sesión con diseño moderno y minimalista.
 * Utiliza CSS de src/styles/pages/login.css
 */
export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/'

  const onLoggedIn = useCallback(() => {
    navigate(from, { replace: true })
  }, [from, navigate])

  return (
    <div className="auth-page">
      {/* Decoración de fondo */}
      <div className="auth-orb" style={{ top: 0, left: 0 }}></div>
      <div className="auth-orb" style={{ bottom: 0, right: 0, animationDelay: '-10s', background: 'radial-gradient(circle, var(--color-accent-secondary) 0%, transparent 70%)' }}></div>

      {/* Control de tema */}
      <div style={{ position: 'absolute', top: 20, right: 20, zIndex: 20 }}>
        <ThemeToggle />
      </div>

      <div className="auth-card fade-in">
        <header className="auth-header">
            <div className="auth-logo">M</div>
            <h1 className="auth-title">Bienvenido de nuevo</h1>
            <p className="auth-subtitle">Ingresa a tu cuenta para gestionar tus equipos</p>
        </header>

        <LoginForm onSuccess={onLoggedIn} />
      </div>
    </div>
  )
}

function LoginForm({ onSuccess }) {
  const { login } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email || !password) return

    setSubmitting(true)
    setError('')

    try {
        const ok = await login(email, password)
        if (ok) {
            onSuccess?.()
        } else {
            setError('Credenciales incorrectas')
        }
    } catch (err) {
        setError('Ocurrió un error. Intenta nuevamente.')
    } finally {
        setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <Input
        label="Correo electrónico"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        placeholder="ej. usuario@empresa.com"
      />

      <div style={{ position: 'relative' }}>
        <Input
            label="Contraseña"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="••••••••"
        />
        <div style={{ position: 'absolute', right: 0, top: '100%', marginTop: '4px' }}>
            <a href="#" style={{ fontSize: '12px', color: 'var(--color-accent-primary)', textDecoration: 'none', fontWeight: 500 }}>
                ¿Olvidaste tu contraseña?
            </a>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
        <input
            type="checkbox"
            id="remember"
            className="custom-checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
        />
        <label htmlFor="remember" style={{ fontSize: '13px', color: 'var(--color-text-secondary)', cursor: 'pointer', userSelect: 'none' }}>
            Recordar mi dispositivo
        </label>
      </div>

      {error && (
        <div className="auth-error">
            {error}
        </div>
      )}

      <Button
        type="submit"
        variant="primary"
        loading={submitting}
        fullWidth
        size="lg"
        style={{ marginTop: '8px' }}
      >
        Iniciar Sesión
      </Button>

      <div style={{ textAlign: 'center', fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '16px' }}>
        ¿No tienes una cuenta? <a href="/signup" style={{ color: 'var(--color-accent-primary)', fontWeight: 600, textDecoration: 'none' }}>Regístrate</a>
      </div>
    </form>
  )
}
