import React from 'react'
import StatusBadge from './StatusBadge.jsx'

// Tarjeta de alerta con info y acciones básicas de NOC (TODO).
export default function AlertCard({ alert, onAction }) {
  return (
    <div className="card alert-card">
      <div className="row justify-between mb-2">
        <strong>{alert?.titulo || 'Alerta'}</strong>
        <StatusBadge estado={alert?.estado} />
      </div>
      <p className="muted small mb-2">{alert?.descripcion}</p>
      <p className="small mb-2"><strong>Acción:</strong> {alert?.accion_recomendada}</p>
      <div className="row wrap gap-2 small">
        <span className="badge badge-minor">Operativo: {alert?.status_operativo || 'Pendiente'}</span>
        {alert?.comentario_ultimo && <span className="badge badge-minor">"{alert.comentario_ultimo}"</span>}
        {alert?.created_at && <span className="badge badge-minor">{new Date(alert.created_at).toLocaleString()}</span>}
      </div>
      <div className="row gap-2 mt-2">
        <button className="btn btn-secondary" onClick={() => onAction?.(alert, 'En curso')}>
          Marcar En curso
        </button>
        <button className="btn btn-primary" onClick={() => onAction?.(alert, 'Resuelta')}>
          Marcar Resuelta
        </button>
      </div>
    </div>
  )
}
