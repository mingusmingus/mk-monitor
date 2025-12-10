import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getAlerts, updateAlertStatus } from '../api/alertApi.js'
import client from '../api/client.js'
import useAuth from '../hooks/useAuth.js'
import Card from '../components/ui/Card.jsx'
import Button from '../components/ui/Button.jsx'
import Input from '../components/ui/Input.jsx'
import AIDiagnosisCard from '../components/AIDiagnosisCard.jsx'
import InterfacesTable from '../components/InterfacesTable.jsx'

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
  const [activeTab, setActiveTab] = useState('overview') // 'overview', 'interfaces', 'neighbors'

  const isSuspended = tenantStatus === 'suspendido'

  // Mock data for AI Diagnosis and Interfaces since backend evolution is mentioned
  // Ideally this would come from `device.forensic_data` or similar.
  const [forensicData, setForensicData] = useState(null)

  useEffect(() => {
    // Parallel fetch
    const fetchAll = async () => {
        setLoading(true)
        try {
            // Mock device info fetch (usually this would be await getDevice(deviceId))
            // Simulating fetching a device object that contains the new structure
            const mockDevice = {
                id: deviceId,
                ip_address: "192.168.88.1",
                mac_address: "B8:69:F4:XX:XX:XX",
                location: "Oficina Central - Rack 1",
                uptime: "14d 2h 12m",
                firmware: "RouterOS v7.1.5",
                model: "RB4011iGS+",
                // Forensic Data Mining Structure
                forensic_data: {
                    analysis: {
                        severity: "Alerta Menor",
                        root_cause: "High latency detected on WAN interface due to saturation.",
                        recommendations: ["Check ISP bandwidth", "Review QoS policies"]
                    },
                    telemetry: {
                        cpu_load: 12,
                        memory_usage: 45,
                        uptime: 123456,
                        interfaces: [
                            { name: "ether1", type: "ether", mac_address: "00:00:00:00:00:01", mtu: 1500, tx_byte: 1234567, rx_byte: 7654321, running: true, stats: { fcs_error: 0, collisions: 0 } },
                            { name: "wlan1", type: "wlan", mac_address: "00:00:00:00:00:02", mtu: 1500, tx_byte: 12345, rx_byte: 54321, running: true, stats: { fcs_error: 50, collisions: 2 } }
                        ],
                        system: {
                            health: {
                                voltage: 24.1,
                                temperature: 42
                            }
                        },
                        neighbors: [
                            { interface: "ether2", ip: "192.168.88.2", identity: "Switch-Core" },
                            { interface: "wlan1", ip: "192.168.88.50", identity: "AP-Lobby" }
                        ]
                    }
                }
            }

            // Try to fetch real data if API available, else use mock
            // In a real scenario, we would do:
            // const res = await client.get(`/devices/${deviceId}`)
            // setDevice(res.data)
            // But for this task, we set the mock with the structure we need to visualize.
            setDevice(mockDevice)
            setForensicData(mockDevice.forensic_data)


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

  // Safe access to nested properties
  const systemHealth = forensicData?.telemetry?.system?.health
  const neighbors = forensicData?.telemetry?.neighbors || []
  const interfaces = forensicData?.telemetry?.interfaces || []

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

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: '24px', borderBottom: '1px solid var(--color-border)', marginBottom: '24px', paddingBottom: '0' }}>
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
            style={{
                background: 'none', border: 'none', padding: '12px 0',
                borderBottom: activeTab === 'overview' ? '2px solid var(--color-accent-primary)' : '2px solid transparent',
                fontWeight: activeTab === 'overview' ? 600 : 400,
                color: activeTab === 'overview' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                cursor: 'pointer'
            }}
          >
            Visión General
          </button>
          <button
            className={`tab-btn ${activeTab === 'interfaces' ? 'active' : ''}`}
            onClick={() => setActiveTab('interfaces')}
            style={{
                background: 'none', border: 'none', padding: '12px 0',
                borderBottom: activeTab === 'interfaces' ? '2px solid var(--color-accent-primary)' : '2px solid transparent',
                fontWeight: activeTab === 'interfaces' ? 600 : 400,
                color: activeTab === 'interfaces' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                cursor: 'pointer'
            }}
          >
            Interfaces
          </button>
           <button
            className={`tab-btn ${activeTab === 'neighbors' ? 'active' : ''}`}
            onClick={() => setActiveTab('neighbors')}
            style={{
                background: 'none', border: 'none', padding: '12px 0',
                borderBottom: activeTab === 'neighbors' ? '2px solid var(--color-accent-primary)' : '2px solid transparent',
                fontWeight: activeTab === 'neighbors' ? 600 : 400,
                color: activeTab === 'neighbors' ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                cursor: 'pointer'
            }}
          >
            Vecinos
          </button>
      </div>


      {/* Main Grid Layout */}
      <div className="detail-grid">

        {/* Left Column (Main Info & Charts) */}
        <div className="left-column">

            {/* AI Diagnosis Card */}
            {forensicData && (
                <AIDiagnosisCard data={forensicData} />
            )}

            {activeTab === 'overview' && (
                <>
                    {/* Basic Info Card */}
                    <Card>
                        <h3 className="h3" style={{ marginBottom: '16px' }}>Información del Sistema</h3>
                        <div className="info-grid">
                            <InfoItem label="Dirección IP" value={device?.ip_address || "Loading..."} />
                            <InfoItem label="MAC Address" value={device?.mac_address || "Loading..."} />
                            <InfoItem label="Ubicación" value={device?.location || "Loading..."} />
                            <InfoItem
                                label="Uptime"
                                value={
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <span>{device?.uptime || "Loading..."}</span>
                                        {/* Hardware Widget: Voltage & Temperature */}
                                        {systemHealth && (
                                            <div style={{ display: 'flex', gap: '8px', fontSize: '12px' }}>
                                                {systemHealth.voltage && (
                                                    <span title={`Voltage: ${systemHealth.voltage}V`} style={{ display: 'flex', alignItems: 'center', gap: '2px', color: 'var(--color-text-secondary)' }}>
                                                        <span style={{ color: 'var(--color-accent-warning)' }}>⚡</span>
                                                        {systemHealth.voltage}V
                                                    </span>
                                                )}
                                                {systemHealth.temperature && (
                                                    <span title={`Temperature: ${systemHealth.temperature}°C`} style={{ display: 'flex', alignItems: 'center', gap: '2px', color: 'var(--color-text-secondary)' }}>
                                                        <span style={{ color: getTempColor(systemHealth.temperature) }}>🌡</span>
                                                        {systemHealth.temperature}°C
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                }
                            />
                            <InfoItem label="Versión Firmware" value={device?.firmware || "Loading..."} />
                            <InfoItem label="Modelo" value={device?.model || "Loading..."} />
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
                            <span>CPU Load: {forensicData?.telemetry?.cpu_load ?? 12}%</span>
                            <span>Memory: {forensicData?.telemetry?.memory_usage ?? 45}%</span>
                            <span>Temp: {systemHealth?.temperature ?? 42}°C</span>
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
                </>
            )}

            {activeTab === 'interfaces' && (
                <Card>
                    <h3 className="h3" style={{ marginBottom: '16px' }}>Interfaces de Red</h3>
                    <InterfacesTable interfaces={interfaces} />
                </Card>
            )}

            {activeTab === 'neighbors' && (
                <Card>
                    <h3 className="h3" style={{ marginBottom: '16px' }}>Vecinos Detectados</h3>
                    {neighbors && neighbors.length > 0 ? (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                                <thead>
                                    <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                                        <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Interfaz</th>
                                        <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>IP</th>
                                        <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Dispositivo (Identity)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {neighbors.map((n, i) => (
                                        <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                                            <td style={{ padding: '12px 8px', fontWeight: 500 }}>{n.interface}</td>
                                            <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>{n.ip}</td>
                                            <td style={{ padding: '12px 8px', color: 'var(--color-text-secondary)' }}>{n.identity || '-'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                            No neighbors detected.
                        </div>
                    )}
                </Card>
            )}

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
                            <span style={{ fontSize: '20px', fontWeight: 600 }}>{alerts.length}</span>
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

function getTempColor(temp) {
    if (temp < 40) return 'var(--color-accent-secondary)'
    if (temp < 60) return 'var(--color-accent-warning)'
    return 'var(--color-accent-danger)'
}
