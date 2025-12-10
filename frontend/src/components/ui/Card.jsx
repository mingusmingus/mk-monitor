import React from 'react'

/**
 * Card
 * - Structure: Padding 16px, rounded 8px
 * - Variants: Default, Elevated, Interactive, Status
 */
export default function Card({
  children,
  className = '',
  elevated = false,
  interactive = false,
  statusColor = null, // 'success', 'warning', 'danger'
  style = {},
  onClick,
  ...rest
}) {
  const statusColors = {
    success: 'var(--color-accent-secondary)',
    warning: 'var(--color-accent-warning)',
    danger: 'var(--color-accent-danger)',
    primary: 'var(--color-accent-primary)'
  }

  const borderLeftStyle = statusColor
    ? { borderLeft: `3px solid ${statusColors[statusColor] || statusColor}` }
    : {}

  return (
    <div
      className={`card ${className}`}
      onClick={interactive ? onClick : undefined}
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--color-border)',
        padding: '16px',
        boxShadow: elevated ? 'var(--shadow-md)' : 'var(--shadow-sm)',
        transition: 'transform 0.2s, box-shadow 0.2s',
        cursor: interactive ? 'pointer' : 'default',
        transform: interactive ? 'scale(1)' : undefined,
        ...borderLeftStyle,
        ...style
      }}
      onMouseEnter={(e) => {
        if (interactive) {
          e.currentTarget.style.transform = 'scale(1.01)'
          e.currentTarget.style.boxShadow = 'var(--shadow-md)'
        }
      }}
      onMouseLeave={(e) => {
        if (interactive) {
          e.currentTarget.style.transform = 'scale(1)'
          e.currentTarget.style.boxShadow = elevated ? 'var(--shadow-md)' : 'var(--shadow-sm)'
        }
      }}
      {...rest}
    >
      {children}
    </div>
  )
}
