import React, { useId, useState, useMemo } from 'react'
import Input from './Input.jsx'
import Button from './Button.jsx'

/**
 * PasswordField
 * - TextField especializado con toggle show/hide
 * - Accesible: aria-controls al input, aria-pressed en el toggle
 */
export default function PasswordField({
  id,
  label = 'Password',
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
  const inputId = id || `pf-${autoId}`
  const [show, setShow] = useState(false)
  const helperId = `${inputId}-helper`
  const errorId = `${inputId}-error`

  const describedBy = useMemo(() => {
    const ids = []
    if (helperText && !error) ids.push(helperId)
    if (error) ids.push(errorId)
    return ids.join(' ')
  }, [helperText, error, helperId, errorId])

  const showErrorText = typeof error === 'string' ? error : error === true

  return (
    <div className={className} style={style}>
      {label && (
        <label htmlFor={inputId} className="small" style={{ display: 'block', marginBottom: 6 }}>
          {label} {required && <span aria-hidden="true" style={{ color: 'var(--danger)' }}>*</span>}
        </label>
      )}
      {hint && <div className="small" style={{ marginBottom: 6, color: 'var(--text-muted)' }}>{hint}</div>}

      <div style={{ position: 'relative', width: '100%' }}>
        <Input
          id={inputId}
          type={show ? 'text' : 'password'}
          aria-describedby={describedBy || undefined}
          error={!!error}
          style={{ paddingRight: 44 }}
          {...props}
          {...inputProps}
        />
        <Button
          type="button"
          variant="ghost"
          size="sm"
          aria-controls={inputId}
          aria-pressed={show}
          onClick={() => setShow((s) => !s)}
          style={{
            position: 'absolute',
            right: 6,
            top: '50%',
            transform: 'translateY(-50%)',
            minWidth: 0,
            padding: '4px 8px'
          }}
          title={show ? 'Ocultar contraseña' : 'Mostrar contraseña'}
        >
          {show ? 'Ocultar' : 'Mostrar'}
        </Button>
      </div>

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
// import PasswordField from '@/components/ui/PasswordField.jsx'
// function Example() {
//   const [pwd, setPwd] = React.useState('')
//   return (
//     <PasswordField
//       label="Contraseña"
//       placeholder="••••••••"
//       value={pwd}
//       onChange={(e) => setPwd(e.target.value)}
//       helperText="Mínimo 8 caracteres"
//       error={pwd && pwd.length < 8 ? 'Muy corta' : false}
//       required
//     />
//   )
// }
*/