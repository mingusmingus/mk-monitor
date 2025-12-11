import React, { useCallback, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Input from '../components/ui/Input.jsx'
import Button from '../components/ui/Button.jsx'
import ThemeToggle from '../components/Layout/ThemeToggle.jsx'
import { register as registerApi } from '../api/registerApi.js'

/**
 * SignupPage (Rediseñada)
 *
 * Página de registro de nuevos usuarios.
 * Comparte estilos con la página de Login para consistencia visual.
 */
export default function SignupPage() {
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

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

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault()
      if (loading) return

      setError('')
      setSuccess('')

      const trimmedEmail = email.trim()
      const trimmedFullName = fullName.trim()

      if (!trimmedEmail || !/.+@.+\..+/.test(trimmedEmail)) {
        setError('El email no tiene un formato válido.')
        return
      }

      if (password.length < 8) {
        setError('La contraseña debe tener al menos 8 caracteres.')
        return
      }

      if (password !== confirmPassword) {
        setError('Las contraseñas no coinciden.')
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
          setSuccess('Cuenta creada. Redirigiendo...')
          setError('')
          setTimeout(() => {
            navigate('/login', { state: { prefillEmail: trimmedEmail } })
          }, 1500)
        } else if (status === 409) {
          setError('Este email ya está registrado.')
        } else {
          setError('Ocurrió un error al registrar tu cuenta.')
        }
      } catch (err) {
        if (err?.response?.status === 409) {
          setError('Este email ya está registrado.')
        } else {
          setError('Ocurrió un error al registrar tu cuenta.')
        }
      } finally {
        setLoading(false)
      }
    },
    [email, password, confirmPassword, fullName, loading, navigate]
  )

  return (
    <div className="auth-page">
      {/* Decoración */}
      <div className="auth-orb" style={{ top: 0, left: 0 }}></div>
      <div className="auth-orb" style={{ bottom: 0, right: 0, animationDelay: '-10s', background: 'radial-gradient(circle, var(--color-accent-secondary) 0%, transparent 70%)' }}></div>

      {/* Control de Tema */}
      <div style={{ position: 'absolute', top: 20, right: 20, zIndex: 20 }}>
        <ThemeToggle />
      </div>

      <div className="auth-card fade-in">
        <header className="auth-header">
            <div className="auth-logo">M</div>
            <h1 className="auth-title">Crear Cuenta</h1>
            <p className="auth-subtitle">Registra tu organización y comienza gratis</p>
        </header>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <Input
            label="Nombre Completo"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            placeholder="Juan Pérez"
          />

          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={!emailValid && email ? 'Email inválido' : undefined}
            required
            placeholder="usuario@empresa.com"
          />

          <Input
            label="Contraseña"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="Mínimo 8 caracteres"
          />

          <Input
            label="Confirmar Contraseña"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            placeholder="Repite tu contraseña"
          />

          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          {success && (
            <div style={{ color: 'var(--color-accent-secondary)', textAlign: 'center', fontSize: '13px', fontWeight: 600 }}>
              {success}
            </div>
          )}

          <Button
            type="submit"
            variant="primary"
            loading={loading}
            disabled={!canSubmit}
            fullWidth
            size="lg"
            style={{ marginTop: '8px' }}
          >
            Registrarse
          </Button>

          <div style={{ textAlign: 'center', fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '16px' }}>
            ¿Ya tienes cuenta? <a href="/login" style={{ color: 'var(--color-accent-primary)', fontWeight: 600, textDecoration: 'none' }}>Inicia sesión</a>
          </div>
        </form>
      </div>
    </div>
  )
}
