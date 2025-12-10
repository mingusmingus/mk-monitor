import React, { forwardRef } from 'react'

/**
 * Button
 * - Variants: primary, secondary, danger, ghost
 * - Sizes: sm, md, lg
 * - States: hover, active, disabled, loading
 *
 * Styled via CSS classes in src/styles/components/button.css
 */

function Spinner({ size = 16, color = 'currentColor' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ animation: 'spin 1s linear infinite' }}
    >
      <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
      <circle cx="12" cy="12" r="10" stroke={color} strokeWidth="3" strokeOpacity="0.3" />
      <path d="M12 2C6.47715 2 2 6.47715 2 12" stroke={color} strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

const Button = forwardRef(function Button(
  {
    as: As = 'button',
    variant = 'primary', // primary, secondary, danger, ghost
    size = 'md',
    fullWidth = false,
    loading = false,
    disabled = false,
    leftIcon = null,
    rightIcon = null,
    className = '',
    style = {},
    children,
    ...rest
  },
  ref
) {
  const isDisabled = disabled || loading

  const variantClass = `btn-${variant}`
  const sizeClass = `btn-${size}`
  const widthClass = fullWidth ? 'w-full' : ''

  return (
    <As
      ref={ref}
      className={`btn ${variantClass} ${sizeClass} ${widthClass} ${className}`}
      disabled={As === 'button' ? isDisabled : undefined}
      style={style}
      {...rest}
    >
      {loading && <Spinner size={size === 'sm' ? 12 : 16} />}
      {!loading && leftIcon}
      <span>{children}</span>
      {!loading && rightIcon}
    </As>
  )
})

export default Button
