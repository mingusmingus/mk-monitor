import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getAlerts } from '../api/alertApi.js'
import client from '../api/client.js'
import AlertCard from '../components/AlertCard.jsx'
import { updateAlertStatus } from '../api/alertApi.js'
import useAuth from '../hooks/useAuth.js'
import Button from '../components/ui/Button.jsx'
import TextField from '../components/ui/TextField.jsx'

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
    <div className="col gap-6">
      <h1 className="h1">Dispositivo #{deviceId}</h1>

      <div className="card">
        <div className="row justify-between mb-4">
          <h3 className="h3">Alertas</h3>
        </div>
        <div className="col gap-3">
          {alerts.map((a) => (
            <AlertCard key={a.id} alert={a} onAction={isSuspended ? null : handleAction} />
          ))}
          {!alerts.length && <span className="muted p-4 text-center">Sin alertas.</span>}
        </div>
      </div>

      <div className="card">
        <div className="row justify-between wrap gap-2 mb-4">
          <h3 className="h3">Logs recientes</h3>
          <div className="row gap-2">
            <select
              className="input"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              style={{ width: 'auto' }}
            >
              {[5, 10, 20].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
            <Button variant="primary" onClick={handleExportCSV}>
              Exportar CSV
            </Button>
          </div>
        </div>

        {/* Filtros de fecha (prioridad MEDIA) */}
        <div className="row wrap gap-3 mb-4 items-end">
          <div className="col gap-1" style={{ flex: 1 }}>
            <span className="small muted">Fecha inicio:</span>
            <input
              type="datetime-local"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
              className="input"
            />
          </div>
          <div className="col gap-1" style={{ flex: 1 }}>
            <span className="small muted">Fecha fin:</span>
            <input
              type="datetime-local"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
              className="input"
            />
          </div>
          <Button onClick={loadLogs}>
            Aplicar filtros
          </Button>
        </div>

        <div className="logs bg-muted p-4 rounded-md" style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {logs.map((l) => (
            <pre key={l.id} className="small" style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              <span className="muted">[{l.timestamp_equipo || 'N/A'}]</span> {l.raw_log}
            </pre>
          ))}
          {!logs.length && <span className="muted">Sin logs.</span>}
        </div>
      </div>
    </div>
  )
}
