import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getAlerts, updateAlertStatus } from '../api/alertApi.js'
import client from '../api/client.js'
import useAuth from '../hooks/useAuth.js'
import Card from '../components/ui/Card.jsx'
import Button from '../components/ui/Button.jsx'
import Input from '../components/ui/Input.jsx'

// Nuevos componentes visuales
import AIDiagnosisCard from '../components/AIDiagnosisCard.jsx'
import VitalSigns from '../components/VitalSigns.jsx'
import InterfacesTable from '../components/InterfacesTable.jsx'
import NetworkTopology from '../components/NetworkTopology.jsx'

// Estilos globales de la página (layout)
import '../styles/pages/detail.css'

/**
 * Device Detail Page (Rediseñada - Fase 2)
 *
 * Página de detalle de un dispositivo. Integra visualización forense avanzada.
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
  const [deleting, setDeleting] = useState(false)

  const isSuspended = tenantStatus === 'suspendido'
  const [forensicData, setForensicData] = useState(null)

  // MOCK DATA GENERATOR (For fallback/dev)
  const getMockForensicData = (baseDevice) => ({
        analysis: {
            severity: "Alerta Menor",
            root_cause: "Latencia intermitente detectada en interfaz WAN.",
            summary: "El dispositivo opera dentro de parámetros normales, aunque se detectó saturación puntual en la interfaz WAN durante las últimas 2 horas.",
            recommendations: ["Verificar ancho de banda ISP", "Revisar políticas QoS", "Monitorear colas de tráfico"],
            confidence_score: 0.92
        },
        security_audit: {
            risk_score: 3,
            insecure_ports: [21, 23] // FTP, Telnet open example
        },
        telemetry: {
            cpu_load: 12,
            memory_usage: 45,
            uptime: 123456,
            interfaces: [
                { name: "ether1-wan", type: "ether", mac_address: "B8:69:F4:A1:B2:C1", mtu: 1500, tx_byte: 123456789, rx_byte: 987654321, running: true, stats: { fcs_error: 0, collisions: 0 } },
                { name: "ether2-lan", type: "ether", mac_address: "B8:69:F4:A1:B2:C2", mtu: 1500, tx_byte: 54321, rx_byte: 12345, running: true, stats: { fcs_error: 50, collisions: 2 } },
                { name: "wlan1", type: "wlan", mac_address: "B8:69:F4:A1:B2:C3", mtu: 1500, tx_byte: 0, rx_byte: 0, running: false, stats: {} }
            ],
            system: {
                health: {
                    voltage: 23.5, // Low voltage test
                    temperature: 42
                }
            },
            neighbors: [
                { interface: "ether2-lan", ip: "192.168.88.2", identity: "SW-Core-01", platform: "MikroTik", version: "6.48.6", board: "CRS326" },
                { interface: "ether2-lan", ip: "192.168.88.200", identity: "UAP-AC-Pro", platform: "Ubiquiti", version: "6.0.21" },
                { interface: "ether1-wan", ip: "10.0.0.1", identity: "Cisco-ISR", platform: "Cisco IOS", version: "15.1" }
            ]
        }
  })


  useEffect(() => {
    const fetchAll = async () => {
        setLoading(true)
        try {
            // Fetch real device data
            const res = await client.get(`/devices/${deviceId}`)
            const deviceData = res.data
            setDevice(deviceData)

            // Intenta usar data forense real si el backend la envía.
            // Si no (porque el backend está en desarrollo o no tiene data), usa el mock para visualización.
            if (deviceData.forensic_data) {
                setForensicData(deviceData.forensic_data)
            } else if (process.env.NODE_ENV === 'development') {
                // Fallback para desarrollo: Visualizar UI con datos mock si no hay reales
                setForensicData(getMockForensicData(deviceData))
            }

            // Cargar Alertas
            const alertsRes = await getAlerts({ device_id: Number(deviceId) })
            setAlerts(alertsRes.data || [])

            // Cargar Logs
            await loadLogs()

        } catch(e) {
            console.error("Error fetching device details", e)
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
        console.warn('Error cargando logs', e)
    }
  }

  const handleDelete = async () => {
      if (!window.confirm("¿Estás seguro de que deseas eliminar este equipo? Esta acción moverá el equipo a la papelera y dejará de ser monitoreado.")) {
          return
      }

      setDeleting(true)
      try {
          await client.delete(`/devices/${deviceId}`)
          navigate('/devices')
      } catch (e) {
          console.error("Error deleting device", e)
          alert("Hubo un error al eliminar el dispositivo.")
          setDeleting(false)
      }
  }

  const handleAction = async (alertId, newStatus) => {
    if (isSuspended) return
    await updateAlertStatus(alertId, { status_operativo: newStatus })
    const alertsRes = await getAlerts({ device_id: Number(deviceId) })
    setAlerts(alertsRes.data || [])
  }

  // Safe accessors
  const systemHealth = forensicData?.telemetry?.system?.health
  const cpuLoad = forensicData?.telemetry?.cpu_load
  const neighbors = forensicData?.telemetry?.neighbors || []
  const interfaces = forensicData?.telemetry?.interfaces || []

  return (
    <div className="detail-page fade-in" style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>

      {/* Encabezado */}
      <header className="detail-header" style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
                <button
                    onClick={() => navigate('/devices')}
                    className="back-link"
                    style={{ marginBottom: '8px', color: 'var(--color-text-secondary)', display: 'block' }}
                >
                    ← Volver a equipos
                </button>
                <h1 className="h1" style={{ fontSize: '28px', marginBottom: '4px' }}>
                    {device?.identity || device?.model || `Router #${deviceId}`}
                </h1>
                <p className="body-sm text-muted">
                    {device?.ip_address} • {device?.location}
                </p>

                {/* Vital Signs Widget Integration */}
                {!loading && (
                    <div style={{ marginTop: '8px', maxWidth: '400px' }}>
                        <VitalSigns health={systemHealth} cpuLoad={cpuLoad} />
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
                <Button variant="danger" disabled={isSuspended || deleting} loading={deleting} onClick={handleDelete}>
                    Eliminar
                </Button>
                <Button variant="ghost" disabled={isSuspended}>Reiniciar</Button>
                <Button variant="primary" disabled={isSuspended}>Configuración</Button>
            </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: '32px', borderBottom: '1px solid var(--color-border)', marginBottom: '32px' }}>
          {['overview', 'interfaces', 'neighbors'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                    background: 'none',
                    border: 'none',
                    padding: '12px 0',
                    borderBottom: activeTab === tab ? '2px solid var(--color-accent-primary)' : '2px solid transparent',
                    fontWeight: activeTab === tab ? 600 : 400,
                    color: activeTab === tab ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                    cursor: 'pointer',
                    textTransform: 'capitalize',
                    fontSize: '14px',
                    transition: 'color 0.2s, border-color 0.2s'
                }}
              >
                {tab === 'overview' ? 'Visión General' : tab === 'interfaces' ? 'Interfaces de Red' : 'Topología (Vecinos)'}
              </button>
          ))}
      </div>


      <div className="detail-grid" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>

        {/* Left Column */}
        <div className="left-column">

            {activeTab === 'overview' && (
                <>
                    <AIDiagnosisCard data={forensicData} loading={loading} />

                    <Card>
                        <h3 className="h3" style={{ marginBottom: '16px' }}>Logs Recientes</h3>
                        <div className="logs-container" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                            {logs.length > 0 ? logs.map(l => (
                                <div key={l.id} className="log-entry" style={{ fontSize: '12px', padding: '8px 0', borderBottom: '1px solid var(--color-border-subtle)' }}>
                                    <span className="font-mono" style={{ color: 'var(--color-accent-primary)', marginRight: '8px' }}>
                                        {new Date(l.timestamp_equipo || l.created_at).toLocaleTimeString()}
                                    </span>
                                    {l.raw_log}
                                </div>
                            )) : (
                                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--color-text-muted)' }}>No hay logs recientes.</div>
                            )}
                        </div>
                    </Card>
                </>
            )}

            {activeTab === 'interfaces' && (
                <Card>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 className="h3">Interfaces Físicas & Lógicas</h3>
                        <span className="body-sm text-muted">{interfaces.length} interfaces detectadas</span>
                    </div>
                    <InterfacesTable interfaces={interfaces} />
                </Card>
            )}

            {activeTab === 'neighbors' && (
                <Card>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 className="h3">Descubrimiento de Vecinos</h3>
                        <span className="body-sm text-muted">Protocolos: CDP, LLDP, MNDP</span>
                    </div>
                    <NetworkTopology neighbors={neighbors} />
                </Card>
            )}

        </div>

        {/* Right Column (Status & Quick Actions) */}
        <div className="right-column">

            <Card elevated>
                <div style={{ paddingBottom: '16px', marginBottom: '16px', borderBottom: '1px solid var(--color-border)' }}>
                     <div className="body-sm text-muted">Estado General</div>
                     <div style={{ fontSize: '24px', fontWeight: 600, color: 'var(--color-accent-success)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                         <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: 'var(--color-accent-success)', boxShadow: '0 0 8px var(--color-accent-success)' }}></div>
                         OPERATIVO
                     </div>
                </div>

                <h4 className="body-sm" style={{ fontWeight: 600, marginBottom: '12px' }}>Alertas Activas ({alerts.length})</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {alerts.slice(0, 3).map(a => (
                        <div key={a.id} style={{ padding: '8px', background: 'var(--color-bg-secondary)', borderRadius: '6px', fontSize: '12px', borderLeft: '3px solid var(--color-accent-warning)' }}>
                            {a.mensaje}
                        </div>
                    ))}
                    {alerts.length === 0 && <span className="text-muted" style={{ fontSize: '12px' }}>Todo en orden.</span>}
                </div>
            </Card>

            <Card style={{ marginTop: '24px' }}>
                <h3 className="h3" style={{ marginBottom: '16px' }}>Detalles Técnicos</h3>
                <div className="info-grid" style={{ display: 'grid', gap: '12px' }}>
                    <InfoRow label="Modelo" value={device?.model} />
                    <InfoRow label="Firmware" value={device?.firmware} />
                    <InfoRow label="Arquitectura" value="ARM 64bit" />
                    <InfoRow label="Serial" value="HB88291238" />
                </div>
            </Card>

        </div>

      </div>
    </div>
  )
}

function InfoRow({ label, value }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
            <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
            <span className="font-mono">{value || '-'}</span>
        </div>
    )
}
