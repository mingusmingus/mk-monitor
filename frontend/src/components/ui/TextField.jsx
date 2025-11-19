import React, { useId } from 'react'
import Input from './Input.jsx'

/**
 * TextField
 * - label, hint (arriba opcional), helperText (debajo), error (string o boolean)
 * - Accesible: id/label htmlFor, aria-invalid, aria-describedby (helper/error)
 */
export default function TextField({
  id,
  label,
  hint,
  helperText,
  error = false,
  required = false,
  className = '',
  inputProps = {},
  style,
  ...props
}) {
  const autoId = useId()
  const inputId = id || `tf-${autoId}`
  const helperId = `${inputId}-helper`
  const errorId = `${inputId}-error`

  const describedByIds = []
  if (helperText && !error) describedByIds.push(helperId)
  if (error) describedByIds.push(errorId)

  const showErrorText = typeof error === 'string' ? error : error === true

  return (
    <div className={className} style={style}>
      {label && (
        <label htmlFor={inputId} className="small" style={{ display: 'block', marginBottom: 6 }}>
          {label} {required && <span aria-hidden="true" style={{ color: 'var(--danger)' }}>*</span>}
        </label>
      )}
      {hint && <div className="small" style={{ marginBottom: 6, color: 'var(--text-muted)' }}>{hint}</div>}

      <Input
        id={inputId}
        aria-describedby={describedByIds.length ? describedByIds.join(' ') : undefined}
        error={!!error}
        {...props}
        {...inputProps}
      />

      {/* Mensajes debajo */}
      {!error && helperText && (
        <div id={helperId} className="small" style={{ marginTop: 6, color: 'var(--text-muted)' }}>
          {helperText}
        </div>
      )}
      {showErrorText && (
        <div id={errorId} className="small" style={{ marginTop: 6, color: 'var(--danger)' }} role="alert">
          {typeof error === 'string' ? error : 'Error'}
        </div>
      )}
    </div>
  )
}

/* Ejemplo de uso (solo documentación, no incluir en build)
// import TextField from '@/components/ui/TextField.jsx'
// function Example() {
//   const [email, setEmail] = React.useState('')
//   return (
//     <TextField
//       label="Email"
//       placeholder="email@dominio.com"
//       helperText="Usa tu correo corporativo"
//       value={email}
//       onChange={(e) => setEmail(e.target.value)}
//       error={!email.includes('@') && email ? 'Email inválido' : false}
//       required
//     />
//   )
// }
*/