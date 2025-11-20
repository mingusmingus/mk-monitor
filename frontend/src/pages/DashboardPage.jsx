import React, { useEffect, useMemo, useState } from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import useDeviceHealth from '../hooks/useDeviceHealth.js'
import DeviceHealthIndicator from '../components/DeviceHealthIndicator.jsx'
import useAuth from '../hooks/useAuth.js'

// Dashboard general con resumen rápido.
// Gating estricto: no consumir endpoints hasta authReady + token.
// DEBUG: logs con prefijo [Dashboard] (remover tras estabilizar).
export default function DashboardPage() {
  const { token, authReady } = useAuth()
  const { alerts } = useFetchAlerts()
  const { devices, loading: loadingHealth } = useDeviceHealth()
  const [criticas, setCriticas] = useState(0)
  const [slaMin, setSlaMin] = useState(null)
  const [slaLoaded, setSlaLoaded] = useState(false) // evita doble carga en StrictMode

  useEffect(() => {
    setCriticas(alerts.filter((a) => a.estado === 'Alerta Crítica').length)
  }, [alerts])

  useEffect(() => {
    if (!authReady || !token) {
      console.debug('[Dashboard] skip SLA fetch (authReady/token no listos)')
      return
    }
    if (slaLoaded) return
    let mounted = true
    ;(async () => {
      try {
        console.debug('[Dashboard] fetching /sla/metrics')
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
    <div className="col" style={{ gap: 'var(--spacing-6)' }}>
      <header>
        <h1 style={{ fontSize: 'var(--font-2xl)', fontWeight: 600, margin: 0 }}>Dashboard</h1>
        <p className="muted">Resumen operativo en tiempo real.</p>
      </header>

      <div className="grid cards-3" style={{ gap: 'var(--spacing-4)' }}>
        <div className="card">
          <h3 className="muted small uppercase">Alertas activas</h3>
          <div className="kpi" style={{ fontSize: 'var(--font-3xl)', fontWeight: 700 }}>{alerts.length}</div>
        </div>
        <div className="card">
          <h3 className="muted small uppercase">Alertas críticas</h3>
          <div
            className="kpi"
            style={{ fontSize: 'var(--font-3xl)', fontWeight: 700, color: 'var(--critical)' }}
          >
            {criticas}
          </div>
        </div>
        <div className="card">
          <h3 className="muted small uppercase">Salud global</h3>
          <div className="row gap" style={{ marginTop: 'var(--spacing-2)' }}>
            <DeviceHealthIndicator healthStatus={saludGlobal} />
            {loadingHealth && <span className="muted small">Actualizando...</span>}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="muted small uppercase">SLA - Tiempo promedio resolución (severas)</h3>
        <div
          className="kpi"
          style={{ fontSize: 'var(--font-2xl)', fontWeight: 600, marginTop: 'var(--spacing-2)' }}
        >
          {slaMin !== null ? `${slaMin.toFixed(1)} min` : authReady ? '—' : 'Esperando auth…'}
        </div>
        {slaMin === null && authReady && !loadingHealth && (
          <div className="muted small">Calculando o sin datos...</div>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginBottom: 'var(--spacing-3)' }}>Estado de equipos</h3>
        <div className="row wrap" style={{ gap: 'var(--spacing-2)' }}>
          {devices.map((d) => (
            <div key={d.device_id || d.id} className="chip" style={{
              border: '1px solid var(--border)',
              padding: '4px 12px',
              borderRadius: '99px',
              background: 'var(--bg-muted)'
            }}>
              {d.name} <DeviceHealthIndicator healthStatus={d.health_status} />
            </div>
          ))}
          {!devices.length && <span className="muted">Sin equipos aún.</span>}
        </div>
      </div>
    </div>
  )
}