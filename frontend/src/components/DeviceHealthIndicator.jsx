import React from 'react'

// Indicador semáforo de salud del equipo.
export default function DeviceHealthIndicator({ healthStatus = 'verde' }) {
  // Map healthStatus to CSS class if needed, or rely on .dot.verde/.amarillo/.rojo in theme.css
  return (
    <span className="row gap-1 items-center">
      <span className={`dot ${healthStatus}`} aria-label={healthStatus} />
    </span>
  )
}
