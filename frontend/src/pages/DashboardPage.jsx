import React, { useEffect, useMemo, useState } from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import useDeviceHealth from '../hooks/useDeviceHealth.js'
import DeviceHealthIndicator from '../components/DeviceHealthIndicator.jsx'
import useAuth from '../hooks/useAuth.js'

// Dashboard general con resumen rápido.
// TODO: optimizar con endpoints dedicados en backend.
// Ahora incluye KPI de SLA.
export default function DashboardPage() {
  const { token } = useAuth()
  const { alerts } = useFetchAlerts()
  const { devices, loading: loadingHealth } = useDeviceHealth()
  const [criticas, setCriticas] = useState(0)
  const [slaMin, setSlaMin] = useState(null)

  useEffect(() => {
    setCriticas(alerts.filter((a) => a.estado === 'Alerta Crítica').length)
  }, [alerts])

  // Consumir /api/sla/metrics (prioridad BAJA)
  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const r = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000/api'}/sla/metrics`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        if (!r.ok) throw new Error('SLA fetch error')
        const data = await r.json()
        if (mounted) setSlaMin(data?.tiempo_promedio_resolucion_severa_min ?? null)
      } catch (e) {
        console.warn('TODO: manejar error SLA', e)
      }
    })()
    return () => { mounted = false }
  }, [token])

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

      {/* KPI SLA (prioridad BAJA) */}
      <div className="card">
        <h3>SLA - Tiempo promedio resolución (severas)</h3>
        <div className="kpi">
          {slaMin !== null ? `${slaMin.toFixed(1)} min` : '—'}
        </div>
        {slaMin === null && <div className="muted small">Calculando o sin datos...</div>}
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