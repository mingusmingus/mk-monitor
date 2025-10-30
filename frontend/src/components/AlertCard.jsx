import React from 'react'
import StatusBadge from './StatusBadge.jsx'

// Tarjeta de alerta con info y acciones básicas de NOC (TODO).
export default function AlertCard({ alert, onAction }) {
  return (
    <div className="card alert-card">
      <div className="row space-between">
        <strong>{alert?.titulo || 'Alerta'}</strong>
        <StatusBadge estado={alert?.estado} />
      </div>
      <p className="muted">{alert?.descripcion}</p>
      <p><strong>Acción:</strong> {alert?.accion_recomendada}</p>
      <div className="row small gap">
        <span className="tag">Operativo: {alert?.status_operativo || 'Pendiente'}</span>
        {alert?.comentario_ultimo && <span className="tag">"{alert.comentario_ultimo}"</span>}
        {alert?.created_at && <span className="tag">{new Date(alert.created_at).toLocaleString()}</span>}
      </div>
      <div className="row gap mt">
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
