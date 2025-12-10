import React, { forwardRef } from 'react'

/**
 * Input
 * - Styles: src/styles/components/input.css
 * - Features: Floating label support, Focus ring, States (error, success)
 */

const Input = forwardRef(function Input(
  {
    label,
    error,
    success,
    loading,
    className = '',
    style,
    id,
    placeholder = ' ',
    endAdornment,
    ...props
  },
  ref
) {
  const inputId = id || React.useId()

  const stateClass = error ? 'input-error' : success ? 'input-success' : ''
  const hasLabelClass = label ? 'has-label' : ''

  return (
    <div className={`input-group ${className}`} style={style}>
      <input
        ref={ref}
        id={inputId}
        className={`custom-input ${stateClass} ${hasLabelClass}`}
        placeholder={placeholder}
        {...props}
      />

      {label && (
        <label htmlFor={inputId} className="custom-label">
          {label}
        </label>
      )}

      {/* Loading or Icon Adornment */}
      {(loading || endAdornment) && (
        <div className="input-adornment">
          {loading ? (
             <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ animation: 'spin 1s linear infinite' }}>
               <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
               <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.3" />
               <path d="M12 2C6.47715 2 2 6.47715 2 12" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
             </svg>
          ) : (
            endAdornment
          )}
        </div>
      )}

      {error && typeof error === 'string' && (
        <span className="input-helper-text">
          {error}
        </span>
      )}
    </div>
  )
})

export default Input
