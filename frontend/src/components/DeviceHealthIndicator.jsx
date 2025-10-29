import React from 'react'

// Indicador semáforo de salud del equipo (Verde/Amarillo/Rojo) (placeholder).
export default function DeviceHealthIndicator({ health = 'verde' }) {
  return <span className={`health-indicator ${health}`}>{health}</span>
}