import React from 'react'

// Indicador semáforo de salud del equipo.
export default function DeviceHealthIndicator({ healthStatus = 'verde' }) {
  return (
    <span className="health">
      <span className={`dot ${healthStatus}`} aria-label={healthStatus} />
      <span className="label">{healthStatus}</span>
    </span>
  )
}