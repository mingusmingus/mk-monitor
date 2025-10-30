import React from 'react'

// Mapea estado a clase de color.
const mapClass = (estado) => {
  switch (estado) {
    case 'Alerta Crítica':
      return 'badge badge-critical'
    case 'Alerta Severa':
      return 'badge badge-severe'
    case 'Alerta Menor':
      return 'badge badge-minor'
    default:
      return 'badge badge-info'
  }
}

// Badge de estado de alerta.
export default function StatusBadge({ estado = 'Aviso' }) {
  return <span className={mapClass(estado)}>{estado}</span>
}