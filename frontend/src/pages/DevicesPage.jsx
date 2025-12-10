import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDevices, createDevice } from '../api/deviceApi.js'
import UpsellModal from '../components/UpsellModal.jsx'
import useAuth from '../hooks/useAuth.js'
import Button from '../components/ui/Button.jsx'
import Input from '../components/ui/Input.jsx'
import Card from '../components/ui/Card.jsx'

/**
 * Devices Page Redesign
 * - CSS: src/styles/pages/devices.css
 */
export default function DevicesPage() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState('table') // 'table' | 'grid'
  const [searchTerm, setSearchTerm] = useState('')

  // Form State
  const [form, setForm] = useState({ name: '', ip_address: '', port: 22, username: '', password: '' })
  const [isFormVisible, setIsFormVisible] = useState(false)
  const [showUpsell, setShowUpsell] = useState(false)

  const { tenantStatus } = useAuth()
  const navigate = useNavigate()
  const isSuspended = tenantStatus === 'suspendido'

  const load = async () => {
    setLoading(true)
    try {
      const res = await getDevices()
      setDevices(res.data || [])
    } catch (e) {
      console.error('Error loading devices', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const onAdd = async (e) => {
    e.preventDefault()
    if (isSuspended) return

    try {
      await createDevice({
        name: form.name,
        ip_address: form.ip_address,
        port: Number(form.port) || 22,
        username: form.username,
        password: form.password
      })
      setForm({ name: '', ip_address: '', port: 22, username: '', password: '' })
      setIsFormVisible(false)
      load()
    } catch (err) {
      if (err.upsell) setShowUpsell(true)
      else alert('Error al crear equipo')
    }
  }

  const filteredDevices = devices.filter(d =>
    d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.ip_address.includes(searchTerm)
  )

  return (
    <div className="devices-page fade-in">
      {/* Header & Controls */}
      <div className="devices-header-container">
        <div>
            <h1 className="h1">Equipos</h1>
            <p className="body-sm text-muted">Administra y monitorea tu infraestructura</p>
        </div>

        <div className="devices-controls">
            <Input
                placeholder="Buscar..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
            />

            <div className="view-toggle">
                <button
                    onClick={() => setViewMode('table')}
                    className={`view-toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
                </button>
                <button
                    onClick={() => setViewMode('grid')}
                    className={`view-toggle-btn ${viewMode === 'grid' ? 'active' : ''}`}
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
                </button>
            </div>

            <Button onClick={() => setIsFormVisible(!isFormVisible)} variant="primary" leftIcon={<span style={{ fontSize: '18px', fontWeight: 'bold' }}>+</span>}>
                Nuevo Equipo
            </Button>
        </div>
      </div>

      {/* Add Device Form (Collapsible) */}
      {isFormVisible && (
        <Card elevated className="fade-in">
            <h3 className="h3" style={{ marginBottom: '16px' }}>Agregar Nuevo Dispositivo</h3>
            <form onSubmit={onAdd} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', alignItems: 'end' }}>
                <Input label="Nombre" value={form.name} onChange={e => setForm({...form, name: e.target.value})} required placeholder="Ej. Router Borde" />
                <Input label="Dirección IP" value={form.ip_address} onChange={e => setForm({...form, ip_address: e.target.value})} required placeholder="192.168.1.1" />
                <Input label="Puerto SSH" type="number" value={form.port} onChange={e => setForm({...form, port: e.target.value})} placeholder="22" />
                <Input label="Usuario" value={form.username} onChange={e => setForm({...form, username: e.target.value})} required placeholder="admin" />
                <Input label="Contraseña" type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} required placeholder="••••••" />
                <div style={{ display: 'flex', gap: '8px' }}>
                    <Button type="button" variant="secondary" onClick={() => setIsFormVisible(false)}>Cancelar</Button>
                    <Button type="submit" variant="primary" disabled={isSuspended}>Guardar Equipo</Button>
                </div>
            </form>
        </Card>
      )}

      {/* Device List */}
      {viewMode === 'table' ? (
          <Card style={{ padding: 0, overflow: 'hidden' }}>
            <div className="table-container">
                <table className="table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                        <tr style={{ background: 'var(--color-bg-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
                            <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Nombre</th>
                            <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>IP / Puerto</th>
                            <th style={{ textAlign: 'left', padding: '12px 16px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Estado</th>
                            <th style={{ textAlign: 'right', padding: '12px 16px', fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredDevices.map(d => (
                            <tr key={d.id} className="table-row" onClick={() => navigate(`/devices/${d.id}`)} style={{ cursor: 'pointer', borderBottom: '1px solid var(--color-border)', transition: 'background 0.1s' }}>
                                <style>{`.table-row:hover { background-color: var(--color-bg-tertiary); }`}</style>
                                <td style={{ padding: '12px 16px', fontWeight: 500 }}>{d.name}</td>
                                <td style={{ padding: '12px 16px', fontFamily: 'monospace', color: 'var(--color-text-secondary)' }}>{d.ip_address}:{d.port}</td>
                                <td style={{ padding: '12px 16px' }}><StatusBadge status={d.health_status || 'unknown'} /></td>
                                <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                                    <button style={{ background: 'transparent', border: 'none', color: 'var(--color-accent-primary)', cursor: 'pointer', fontWeight: 500 }}>Detalle</button>
                                </td>
                            </tr>
                        ))}
                         {filteredDevices.length === 0 && !loading && (
                            <tr><td colSpan="4" style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>No se encontraron equipos</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
          </Card>
      ) : (
          <div className="devices-grid">
              {filteredDevices.map(d => (
                  <Card key={d.id} interactive onClick={() => navigate(`/devices/${d.id}`)} statusColor={getStatusColor(d.health_status)}>
                      <div className="device-card-header">
                          <div className="device-icon-wrapper">
                             <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                          </div>
                          <StatusBadge status={d.health_status || 'unknown'} />
                      </div>
                      <h3 className="device-name">{d.name}</h3>
                      <p className="device-ip">{d.ip_address}</p>
                  </Card>
              ))}
          </div>
      )}

      <UpsellModal open={showUpsell} onClose={() => setShowUpsell(false)} />
    </div>
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
        <span style={{
            backgroundColor: s.bg, color: s.color,
            padding: '2px 8px', borderRadius: '12px',
            fontSize: '11px', fontWeight: 600
        }}>
            {s.label}
        </span>
    )
}

function getStatusColor(status) {
    if (status === 'verde') return 'success'
    if (status === 'amarillo') return 'warning'
    if (status === 'rojo') return 'danger'
    return null
}
