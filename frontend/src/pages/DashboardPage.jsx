import React, { useEffect, useMemo, useState } from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import useDeviceHealth from '../hooks/useDeviceHealth.js'
import useAuth from '../hooks/useAuth.js'
import Card from '../components/ui/Card.jsx'

/**
 * Dashboard Page Redesign
 * - CSS: src/styles/pages/dashboard.css
 */
export default function DashboardPage() {
  const { token, authReady } = useAuth()
  const { alerts } = useFetchAlerts()
  const { devices, loading: loadingHealth } = useDeviceHealth()
  const [slaMin, setSlaMin] = useState(null)

  // Computed metrics
  const activeAlerts = alerts.length
  const criticalAlerts = alerts.filter(a => a.estado === 'Alerta Crítica').length

  const globalHealth = useMemo(() => {
    if (!devices.length) return 'unknown'
    if (devices.some((d) => d.health_status === 'rojo')) return 'critical'
    if (devices.some((d) => d.health_status === 'amarillo')) return 'warning'
    return 'healthy'
  }, [devices])

  useEffect(() => {
    if (!authReady || !token) return

    // Simulate SLA fetch or real fetch
    let mounted = true
    ;(async () => {
      try {
        const r = await fetch(
          `${import.meta.env.VITE_API_URL || 'http://localhost:5000/api'}/sla/metrics`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        if (r.ok) {
            const data = await r.json()
            if (mounted) setSlaMin(data?.tiempo_promedio_resolucion_severa_min ?? 0)
        }
      } catch (e) {
        // Silent fail or mock
        if (mounted) setSlaMin(0.0) // fallback
      }
    })()

    return () => { mounted = false }
  }, [authReady, token])

  return (
    <div className="dashboard fade-in">

      {/* Header */}
      <header>
        <div className="dashboard-header-meta">
          Overview / Dashboard
        </div>
        <h1 className="h1">Dashboard Operativo</h1>
      </header>

      {/* Metrics Grid */}
      <div className="dashboard-grid-metrics">

        {/* Active Alerts */}
        <MetricCard
            title="Alertas Activas"
            value={activeAlerts}
            trend="+2% vs ayer" // Mock trend
            color={activeAlerts > 0 ? 'warning' : 'neutral'}
        />

        {/* Critical Alerts */}
        <MetricCard
            title="Críticas"
            value={criticalAlerts}
            trend="0 críticas nuevas"
            color={criticalAlerts > 0 ? 'danger' : 'success'}
        />

        {/* Global Health */}
        <Card statusColor={globalHealth === 'critical' ? 'danger' : globalHealth === 'warning' ? 'warning' : 'success'}>
            <div className="metric-title">Salud Global</div>
            <div className="global-health-status">
                <span style={{ textTransform: 'capitalize' }}>
                    {globalHealth === 'healthy' ? 'Óptima' : globalHealth === 'critical' ? 'Crítica' : globalHealth === 'warning' ? 'Degradada' : 'Desconocida'}
                </span>
                <StatusDot status={globalHealth} size={16} />
            </div>
            <div className="global-health-subtext">
                {devices.length} equipos monitoreados
            </div>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid-content">

        {/* SLA Section (Left/Top) */}
        <div style={{ gridColumn: 'span 2' }}>
            <Card elevated>
                <div className="sla-card-header">
                    <div>
                        <h3 className="h3">SLA Resolución</h3>
                        <p className="sla-description">Tiempo promedio de resolución de incidentes severos</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                         <div className="sla-value">
                            {slaMin !== null ? slaMin.toFixed(1) : '-'} <span className="sla-unit">min</span>
                         </div>
                         <div className="sla-trend">
                            ▼ 12% vs semana pasada
                         </div>
                    </div>
                </div>
                {/* Mock Chart Area */}
                <div className="sla-chart-area">
                    <div style={{ position: 'absolute', bottom: 8, left: 8, fontSize: '11px', color: 'var(--color-text-muted)' }}>Ultimos 7 días</div>
                </div>
            </Card>
        </div>

        {/* Device Status List (Right/Bottom) */}
        <div style={{ gridColumn: 'span 2' }}>
            <Card>
                <div className="equipment-table-header">
                    <h3 className="h3">Estado de Equipos</h3>
                    <button style={{ background: 'none', border: 'none', color: 'var(--color-accent-primary)', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}>Ver todos</button>
                </div>

                {loadingHealth ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-muted)' }}>Cargando equipos...</div>
                ) : devices.length === 0 ? (
                    <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-muted)' }}>No hay equipos registrados</div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table className="equipment-table">
                            <thead>
                                <tr>
                                    <th>EQUIPO</th>
                                    <th>IP</th>
                                    <th>ESTADO</th>
                                    <th style={{ textAlign: 'right' }}>ÚLTIMA CONEXIÓN</th>
                                </tr>
                            </thead>
                            <tbody>
                                {devices.slice(0, 5).map(d => (
                                    <tr key={d.id}>
                                        <td style={{ fontWeight: 500 }}>{d.name}</td>
                                        <td style={{ color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>{d.ip_address}</td>
                                        <td>
                                            <StatusBadge status={d.health_status} />
                                        </td>
                                        <td style={{ textAlign: 'right', color: 'var(--color-text-muted)', fontSize: '12px' }}>
                                            {d.last_seen ? new Date(d.last_seen).toLocaleTimeString() : 'N/A'}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </Card>
        </div>

      </div>
    </div>
  )
}

// Sub-components for Dashboard
function MetricCard({ title, value, trend, color }) {
    const colors = {
        warning: 'var(--color-accent-warning)',
        danger: 'var(--color-accent-danger)',
        success: 'var(--color-accent-secondary)',
        neutral: 'var(--color-text-primary)'
    }
    const currentColor = colors[color] || colors.neutral

    return (
        <Card>
            <div className="metric-title">{title}</div>
            <div className="metric-value" style={{ color: currentColor }}>
                {value}
            </div>
            {trend && (
                <div className="metric-trend">
                    {trend}
                </div>
            )}
        </Card>
    )
}

function StatusBadge({ status }) {
    const styles = {
        verde: { bg: 'rgba(52, 199, 89, 0.15)', color: '#34c759', label: 'Online' },
        amarillo: { bg: 'rgba(255, 149, 0, 0.15)', color: '#ff9500', label: 'Warning' },
        rojo: { bg: 'rgba(255, 59, 48, 0.15)', color: '#ff3b30', label: 'Offline' },
        unknown: { bg: 'var(--color-bg-tertiary)', color: 'var(--color-text-muted)', label: 'Unknown' }
    }
    const s = styles[status] || styles.unknown

    return (
        <span className="status-badge" style={{ backgroundColor: s.bg, color: s.color }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: s.color }}></span>
            {s.label}
        </span>
    )
}

function StatusDot({ status, size = 8 }) {
    const map = {
        healthy: '#34c759',
        warning: '#ff9500',
        critical: '#ff3b30',
        unknown: '#8e8e93'
    }
    return <div style={{ width: size, height: size, borderRadius: '50%', backgroundColor: map[status] || map.unknown }}></div>
}
