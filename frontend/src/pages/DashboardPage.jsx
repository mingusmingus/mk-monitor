import React, { useEffect, useMemo, useState } from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import useDeviceHealth from '../hooks/useDeviceHealth.js'
import DeviceHealthIndicator from '../components/DeviceHealthIndicator.jsx'

// Dashboard general con resumen rápido.
// TODO: optimizar con endpoints dedicados en backend.
export default function DashboardPage() {
  const { alerts } = useFetchAlerts()
  const { devices, loading: loadingHealth } = useDeviceHealth()
  const [criticas, setCriticas] = useState(0)

  useEffect(() => {
    setCriticas(alerts.filter((a) => a.estado === 'Alerta Crítica').length)
  }, [alerts])

  const saludGlobal = useMemo(() => {
    if (!devices.length) return 'verde'
    if (devices.some((d) => d.health_status === 'rojo')) return 'rojo'
    if (devices.some((d) => d.health_status === 'amarillo')) return 'amarillo'
    return 'verde'
  }, [devices])

  return (
    <div className="col gap">
      <h1>Dashboard</h1>
      <div className="grid cards-3">
        <div className="card">
          <h3>Alertas activas</h3>
          <div className="kpi">{alerts.length}</div>
        </div>
        <div className="card">
          <h3>Alertas críticas</h3>
          <div className="kpi">{criticas}</div>
        </div>
        <div className="card">
          <h3>Salud global</h3>
          <div className="row gap">
            <DeviceHealthIndicator healthStatus={saludGlobal} />
            {loadingHealth && <span className="muted">Actualizando...</span>}
          </div>
        </div>
      </div>
      <div className="card">
        <h3>Estado de equipos</h3>
        <div className="row wrap gap">
          {devices.map((d) => (
            <div key={d.device_id} className="chip">
              {d.name} <DeviceHealthIndicator healthStatus={d.health_status} />
            </div>
          ))}
          {!devices.length && <span className="muted">Sin equipos aún.</span>}
        </div>
      </div>
    </div>
  )
}