import React from 'react'

// Tarjeta compacta para listar alertas con estado y acción recomendada (placeholder).
export default function AlertCard({ alert }) {
  return (
    <div className="alert-card">
      <strong>{alert?.estado || 'Estado'}</strong>
      <p>{alert?.accion_recomendada || 'Acción recomendada'}</p>
    </div>
  )
}
