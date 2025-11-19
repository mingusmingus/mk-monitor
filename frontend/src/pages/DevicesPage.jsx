import React, { useEffect, useState } from 'react'
import { getDevices, createDevice } from '../api/deviceApi.js'
import DeviceHealthIndicator from '../components/DeviceHealthIndicator.jsx'
import UpsellModal from '../components/UpsellModal.jsx'
import useAuth from '../hooks/useAuth.js'
import Button from '../components/ui/Button.jsx'
import TextField from '../components/ui/TextField.jsx'

// Listado y alta de equipos. Si supera límite -> Upsell.
export default function DevicesPage() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Añadir username/password reales en el formulario
  const [form, setForm] = useState({ name: '', ip_address: '', port: 22, username: '', password: '' })
  const [showUpsell, setShowUpsell] = useState(false)
  const { tenantStatus } = useAuth()
  const isSuspended = tenantStatus === 'suspendido'

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getDevices()
      setDevices(res.data || [])
    } catch (e) {
      setError('Error al cargar dispositivos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const onAdd = async (e) => {
    e.preventDefault()
    if (isSuspended) {
      alert('Acción bloqueada: cuenta suspendida')
      return
    }
    try {
      // Enviar credenciales en claro; el backend las cifra en reposo y NUNCA las devuelve.
      await createDevice({
        name: form.name,
        ip_address: form.ip_address,
        port: Number(form.port) || 22,
        username: form.username,
        password: form.password
      })
      setForm({ name: '', ip_address: '', port: 22, username: '', password: '' })
      load()
    } catch (err) {
      if (err.upsell) {
        setShowUpsell(true)
      } else {
        alert('Error al crear equipo')
      }
    }
  }

  return (
    <div className="col" style={{ gap: 'var(--spacing-6)' }}>
      <header>
        <h1 style={{ fontSize: 'var(--font-2xl)', fontWeight: 600 }}>Dispositivos</h1>
        <p className="muted">Gestiona tus equipos MikroTik y monitorea su estado.</p>
      </header>

      <div className="card">
        <h3 style={{ marginBottom: 'var(--spacing-4)' }}>Nuevo Dispositivo</h3>
        <form className="row wrap" style={{ gap: 'var(--spacing-3)', alignItems: 'flex-end' }} onSubmit={onAdd}>
          <div style={{ flex: '1 1 200px' }}>
            <TextField
              label="Nombre"
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="Ej. Router Principal"
              required
            />
          </div>
          <div style={{ flex: '1 1 140px' }}>
            <TextField
              label="IP"
              value={form.ip_address}
              onChange={(e) => setForm((f) => ({ ...f, ip_address: e.target.value }))}
              placeholder="192.168.88.1"
              required
            />
          </div>
          <div style={{ flex: '0 1 80px' }}>
            <TextField
              label="Puerto"
              type="number"
              value={form.port}
              onChange={(e) => setForm((f) => ({ ...f, port: e.target.value }))}
              placeholder="22"
            />
          </div>
          {/* Campos de credenciales (no se muestran luego y no se guardan en cliente) */}
          <div style={{ flex: '1 1 140px' }}>
            <TextField
              label="Usuario"
              value={form.username}
              onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
              placeholder="admin"
              required
            />
          </div>
          <div style={{ flex: '1 1 140px' }}>
            <TextField
              label="Password"
              type="password"
              value={form.password}
              onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
              placeholder="••••••"
              required
            />
          </div>
          <div style={{ paddingBottom: 2 }}>
            <Button
              variant="primary"
              type="submit"
              disabled={isSuspended}
              title={isSuspended ? 'Acción bloqueada: cuenta suspendida' : undefined}
            >
              + Agregar
            </Button>
          </div>
        </form>
        {isSuspended && (
          <div className="muted small mt">
            ℹ️ Modo solo lectura: no puedes agregar equipos mientras la cuenta esté suspendida.
          </div>
        )}
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table">
          <div className="thead row" style={{ padding: 'var(--spacing-3) var(--spacing-4)', background: 'var(--bg-muted)' }}>
            <div>Nombre</div>
            <div>IP</div>
            <div>Puerto</div>
            <div>Salud</div>
          </div>
          <div style={{ padding: '0 var(--spacing-4)' }}>
            {devices.map((d) => (
              <div key={d.id} className="row" style={{ padding: 'var(--spacing-3) 0' }}>
                <div style={{ fontWeight: 500 }}>{d.name}</div>
                <div className="muted">{d.ip_address}</div>
                <div className="muted">{d.port}</div>
                <div><DeviceHealthIndicator healthStatus={d.health_status || 'verde'} /></div>
              </div>
            ))}
            {!devices.length && !loading && (
              <div className="muted" style={{ padding: 'var(--spacing-4) 0' }}>
                No hay dispositivos registrados.
              </div>
            )}
          </div>
        </div>
      </div>

      <UpsellModal open={showUpsell} onClose={() => setShowUpsell(false)} />
    </div>
  )
}