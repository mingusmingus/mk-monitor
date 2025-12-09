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
    <div className="col gap-6">
      <header>
        <h1 className="h1">Dispositivos</h1>
        <p className="muted">Gestiona tus equipos MikroTik y monitorea su estado.</p>
      </header>

      <div className="card">
        <h3 className="h3 mb-4">Nuevo Dispositivo</h3>
        <form className="row wrap gap-3" style={{ alignItems: 'flex-end' }} onSubmit={onAdd}>
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
          <div className="muted small mt-2">
            ℹ️ Modo solo lectura: no puedes agregar equipos mientras la cuenta esté suspendida.
          </div>
        )}
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr style={{ background: 'var(--bg-muted)' }}>
                <th>Nombre</th>
                <th>IP</th>
                <th>Puerto</th>
                <th>Salud</th>
              </tr>
            </thead>
            <tbody>
              {devices.map((d) => (
                <tr key={d.id}>
                  <td className="bold">{d.name}</td>
                  <td className="muted">{d.ip_address}</td>
                  <td className="muted">{d.port}</td>
                  <td><DeviceHealthIndicator healthStatus={d.health_status || 'verde'} /></td>
                </tr>
              ))}
              {!devices.length && !loading && (
                <tr>
                  <td colSpan="4" className="text-center muted" style={{ padding: 'var(--spacing-4)' }}>
                    No hay dispositivos registrados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <UpsellModal open={showUpsell} onClose={() => setShowUpsell(false)} />
    </div>
  )
}
