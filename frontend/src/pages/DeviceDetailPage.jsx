import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getAlerts } from '../api/alertApi.js'
import client from '../api/client.js'
import AlertCard from '../components/AlertCard.jsx'
import { updateAlertStatus } from '../api/alertApi.js'

// Detalle del equipo con alertas y logs recientes.
export default function DeviceDetailPage() {
  const { deviceId } = useParams()
  const [alerts, setAlerts] = useState([])
  const [logs, setLogs] = useState([])
  const [limit, setLimit] = useState(10)

  const loadAlerts = async () => {
    const res = await getAlerts({ device_id: Number(deviceId) })
    setAlerts(res.data || [])
  }

  const loadLogs = async () => {
    const res = await client.get(`/devices/${deviceId}/logs`, { params: { limit } })
    setLogs(res.data || [])
  }

  useEffect(() => {
    loadAlerts()
  }, [deviceId])

  useEffect(() => {
    loadLogs()
  }, [deviceId, limit])

  const handleAction = async (alert, newStatus) => {
    await updateAlertStatus(alert.id, { status_operativo: newStatus })
    await loadAlerts()
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
            <AlertCard key={a.id} alert={a} onAction={handleAction} />
          ))}
          {!alerts.length && <span className="muted">Sin alertas.</span>}
        </div>
      </div>

      <div className="card">
        <div className="row space-between">
          <h3>Logs recientes</h3>
          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            {[5, 10, 20].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <div className="logs">
          {logs.map((l) => (
            <pre key={l.id} className="log-line">[{l.timestamp_equipo}] {l.raw_log}</pre>
          ))}
          {!logs.length && <span className="muted">Sin logs.</span>}
        </div>
      </div>
    </div>
  )
}
