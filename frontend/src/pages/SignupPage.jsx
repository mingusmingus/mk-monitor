import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import TextField from '../components/ui/TextField.jsx'
import PasswordField from '../components/ui/PasswordField.jsx'
import Button from '../components/ui/Button.jsx'
import { register as registerApi } from '../api/registerApi.js'

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

// Pantalla de registro simple: crea Tenant + Usuario admin.
export default function SignupPage() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const emailRef = useRef(null)
  const passwordRef = useRef(null)
  const confirmPasswordRef = useRef(null)
  const fullNameRef = useRef(null)

  const emailValid = useMemo(() => !email || /.+@.+\..+/.test(email), [email])

  const canSubmit = useMemo(
    () =>
      email.trim() !== '' &&
      password &&
      confirmPassword &&
      fullName.trim() !== '' &&
      emailValid &&
      !loading,
    [email, password, confirmPassword, fullName, emailValid, loading]
  )

  const focusFirstErrorField = useCallback((field) => {
    if (field === 'email' && emailRef.current) emailRef.current.focus()
    else if (field === 'password' && passwordRef.current) passwordRef.current.focus()
    else if (field === 'confirmPassword' && confirmPasswordRef.current) confirmPasswordRef.current.focus()
    else if (field === 'fullName' && fullNameRef.current) fullNameRef.current.focus()
  }, [])

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault()
      if (loading) return

      setError('')
      setSuccess('')

      const trimmedEmail = email.trim()
      const trimmedFullName = fullName.trim()

      if (!trimmedEmail) {
        setError('El email es obligatorio.')
        focusFirstErrorField('email')
        return
      }

      if (!/.+@.+\..+/.test(trimmedEmail)) {
        setError('El email no tiene un formato válido.')
        focusFirstErrorField('email')
        return
      }

      if (!trimmedFullName) {
        setError('El nombre completo es obligatorio.')
        focusFirstErrorField('fullName')
        return
      }

      if (!password || password.length < 8) {
        setError('La contraseña debe tener al menos 8 caracteres.')
        focusFirstErrorField('password')
        return
      }

      if (password !== confirmPassword) {
        setError('Las contraseñas no coinciden.')
        focusFirstErrorField('confirmPassword')
        return
      }

      setLoading(true)

      try {
        const response = await registerApi({
          email: trimmedEmail,
          password,
          full_name: trimmedFullName
        })

        const status = response?.status

        if (status === 201) {
          setSuccess('Cuenta creada. Ahora inicia sesión.')
          setError('')
          setPassword('')
          setConfirmPassword('')

          setTimeout(() => {
            navigate('/login', { state: { prefillEmail: trimmedEmail } })
          }, 1500)
        } else if (status === 409) {
          setError('Este email ya está registrado.')
          focusFirstErrorField('email')
        } else if (status === 429) {
          setError('Demasiados solicitudes. Intenta más tarde.')
        } else {
          setError('Ocurrió un error al registrar tu cuenta.')
        }
      } catch (err) {
        const status = err?.response?.status
        if (status === 409) {
          setError('Este email ya está registrado.')
          focusFirstErrorField('email')
        } else if (status === 429) {
          setError('Demasiados solicitudes. Intenta más tarde.')
        } else {
          setError('Ocurrió un error al registrar tu cuenta.')
        }
      } finally {
        setLoading(false)
      }
    },
    [email, password, confirmPassword, fullName, loading, focusFirstErrorField, navigate]
  )

  return (
    <div className="centered" style={{ minHeight: '100vh' }}>
      <div
        className="glass"
        style={{
          width: '100%',
          maxWidth: 420,
          padding: 24,
          borderRadius: 18,
          boxShadow: 'var(--shadow-strong)'
        }}
      >
        <header className="col" style={{ gap: 6, marginBottom: 14 }}>
          <h1 style={{ fontSize: 28, lineHeight: 1.2, margin: 0, fontWeight: 600 }}>Crear cuenta</h1>
          <p className="muted" style={{ margin: 0 }}>Crea tu tenant y el usuario administrador.</p>
        </header>

        <form onSubmit={handleSubmit} className="col" style={{ gap: 12 }}>
          <TextField
            label="Email"
            type="email"
            placeholder="email@dominio.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            inputRef={emailRef}
            aria-invalid={!!error && !emailValid}
            error={!emailValid && email ? 'El email no tiene un formato válido.' : ''}
            required
          />

          <PasswordField
            label="Contraseña"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            inputRef={passwordRef}
            aria-invalid={!!error && (password.length < 8)}
            error={password && password.length < 8 ? 'La contraseña debe tener al menos 8 caracteres.' : ''}
            required
          />

          <PasswordField
            label="Confirmar contraseña"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            inputRef={confirmPasswordRef}
            aria-invalid={!!error && password !== confirmPassword}
            error={
              confirmPassword && password !== confirmPassword
                ? 'Las contraseñas no coinciden.'
                : ''
            }
            required
          />

          <TextField
            label="Nombre completo"
            type="text"
            placeholder="Nombre y apellidos"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            inputRef={fullNameRef}
            aria-invalid={!!error && !fullName.trim()}
            error={''}
            required
          />
          {error && (
            <div className="small" role="alert" style={{ color: 'var(--danger)', marginTop: 4 }}>
              {error}
            </div>
          )}

          {success && (
            <div className="small" role="status" style={{ color: 'var(--success)', marginTop: 4 }}>
              {success}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            loading={loading}
            disabled={!canSubmit || loading}
            fullWidth
          >
            {loading ? 'Creando cuenta…' : 'Crear cuenta'}
          </Button>

          <div className="row" style={{ justifyContent: 'flex-end', marginTop: 4 }}>
            <a
              href="/login"
              className="small"
              style={{ textDecoration: 'none', color: 'var(--text-muted)' }}
            >
              ¿Ya tienes cuenta? Inicia sesión
            </a>
          </div>
        </form>
      </div>
    </div>
  )
}