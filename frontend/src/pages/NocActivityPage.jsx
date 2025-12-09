import React from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'

// Vista operativa NOC (solo "En curso").
export default function NocActivityPage() {
  const { alerts } = useFetchAlerts({ status_operativo: 'En curso' })
  return (
    <div className="col gap-6">
      <header>
        <h1 className="h1">Actividad NOC</h1>
        <p className="muted small">Monitoreo de alertas en curso.</p>
      </header>

      <div className="grid grid-cols-1 gap-4">
        {alerts.map((a) => (
          <div key={a.id} className="card">
            <div className="row justify-between mb-2">
              <strong className="h3">{a.titulo}</strong>
              <span className="badge badge-warning">En curso</span>
            </div>
            <div className="muted mb-2">{a.descripcion}</div>
            <div className="small muted">
              Actualizado: {new Date(a.updated_at || a.created_at).toLocaleString()}
            </div>
          </div>
        ))}
        {!alerts.length && (
          <div className="card muted text-center p-6">
            No hay alertas en curso actualmente.
          </div>
        )}
      </div>
    </div>
  )
}
