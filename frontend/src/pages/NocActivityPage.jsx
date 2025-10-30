import React from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'

// Vista operativa NOC (solo "En curso").
export default function NocActivityPage() {
  const { alerts } = useFetchAlerts({ status_operativo: 'En curso' })
  return (
    <div className="col gap">
      <h1>Actividad NOC</h1>
      <div className="col gap">
        {alerts.map((a) => (
          <div key={a.id} className="card">
            <strong>{a.titulo}</strong>
            <div className="muted">{a.descripcion}</div>
            <div className="small">Operativo: {a.status_operativo}</div>
          </div>
        ))}
        {!alerts.length && <span className="muted">No hay alertas en curso.</span>}
      </div>
    </div>
  )
}
