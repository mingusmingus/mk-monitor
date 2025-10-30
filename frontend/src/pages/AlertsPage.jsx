import React, { useState } from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import AlertCard from '../components/AlertCard.jsx'
import { updateAlertStatus } from '../api/alertApi.js'

// Listado/gestión de alertas con filtros básicos.
export default function AlertsPage() {
  const [filters, setFilters] = useState({ estado: '', device_id: '', status_operativo: '' })
  const { alerts, loading, error, refetch } = useFetchAlerts(filters)

  const onAction = async (alert, newStatus) => {
    await updateAlertStatus(alert.id, { status_operativo: newStatus })
    refetch()
  }

  return (
    <div className="col gap">
      <h1>Alertas</h1>

      <div className="card">
        <div className="row gap">
          <select
            value={filters.estado}
            onChange={(e) => setFilters((f) => ({ ...f, estado: e.target.value }))}
          >
            <option value="">Todos</option>
            <option>Aviso</option>
            <option>Alerta Menor</option>
            <option>Alerta Severa</option>
            <option>Alerta Crítica</option>
          </select>
          <input
            placeholder="ID Dispositivo"
            value={filters.device_id}
            onChange={(e) => setFilters((f) => ({ ...f, device_id: e.target.value }))}
          />
          <select
            value={filters.status_operativo}
            onChange={(e) => setFilters((f) => ({ ...f, status_operativo: e.target.value }))}
          >
            <option value="">Todos</option>
            <option>Pendiente</option>
            <option>En curso</option>
            <option>Resuelta</option>
          </select>
          <button className="btn" onClick={refetch}>Filtrar</button>
        </div>
      </div>

      <div className="col gap">
        {loading && <div className="muted">Cargando...</div>}
        {error && <div className="error">{String(error)}</div>}
        {!loading && !alerts.length && <div className="muted">Sin resultados.</div>}
        {alerts.map((a) => <AlertCard key={a.id} alert={a} onAction={onAction} />)}
      </div>
    </div>
  )
}