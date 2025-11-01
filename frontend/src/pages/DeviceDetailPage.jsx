import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getAlerts } from '../api/alertApi.js'
import client from '../api/client.js'
import AlertCard from '../components/AlertCard.jsx'
import { updateAlertStatus } from '../api/alertApi.js'
import useAuth from '../hooks/useAuth.js'

// Detalle del equipo con alertas y logs recientes.
// Filtros de fecha + Export CSV.
export default function DeviceDetailPage() {
  const { deviceId } = useParams()
  const { tenantStatus, token } = useAuth()
  const [alerts, setAlerts] = useState([])
  const [logs, setLogs] = useState([])
  const [limit, setLimit] = useState(10)
  const [fechaInicio, setFechaInicio] = useState('')
  const [fechaFin, setFechaFin] = useState('')

  const isSuspended = tenantStatus === 'suspendido'

  const loadAlerts = async () => {
    const res = await getAlerts({ device_id: Number(deviceId) })
    setAlerts(res.data || [])
  }

  const loadLogs = async () => {
    const params = new URLSearchParams()
    params.set('limit', limit.toString())
    if (fechaInicio) params.set('fecha_inicio', new Date(fechaInicio).toISOString())
    if (fechaFin) params.set('fecha_fin', new Date(fechaFin).toISOString())

    const res = await client.get(`/devices/${deviceId}/logs?${params.toString()}`)
    setLogs(res.data || [])
  }

  useEffect(() => {
    loadAlerts()
  }, [deviceId])

  useEffect(() => {
    loadLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId, limit])

  const handleAction = async (alert, newStatus) => {
    if (isSuspended) {
      alert('Acción bloqueada: cuenta suspendida')
      return
    }
    await updateAlertStatus(alert.id, { status_operativo: newStatus })
    await loadAlerts()
  }

  const handleExportCSV = () => {
    const params = new URLSearchParams()
    params.set('export', 'csv')
    params.set('limit', '50')
    if (fechaInicio) params.set('fecha_inicio', new Date(fechaInicio).toISOString())
    if (fechaFin) params.set('fecha_fin', new Date(fechaFin).toISOString())
    
    // Construir URL con token en header (abrir en ventana nueva con descarga)
    const url = `${client.defaults.baseURL}/devices/${deviceId}/logs?${params.toString()}`
    window.open(url, '_blank')
  }

  return (
    <div className="col gap">
      <h1>Dispositivo #{deviceId}</h1>

      <div className="card">
        <div className="row space-between">
          <h3>Alertas</h3>
        </div>
        <div className="col gap">
          {alerts.map((a) => (
            <AlertCard key={a.id} alert={a} onAction={isSuspended ? null : handleAction} />
          ))}
          {!alerts.length && <span className="muted">Sin alertas.</span>}
        </div>
      </div>

      <div className="card">
        <div className="row space-between">
          <h3>Logs recientes</h3>
          <div className="row gap">
            <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
              {[5, 10, 20].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
            <button className="btn btn-primary" onClick={handleExportCSV}>
              Exportar CSV
            </button>
          </div>
        </div>

        {/* Filtros de fecha (prioridad MEDIA) */}
        <div className="row gap mt">
          <label className="col">
            <span className="small">Fecha inicio:</span>
            <input
              type="datetime-local"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
              className="input"
            />
          </label>
          <label className="col">
            <span className="small">Fecha fin:</span>
            <input
              type="datetime-local"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
              className="input"
            />
          </label>
          <button className="btn" onClick={loadLogs}>
            Aplicar filtros
          </button>
        </div>

        <div className="logs">
          {logs.map((l) => (
            <pre key={l.id} className="log-line">
              [{l.timestamp_equipo || 'N/A'}] {l.raw_log}
            </pre>
          ))}
          {!logs.length && <span className="muted">Sin logs.</span>}
        </div>
      </div>
    </div>
  )
}
