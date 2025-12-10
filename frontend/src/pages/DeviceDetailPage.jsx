import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getAlerts, updateAlertStatus } from '../api/alertApi.js'
import client from '../api/client.js'
import useAuth from '../hooks/useAuth.js'
import Card from '../components/ui/Card.jsx'
import Button from '../components/ui/Button.jsx'
import Input from '../components/ui/Input.jsx'
import AIDiagnosisCard from '../components/AIDiagnosisCard.jsx'
import HealthWidget from '../components/DeviceHealthIndicator.jsx'

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

  // New Forensic Data State
  const [miningData, setMiningData] = useState(null)
  const [activeTab, setActiveTab] = useState('overview') // 'overview', 'neighbors', 'interfaces'

  const isSuspended = tenantStatus === 'suspendido'

  useEffect(() => {
    // Parallel fetch
    const fetchAll = async () => {
        setLoading(true)
        try {
            // Mock device info fetch (usually this would be await getDevice(deviceId))
            // In a real scenario, we might call an endpoint that triggers mining or gets last mined state
            // For now, we simulate fetching the device detail which includes the new fields if backend provides them
            // or we fetch the "latest forensic report" alert.

            // Fetch Alerts
            const alertsRes = await getAlerts({ device_id: Number(deviceId) })
            setAlerts(alertsRes.data || [])

            // Fetch Logs
            await loadLogs()

            // Fetch Mining Data (Mocking backend response structure for now)
            // Ideally: const miningRes = await client.get(`/devices/${deviceId}/forensics/latest`)
            // We will pretend the device object has it or we just create a placeholder
            // to demonstrate the UI.

            // Mock Data for UI demonstration
            setMiningData({
                context: {
                    identity: "MikroTik-Core-Router",
                    version: "7.14.3",
                    uptime: "4w 2d 1h",
                    cpu_load: "15%",
                    board_name: "CCR1009"
                },
                health: {
                    voltage: "24.1",
                    temperature: "38"
                },
                interfaces: [
                   { name: "ether1", type: "ether", rx_fcs_error: "0", speed: "1Gbps", running: true },
                   { name: "ether2", type: "ether", rx_fcs_error: "532", speed: "100Mbps", running: true, comment: "Link to Switch" }, // Error example
                   { name: "wlan1", type: "wifi", rx_fcs_error: "0", speed: "", running: true }
                ],
                layer3: {
                    neighbors: [
                        { interface: "ether2", ip: "192.168.88.254", identity: "SW-Access-01", platform: "MikroTik" },
                        { interface: "ether3", ip: "10.0.0.1", identity: "Uplink-ISP", platform: "Cisco" }
                    ],
                    active_protocols: ["OSPF", "BGP"]
                },
                diagnosis: {
                    estado: "Alerta Severa",
                    analysis: "Detectado alto número de errores FCS en ether2. Esto indica casi con certeza un cable de red dañado o conectores defectuosos entre el Router y el Switch de Acceso. Además, el enlace negoció a 100Mbps en lugar de 1Gbps.",
                    telemetry: {
                        resource_stress: "CPU Normal (15%)",
                        interface_errors: { "ether2": "FCS: 532, Autoneg: 100Mbps (Cap: 1Gbps)" }
                    },
                    recommendations: [
                        "Reemplazar cable patchcord en ether2",
                        "Verificar crimpado de conectores RJ45",
                        "Revisar logs de flapping en el switch vecino"
                    ]
                }
            })

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
      <header className="detail-header" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
                <button
                    onClick={() => navigate('/devices')}
                    className="back-link"
                >
                    ← Volver a equipos
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '8px' }}>
                    <h1 className="h1" style={{ margin: 0 }}>
                        {miningData?.context?.identity || `Router #${deviceId}`}
                    </h1>
                    {miningData && (
                        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                            <span className="body-sm text-muted">|</span>
                            <span className="body-sm text-secondary">{miningData.context?.board_name}</span>
                            <span className="body-sm text-muted">|</span>
                            <HealthWidget health={miningData.health} />
                        </div>
                    )}
                </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
                <Button variant="ghost" disabled={isSuspended}>Reiniciar</Button>
                <Button variant="primary" disabled={isSuspended}>Minería Forense</Button>
            </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '24px', marginTop: '24px', borderBottom: '1px solid var(--color-border)' }}>
            <TabButton label="Resumen" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
            <TabButton label="Interfaces" active={activeTab === 'interfaces'} onClick={() => setActiveTab('interfaces')} />
            <TabButton label="Vecinos (Topology)" active={activeTab === 'neighbors'} onClick={() => setActiveTab('neighbors')} />
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="detail-grid">

        {/* Left Column (Main Info & Charts) */}
        <div className="left-column">

            {/* AI Diagnosis Card (Top Priority) */}
            {activeTab === 'overview' && miningData?.diagnosis && (
                 <div style={{ marginBottom: '24px' }}>
                    <AIDiagnosisCard diagnosis={miningData.diagnosis} onAction={(act) => console.log(act)} />
                 </div>
            )}

            {activeTab === 'overview' && (
                <>
                    {/* Basic Info Card */}
                    <Card>
                        <h3 className="h3" style={{ marginBottom: '16px' }}>Información del Sistema</h3>
                        <div className="info-grid">
                            <InfoItem label="Dirección IP" value="192.168.88.1" /> {/* TODO: Real IP */}
                            <InfoItem label="Uptime" value={miningData?.context?.uptime || "Unknown"} />
                            <InfoItem label="Versión Firmware" value={miningData?.context?.version || "Unknown"} />
                            <InfoItem label="CPU Load" value={miningData?.context?.cpu_load || "0%"} />
                            <InfoItem label="Protocolos Activos" value={miningData?.layer3?.active_protocols?.join(", ") || "Ninguno"} />
                        </div>
                    </Card>

                    {/* Logs */}
                    <Card>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <h3 className="h3">Logs del Sistema</h3>
                            <Button variant="ghost" size="sm" onClick={() => loadLogs()}>Actualizar</Button>
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

            {activeTab === 'neighbors' && (
                <Card>
                    <h3 className="h3" style={{ marginBottom: '16px' }}>Vecinos Descubiertos (CDP/LLDP/MNDP)</h3>
                    <table className="w-full" style={{ borderCollapse: 'collapse', fontSize: '14px' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>Interfaz</th>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>IP Address</th>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>Identidad</th>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>Plataforma</th>
                            </tr>
                        </thead>
                        <tbody>
                            {miningData?.layer3?.neighbors?.map((n, i) => (
                                <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                                    <td style={{ padding: '12px 8px', fontWeight: 500 }}>{n.interface}</td>
                                    <td style={{ padding: '12px 8px' }}>{n.ip}</td>
                                    <td style={{ padding: '12px 8px' }}>{n.identity}</td>
                                    <td style={{ padding: '12px 8px', color: 'var(--color-text-secondary)' }}>{n.platform}</td>
                                </tr>
                            ))}
                            {(!miningData?.layer3?.neighbors || miningData.layer3.neighbors.length === 0) && (
                                <tr>
                                    <td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                                        No se detectaron vecinos.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </Card>
            )}

            {activeTab === 'interfaces' && (
                <Card>
                    <h3 className="h3" style={{ marginBottom: '16px' }}>Estado de Interfaces</h3>
                    <table className="w-full" style={{ borderCollapse: 'collapse', fontSize: '14px' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>Nombre</th>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>Tipo</th>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>Velocidad</th>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>Salud Física</th>
                                <th style={{ padding: '8px', color: 'var(--color-text-secondary)' }}>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {miningData?.interfaces?.map((iface, i) => {
                                const hasErrors = parseInt(iface.rx_fcs_error || 0) > 0;
                                return (
                                    <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                                        <td style={{ padding: '12px 8px', fontWeight: 500 }}>{iface.name}</td>
                                        <td style={{ padding: '12px 8px', color: 'var(--color-text-muted)' }}>{iface.type}</td>
                                        <td style={{ padding: '12px 8px' }}>{iface.speed || '-'}</td>
                                        <td style={{ padding: '12px 8px' }}>
                                            {hasErrors ? (
                                                <div
                                                    className="tooltip-container"
                                                    title={`Posible daño en cable (FCS: ${iface.rx_fcs_error})`}
                                                    style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'help' }}
                                                >
                                                    <span style={{
                                                        display: 'inline-block',
                                                        width: '8px',
                                                        height: '8px',
                                                        borderRadius: '50%',
                                                        backgroundColor: 'var(--color-accent-warning)'
                                                    }}></span>
                                                    <span style={{ color: 'var(--color-accent-warning)', fontSize: '12px', fontWeight: 600 }}>Error</span>
                                                </div>
                                            ) : (
                                                <span style={{ color: 'var(--color-accent-success)', fontSize: '12px' }}>OK</span>
                                            )}
                                        </td>
                                        <td style={{ padding: '12px 8px' }}>
                                            <span style={{
                                                color: iface.running ? 'var(--color-accent-secondary)' : 'var(--color-text-muted)',
                                                fontWeight: 500
                                            }}>
                                                {iface.running ? 'Running' : 'Down'}
                                            </span>
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                </Card>
            )}

        </div>

        {/* Right Column (Status & Alerts) - Keeps visible on all tabs usually, or mostly overview */}
        <div className="right-column">

            {/* Status Card */}
            <Card statusColor="success" elevated>
                <div className="status-card-content">
                    <div className="status-label">Estado Actual</div>
                    <div className="status-value">
                        <span className="status-dot-large"></span>
                        ONLINE
                    </div>
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

function TabButton({ label, active, onClick }) {
    return (
        <button
            onClick={onClick}
            style={{
                background: 'none',
                border: 'none',
                padding: '0 0 12px 0',
                margin: 0,
                fontSize: '14px',
                fontWeight: active ? 600 : 400,
                color: active ? 'var(--color-accent-primary)' : 'var(--color-text-secondary)',
                borderBottom: active ? '2px solid var(--color-accent-primary)' : '2px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.2s'
            }}
        >
            {label}
        </button>
    )
}
