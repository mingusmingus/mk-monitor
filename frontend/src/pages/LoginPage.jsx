import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import useAuth from '../hooks/useAuth.js'
import TextField from '../components/ui/TextField.jsx'
import PasswordField from '../components/ui/PasswordField.jsx'
import Button from '../components/ui/Button.jsx'

// Nueva pantalla de Login con estilo glassmorphism y manejo fino de errores.
export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/'

  const onLoggedIn = useCallback(() => {
    // Mantener navegación pos-login igual que ahora
    navigate(from, { replace: true })
  }, [from, navigate])

  return (
    <div
      className="centered"
      style={{
        minHeight: '100vh',
        // Gradiente suave usando tokens
        background: `radial-gradient(1200px 600px at 20% -10%, var(--accent-start) 0%, transparent 50%), radial-gradient(1200px 600px at 120% 110%, var(--accent-end) 0%, transparent 50%), linear-gradient(135deg, color-mix(in oklab, var(--accent-start) 18%, var(--bg)), color-mix(in oklab, var(--accent-end) 18%, var(--bg)))`,
        transition: 'background 250ms ease'
      }}
    >
      <div
        className="glass"
        style={{
          width: '100%',
          maxWidth: 420,
          padding: 24,
          borderRadius: 18,
          boxShadow: 'var(--shadow-strong)',
          transform: 'translateZ(0)',
          backdropFilter: 'blur(16px) saturate(140%)',
          background: 'color-mix(in oklab, rgba(15,23,42,0.82) 70%, rgba(15,23,42,0.92) 30%)',
          color: 'white',
          border: '1px solid rgba(148,163,184,0.35)',
          position: 'relative',
          overflow: 'hidden',
          transition: 'transform 150ms ease, box-shadow 200ms ease'
        }}
      >
        <header className="col" style={{ gap: 6, marginBottom: 14 }}>
          <h1 style={{ fontSize: 32, lineHeight: 1.2, margin: 0, fontWeight: 600 }}>Bienvenido</h1>
          <p className="muted" style={{ margin: 0 }}>Inicia sesión para continuar</p>
        </header>

        <LoginForm onSuccess={onLoggedIn} />
      </div>
    </div>
  )
}

function getErrorMessage(err) {
  const status = err?.response?.status
  const code = err?.response?.data?.error

  if (status === 409 && code === 'email_taken') {
    return { message: 'Este email ya está registrado.', target: 'email' }
  }
  if (status === 400 && code === 'invalid_email') {
    return { message: 'El email no tiene un formato válido.', target: 'email' }
  }
  if (status === 400 && code === 'email_required') {
    return { message: 'El email es obligatorio.', target: 'email' }
  }
  if (status === 400 && code === 'weak_password') {
    return { message: 'La contraseña debe tener al menos 8 caracteres.', target: 'password' }
  }
  if (status === 429) {
    return { message: 'Demasiados intentos. Intenta nuevamente más tarde.', target: 'form' }
  }

  // Network o 5xx
  if (!status || status >= 500) {
    return { message: 'Error interno. Reintenta en unos segundos.', target: 'form' }
  }

  return { message: 'Ocurrió un error al registrar tu cuenta.', target: 'form' }
}

function LoginForm({ onSuccess }) {
  const { login } = useAuth()
  const location = useLocation()

  const emailRef = useRef(null)
  const passwordRef = useRef(null)
  const submitRef = useRef(null)

  // Prefill: si venimos de signup con state.prefillEmail, usarlo; si no, usar remember_email
  const [email, setEmail] = useState(() => {
    const prefill = location.state?.prefillEmail
    if (prefill) return prefill
    return localStorage.getItem('remember_email') || ''
  })
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(() => !!localStorage.getItem('remember_email'))

  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')
  const [fieldErrors, setFieldErrors] = useState({ email: '', password: '' })

  const emailValid = useMemo(() => !email || /.+@.+\..+/.test(email), [email])
  const canSubmit = useMemo(
    () => email && password && emailValid && !submitting,
    [email, password, emailValid, submitting]
  )

  useEffect(() => {
    // Limpiar errores por cambios
    if (formError) setFormError('')
    if (fieldErrors.email && emailValid) setFieldErrors((e) => ({ ...e, email: '' }))
  }, [email, password, emailValid]) // eslint-disable-line react-hooks/exhaustive-deps

  const focusTarget = useCallback((target) => {
    if (target === 'password' && passwordRef.current) passwordRef.current.focus()
    else if (target === 'email' && emailRef.current) emailRef.current.focus()
    else if (submitRef.current) submitRef.current.focus()
  }, [])

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault()
    if (!emailValid) {
      setFieldErrors((e) => ({ ...e, email: 'Email inválido' }))
      focusTarget('email')
      return
    }

    setSubmitting(true)
    setFormError('')
    setFieldErrors({ email: '', password: '' })
    try {
      const ok = await login(email, password)
      if (ok) {
        await new Promise(resolve => setTimeout(resolve, 0))
        onSuccess?.()
        return
      }
    } catch (err) {
      const { message, target } = getErrorMessage(err)
      // Para 401, marcar password como error
      if (err?.response?.status === 401) {
        setFieldErrors((e) => ({ ...e, password: 'Verifica tu contraseña' }))
      }
      setFormError(message)
      // Gestión de focus
      focusTarget(target)
    } finally {
      setSubmitting(false)
    }
  }, [email, password, remember, login, onSuccess, emailValid, focusTarget])

  return (
    <form
      onSubmit={handleSubmit}
      className="col"
      style={{ gap: 12 }}
      aria-describedby={formError ? 'login-error' : undefined}
    >
      <TextField
        label="Email"
        type="email"
        placeholder="email@dominio.com"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={fieldErrors.email}
        inputProps={{
          ref: emailRef,
          onKeyDown: (e) => {
            if (e.key === 'Enter' && canSubmit) handleSubmit(e)
          }
        }}
        required
      />

      <PasswordField
        label="Contraseña"
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={fieldErrors.password}
        inputProps={{ ref: passwordRef }}
        required
      />

      <div className="row space-between" style={{ marginTop: 4 }}>
        <label className="row" style={{ gap: 8, cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            aria-label="Recordarme"
          />
          <span className="small">Recordarme</span>
        </label>
        <a
          href="#"
          className="small"
          style={{ textDecoration: 'none', color: 'var(--text-muted)' }}
          onFocus={(e) => (e.currentTarget.style.textDecoration = 'underline')}
          onBlur={(e) => (e.currentTarget.style.textDecoration = 'none')}
          onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
          onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
        >
          ¿Olvidaste tu contraseña?
        </a>
      </div>

      {/* Enlace a registro */}
      <div className="row" style={{ justifyContent: 'flex-end', marginTop: 4 }}>
        <a
          href="/signup"
          className="small"
          style={{ textDecoration: 'none', color: 'var(--text-muted)' }}
          onFocus={(e) => (e.currentTarget.style.textDecoration = 'underline')}
          onBlur={(e) => (e.currentTarget.style.textDecoration = 'none')}
          onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
          onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
        >
          ¿No tienes cuenta? Regístrate
        </a>
      </div>

      {formError && (
        <div id="login-error" className="small" role="alert" style={{ color: 'var(--danger)', marginTop: 4 }}>
          {formError}
        </div>
      )}

      <Button
        ref={submitRef}
        type="submit"
        variant="primary"
        loading={submitting}
        disabled={!canSubmit}
        fullWidth
        style={{ marginTop: 4 }}
        aria-label="Iniciar sesión"
      >
        Iniciar sesión
      </Button>
    </form>
  )
}