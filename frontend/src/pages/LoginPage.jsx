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
    <div className="auth-bg centered">
      <div className="glass-panel fade-in auth-container">
        <header className="col gap-2 mb-4">
          <h1 className="h1 text-center">Bienvenido</h1>
          <p className="muted text-center small">Inicia sesión para continuar</p>
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
      className="col gap-3"
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

      <div className="row justify-between mt-1">
        <label className="row gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            aria-label="Recordarme"
          />
          <span className="small muted">Recordarme</span>
        </label>
        <a
          href="#"
          className="small muted no-decoration"
        >
          ¿Olvidaste tu contraseña?
        </a>
      </div>

      <div className="row justify-end mt-1">
        <a
          href="/signup"
          className="small muted no-decoration"
        >
          ¿No tienes cuenta? <span className="bold text-primary">Regístrate</span>
        </a>
      </div>

      {formError && (
        <div id="login-error" className="small mt-1 text-danger" role="alert">
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
        className="mt-2"
        aria-label="Iniciar sesión"
      >
        Iniciar sesión
      </Button>
    </form>
  )
}
