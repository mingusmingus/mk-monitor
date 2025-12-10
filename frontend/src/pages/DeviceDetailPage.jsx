import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getAlerts, updateAlertStatus } from '../api/alertApi.js'
import client from '../api/client.js'
import useAuth from '../hooks/useAuth.js'
import Card from '../components/ui/Card.jsx'
import Button from '../components/ui/Button.jsx'
import Input from '../components/ui/Input.jsx'

/**
 * Device Detail Page Redesign
 * - CSS: src/styles/pages/detail.css
 */
export default function DeviceDetailPage() {
  const { deviceId } = useParams()
  const navigate = useNavigate()
  const { tenantStatus } = useAuth()
  const [device, setDevice] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [logs, setLogs] = useState([])
  const [limit, setLimit] = useState(10)
  const [fechaInicio, setFechaInicio] = useState('')
  const [fechaFin, setFechaFin] = useState('')
  const [loading, setLoading] = useState(true)

  const isSuspended = tenantStatus === 'suspendido'

  useEffect(() => {
    // Parallel fetch
    const fetchAll = async () => {
        setLoading(true)
        try {
            // Mock device info fetch (usually this would be await getDevice(deviceId))

            // Fetch Alerts
            const alertsRes = await getAlerts({ device_id: Number(deviceId) })
            setAlerts(alertsRes.data || [])

            // Fetch Logs
            await loadLogs()

        } catch(e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }
    fetchAll()
  }, [deviceId]) // eslint-disable-line react-hooks/exhaustive-deps

  const loadLogs = async () => {
    try {
        const params = new URLSearchParams()
        params.set('limit', limit.toString())
        if (fechaInicio) params.set('fecha_inicio', new Date(fechaInicio).toISOString())
        if (fechaFin) params.set('fecha_fin', new Date(fechaFin).toISOString())

        const res = await client.get(`/devices/${deviceId}/logs?${params.toString()}`)
        setLogs(res.data || [])
    } catch (e) {
        console.warn('Error loading logs', e)
    }
  }

  const handleAction = async (alertId, newStatus) => {
    if (isSuspended) return
    await updateAlertStatus(alertId, { status_operativo: newStatus })
    const alertsRes = await getAlerts({ device_id: Number(deviceId) })
    setAlerts(alertsRes.data || [])
  }

  return (
    <div className="detail-page fade-in">

      {/* Header */}
      <header className="detail-header">
        <div>
            <button
                onClick={() => navigate('/devices')}
                className="back-link"
            >
                ← Volver a equipos
            </button>
            <h1 className="h1">Router Principal #{deviceId}</h1>
            <p className="body-sm text-muted">Detalles operativos y monitoreo en tiempo real</p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="ghost" disabled={isSuspended}>Reiniciar</Button>
            <Button variant="primary" disabled={isSuspended}>Editar Configuración</Button>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="detail-grid">

        {/* Left Column (Main Info & Charts) */}
        <div className="left-column">

            {/* Basic Info Card */}
            <Card>
                <h3 className="h3" style={{ marginBottom: '16px' }}>Información del Sistema</h3>
                <div className="info-grid">
                    <InfoItem label="Dirección IP" value="192.168.88.1" />
                    <InfoItem label="MAC Address" value="B8:69:F4:XX:XX:XX" />
                    <InfoItem label="Ubicación" value="Oficina Central - Rack 1" />
                    <InfoItem label="Uptime" value="14d 2h 12m" />
                    <InfoItem label="Versión Firmware" value="RouterOS v7.1.5" />
                    <InfoItem label="Modelo" value="RB4011iGS+" />
                </div>
            </Card>

            {/* Performance Charts Placeholder */}
            <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <h3 className="h3">Rendimiento</h3>
                    <select style={{ border: 'none', background: 'transparent', color: 'var(--color-text-muted)', fontSize: '13px' }}>
                        <option>Última hora</option>
                        <option>24 horas</option>
                    </select>
                </div>
                <div style={{ height: '200px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '4px' }}>
                    {/* Fake Chart Bars */}
                    {Array.from({ length: 40 }).map((_, i) => (
                        <div key={i} style={{
                            width: '100%',
                            height: `${Math.random() * 80 + 20}%`,
                            backgroundColor: i % 2 === 0 ? 'var(--color-accent-primary)' : 'rgba(0,122,255,0.3)',
                            borderRadius: '2px'
                        }}></div>
                    ))}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', fontSize: '12px', color: 'var(--color-text-muted)' }}>
                    <span>CPU Load: 12%</span>
                    <span>Memory: 45%</span>
                    <span>Temp: 42°C</span>
                </div>
            </Card>

            {/* Logs */}
            <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 className="h3">Logs del Sistema</h3>
                    <Button variant="ghost" size="sm" onClick={() => loadLogs()}>Actualizar</Button>
                </div>

                <div className="filters" style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' }}>
                     <Input type="datetime-local" value={fechaInicio} onChange={e => setFechaInicio(e.target.value)} style={{ marginBottom: 0 }} />
                     <Input type="datetime-local" value={fechaFin} onChange={e => setFechaFin(e.target.value)} style={{ marginBottom: 0 }} />
                </div>

                <div className="logs-container">
                    {logs.length > 0 ? logs.map(l => (
                        <div key={l.id} className="log-entry">
                            <span style={{ color: 'var(--color-accent-primary)' }}>[{l.timestamp_equipo || new Date().toISOString()}]</span> {l.raw_log}
                        </div>
                    )) : (
                        <div style={{ textAlign: 'center', padding: '20px', color: 'var(--color-text-muted)' }}>No hay logs para mostrar</div>
                    )}
                </div>
            </Card>

        </div>

        {/* Right Column (Status & Alerts) */}
        <div className="right-column">

            {/* Status Card */}
            <Card statusColor="success" elevated>
                <div className="status-card-content">
                    <div className="status-label">Estado Actual</div>
                    <div className="status-value">
                        <span className="status-dot-large"></span>
                        ONLINE
                    </div>
                    <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--color-border)', paddingTop: '16px' }}>
                         <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                            <span style={{ fontSize: '20px', fontWeight: 600 }}>99.9%</span>
                            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>SLA Mes</span>
                         </div>
                         <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                            <span style={{ fontSize: '20px', fontWeight: 600 }}>2</span>
                            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Alertas</span>
                         </div>
                    </div>
                </div>
            </Card>

            {/* Quick Actions */}
            <Card>
                <h3 className="h3" style={{ marginBottom: '16px' }}>Acciones Rápidas</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <Button variant="secondary" fullWidth disabled={isSuspended}>Ver Tráfico en Vivo</Button>
                    <Button variant="secondary" fullWidth disabled={isSuspended}>Descargar Backup</Button>
                    <Button variant="secondary" fullWidth disabled={isSuspended}>Test de Velocidad</Button>
                    <div style={{ height: '1px', background: 'var(--color-border)', margin: '8px 0' }}></div>
                    <Button variant="danger" fullWidth disabled={isSuspended}>Apagar Interfaz</Button>
                </div>
            </Card>

            {/* Active Alerts */}
            <Card>
                <h3 className="h3" style={{ marginBottom: '16px' }}>Alertas Activas</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {alerts.length > 0 ? alerts.map(a => (
                        <div key={a.id} className={`alert-item ${a.estado === 'Alerta Crítica' ? 'alert-critical' : 'alert-warning'}`}>
                            <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: '4px' }}>{a.mensaje}</div>
                            <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>{new Date(a.fecha_detectado).toLocaleString()}</div>

                            {!isSuspended && (
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button onClick={() => handleAction(a.id, 'en_revision')} style={{ fontSize: '11px', color: 'var(--color-accent-primary)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Revisar</button>
                                    <button onClick={() => handleAction(a.id, 'resuelto')} style={{ fontSize: '11px', color: 'var(--color-accent-secondary)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Resolver</button>
                                </div>
                            )}
                        </div>
                    )) : (
                        <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', textAlign: 'center', padding: '12px' }}>
                            Sin alertas activas
                        </div>
                    )}
                </div>
            </Card>

        </div>

      </div>
    </div>
  )
}

function InfoItem({ label, value }) {
    return (
        <div className="info-item">
            <span className="info-label">{label}</span>
            <span className="info-value">{value}</span>
        </div>
    )
}
