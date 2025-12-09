import React, { useEffect, useMemo, useState } from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import useDeviceHealth from '../hooks/useDeviceHealth.js'
import DeviceHealthIndicator from '../components/DeviceHealthIndicator.jsx'
import useAuth from '../hooks/useAuth.js'

// Dashboard general con resumen rápido.
// Gating estricto: no consumir endpoints hasta authReady + token.
export default function DashboardPage() {
  const { token, authReady } = useAuth()
  const { alerts } = useFetchAlerts()
  const { devices, loading: loadingHealth } = useDeviceHealth()
  const [criticas, setCriticas] = useState(0)
  const [slaMin, setSlaMin] = useState(null)
  const [slaLoaded, setSlaLoaded] = useState(false)

  useEffect(() => {
    setCriticas(alerts.filter((a) => a.estado === 'Alerta Crítica').length)
  }, [alerts])

  useEffect(() => {
    if (!authReady || !token) {
      return
    }
    if (slaLoaded) return
    let mounted = true
    ;(async () => {
      try {
        const r = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:5000/api'}/sla/metrics`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        if (!r.ok) throw new Error('SLA fetch error')
        const data = await r.json()
        if (mounted) setSlaMin(data?.tiempo_promedio_resolucion_severa_min ?? null)
      } catch (e) {
        console.warn('[Dashboard] SLA error', e)
      } finally {
        if (mounted) setSlaLoaded(true)
      }
    })()
    return () => {
      mounted = false
    }
  }, [authReady, token, slaLoaded])

  const saludGlobal = useMemo(() => {
    if (!devices.length) return 'verde'
    if (devices.some((d) => d.health_status === 'rojo')) return 'rojo'
    if (devices.some((d) => d.health_status === 'amarillo')) return 'amarillo'
    return 'verde'
  }, [devices])

  return (
    <div className="col gap-6">
      <header>
        <h1 className="h1">Dashboard</h1>
        <p className="muted small">Resumen operativo en tiempo real.</p>
      </header>

      <div className="grid grid-cols-3 gap-4">
        <div className="card">
          <h3 className="kpi-label">Alertas activas</h3>
          <div className="kpi-value">{alerts.length}</div>
        </div>
        <div className="card">
          <h3 className="kpi-label">Alertas críticas</h3>
          <div className="kpi-value" style={{ color: 'var(--critical)' }}>
            {criticas}
          </div>
        </div>
        <div className="card">
          <h3 className="kpi-label">Salud global</h3>
          <div className="row gap-2 mt-2 items-center">
            <DeviceHealthIndicator healthStatus={saludGlobal} />
            {loadingHealth && <span className="muted small">Actualizando...</span>}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="kpi-label">SLA - Tiempo promedio resolución (severas)</h3>
        <div className="kpi-value">
          {slaMin !== null ? `${slaMin.toFixed(1)} min` : authReady ? '—' : 'Esperando auth…'}
        </div>
        {slaMin === null && authReady && !loadingHealth && (
          <div className="muted small">Calculando o sin datos...</div>
        )}
      </div>

      <div className="card">
        <h3 className="h3 mb-3">Estado de equipos</h3>
        <div className="row wrap gap-2" style={{ flexWrap: 'wrap' }}>
          {devices.map((d) => (
            <div key={d.device_id || d.id} className="badge badge-pill">
              {d.name} <DeviceHealthIndicator healthStatus={d.health_status} />
            </div>
          ))}
          {!devices.length && <span className="muted">Sin equipos aún.</span>}
        </div>
      </div>
    </div>
  )
}
