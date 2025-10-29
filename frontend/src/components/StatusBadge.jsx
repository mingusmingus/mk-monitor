import React from 'react'

// Muestra el estado de alerta con colores (placeholder).
export default function StatusBadge({ status = 'Aviso' }) {
  return <span className={`status-badge status-${status}`}>{status}</span>
}