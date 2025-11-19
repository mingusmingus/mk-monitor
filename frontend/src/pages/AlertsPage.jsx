import React, { useState } from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import AlertCard from '../components/AlertCard.jsx'
import { updateAlertStatus } from '../api/alertApi.js'
import useAuth from '../hooks/useAuth.js'
import Button from '../components/ui/Button.jsx'
import TextField from '../components/ui/TextField.jsx'

// Listado/gestión de alertas con filtros básicos.
// Bloqueo por suspensión: deshabilitar acciones de cambio de estado.
export default function AlertsPage() {
  const { tenantStatus } = useAuth()
  const [filters, setFilters] = useState({ estado: '', device_id: '', status_operativo: '' })
  const { alerts, loading, error, refetch } = useFetchAlerts(filters)

  const isSuspended = tenantStatus === 'suspendido'

  const onAction = async (alert, newStatus) => {
    if (isSuspended) {
      alert('Acción bloqueada: cuenta suspendida')
      return
    }
    await updateAlertStatus(alert.id, { status_operativo: newStatus })
    refetch()
  }

  return (
    <div className="col" style={{ gap: 'var(--spacing-6)' }}>
      <header className="row space-between wrap">
        <h1 style={{ fontSize: 'var(--font-2xl)', fontWeight: 600, margin: 0 }}>Alertas</h1>
        <Button onClick={refetch} variant="secondary" size="sm">Actualizar</Button>
      </header>

      <div className="card">
        <div className="row wrap" style={{ gap: 'var(--spacing-3)', alignItems: 'flex-end' }}>
          <div className="col" style={{ gap: 4 }}>
            <label className="small muted">Severidad</label>
            <select
              className="input"
              value={filters.estado}
              onChange={(e) => setFilters((f) => ({ ...f, estado: e.target.value }))}
              style={{ height: 40, minWidth: 140 }}
            >
              <option value="">Todas</option>
              <option>Aviso</option>
              <option>Alerta Menor</option>
              <option>Alerta Severa</option>
              <option>Alerta Crítica</option>
            </select>
          </div>
          
          <div style={{ width: 140 }}>
            <TextField
              label="ID Dispositivo"
              placeholder="Ej. 1"
              value={filters.device_id}
              onChange={(e) => setFilters((f) => ({ ...f, device_id: e.target.value }))}
            />
          </div>

          <div className="col" style={{ gap: 4 }}>
            <label className="small muted">Estado Operativo</label>
            <select
              className="input"
              value={filters.status_operativo}
              onChange={(e) => setFilters((f) => ({ ...f, status_operativo: e.target.value }))}
              style={{ height: 40, minWidth: 140 }}
            >
              <option value="">Todos</option>
              <option>Pendiente</option>
              <option>En curso</option>
              <option>Resuelta</option>
            </select>
          </div>

          <div style={{ paddingBottom: 2 }}>
            <Button onClick={refetch}>Aplicar Filtros</Button>
          </div>
        </div>
        {isSuspended && (
          <div className="muted small mt">
            ℹ️ Modo solo lectura: no puedes cambiar el estado de alertas mientras la cuenta esté suspendida.
          </div>
        )}
      </div>

      <div className="col" style={{ gap: 'var(--spacing-3)' }}>
        {loading && <div className="muted">Cargando alertas...</div>}
        {error && <div className="error">{String(error)}</div>}
        {!loading && !alerts.length && (
          <div className="card muted" style={{ textAlign: 'center', padding: 'var(--spacing-8)' }}>
            Sin resultados para los filtros actuales.
          </div>
        )}
        {alerts.map((a) => (
          <AlertCard
            key={a.id}
            alert={a}
            onAction={onAction}
          />
        ))}
      </div>
    </div>
  )
}