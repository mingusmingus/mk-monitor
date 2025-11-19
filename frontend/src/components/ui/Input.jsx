import React, { forwardRef } from 'react'

/**
 * Input (low-level)
 * - Usa estilos base .input de theme.css
 * - Soporta error (borde danger) y loading (spinner al final con SVG)
 */
function Spinner({ size = 16 }) {
  const s = size
  return (
    <svg
      width={s}
      height={s}
      viewBox="0 0 24 24"
      role="img"
      aria-label="Cargando"
      style={{ display: 'inline-block' }}
    >
      <circle cx="12" cy="12" r="10" stroke="color-mix(in oklab, var(--text-muted) 45%, transparent)" strokeWidth="3" fill="none" />
      <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="3" fill="none">
        <animateTransform attributeName="transform" type="rotate" dur="0.8s" from="0 12 12" to="360 12 12" repeatCount="indefinite" />
      </path>
    </svg>
  )
}

const Input = forwardRef(function Input(
  { error = false, loading = false, className = '', style, endAdornment = null, ...props },
  ref
) {
  const showAdornment = loading || endAdornment
  return (
    <div className="row" style={{ position: 'relative', width: '100%' }}>
      <input
        ref={ref}
        className={['input', className].filter(Boolean).join(' ')}
        aria-invalid={!!error || undefined}
        style={{
          width: '100%',
          paddingRight: showAdornment ? 36 : undefined,
          borderColor: error ? 'var(--danger)' : undefined,
          ...style
        }}
        {...props}
      />
      {showAdornment && (
        <div
          style={{
            position: 'absolute',
            right: 8,
            top: '50%',
            transform: 'translateY(-50%)',
            display: 'grid',
            placeItems: 'center'
          }}
        >
          {loading ? <Spinner /> : endAdornment}
        </div>
      )}
    </div>
  )
})

export default Input
/* Ejemplo de uso (solo documentación, no incluir en build)
// import Input from '@/components/ui/Input.jsx'
// function Example() {
//   const [v, setV] = React.useState('')
//   return <Input placeholder="Escribe aquí" value={v} onChange={(e) => setV(e.target.value)} />
// }
*/