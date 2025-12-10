import React from 'react'

/**
 * Device Health Indicator
 * - Refactored to use inline styles or new CSS variables
 */
export default function DeviceHealthIndicator({ healthStatus = 'verde' }) {
  const colors = {
    verde: '#34c759',
    amarillo: '#ff9500',
    rojo: '#ff3b30',
    unknown: '#8e8e93'
  }

  const color = colors[healthStatus] || colors.unknown

  return (
    <span style={{
        display: 'inline-block',
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        backgroundColor: color,
        boxShadow: `0 0 4px ${color}`
    }} aria-label={healthStatus} />
  )
}
