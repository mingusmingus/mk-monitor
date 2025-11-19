import React, { forwardRef } from 'react'

/**
 * Button
 * - Variantes: primary, secondary, ghost
 * - Tamaños: sm | md | lg
 * - Estados: hover (hereda .btn), focus-visible (navegador), disabled, loading (spinner SVG)
 * - fullWidth: ancho 100%
 * Usa tokens de theme.css (var(--primary), var(--border), var(--text), etc.)
 */
const sizeStyles = {
  sm: { padding: '6px 10px', fontSize: 'var(--font-size-sm)' },
  md: { padding: '8px 12px', fontSize: 'var(--font-size-base)' },
  lg: { padding: '10px 14px', fontSize: 'var(--font-size-lg)' }
}

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

const Button = forwardRef(function Button(
  {
    as: As = 'button',
    variant = 'primary',
    size = 'md',
    fullWidth = false,
    loading = false,
    disabled = false,
    leftIcon = null,
    rightIcon = null,
    className = '',
    style,
    children,
    ...rest
  },
  ref
) {
  const isDisabled = disabled || loading
  const classes = ['btn']
  // Reutiliza clases existentes de theme.css si aplica
  if (variant === 'primary') classes.push('btn-primary')
  if (variant === 'secondary') classes.push('btn-secondary')

  // Estilos base + tamaño + ancho
  const baseStyle = {
    width: fullWidth ? '100%' : undefined,
    borderRadius: 'var(--radius-sm)',
    ...(sizeStyles[size] || sizeStyles.md)
  }

  // Variante ghost sin CSS adicional (usa tokens)
  if (variant === 'ghost') {
    Object.assign(baseStyle, {
      background: 'transparent',
      color: 'var(--text)',
      border: '1px solid var(--border)',
      boxShadow: 'none'
    })
  }

  return (
    <As
      ref={ref}
      className={[...classes, className].filter(Boolean).join(' ')}
      disabled={As === 'button' ? isDisabled : undefined}
      aria-busy={loading || undefined}
      style={{ ...baseStyle, ...(style || {}) }}
      {...rest}
    >
      <span className="row" style={{ alignItems: 'center', gap: '8px' }}>
        {loading && <Spinner />}
        {!loading && leftIcon}
        <span>{children}</span>
        {!loading && rightIcon}
      </span>
    </As>
  )
})

export default Button
/* Ejemplo de uso (solo documentación, no incluir en build)
// import Button from '@/components/ui/Button.jsx'
// function Example() {
//   return (
//     <div className="row gap">
//       <Button>Primario</Button>
//       <Button variant="secondary">Secundario</Button>
//       <Button variant="ghost">Ghost</Button>
//       <Button size="sm">Pequeño</Button>
//       <Button size="lg" loading>Guardando...</Button>
//       <Button fullWidth>Completo</Button>
//     </div>
//   )
// }
*/