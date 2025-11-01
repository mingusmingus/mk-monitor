import React, { useEffect, useState } from 'react'
import { getDevices, createDevice } from '../api/deviceApi.js'
import DeviceHealthIndicator from '../components/DeviceHealthIndicator.jsx'
import UpsellModal from '../components/UpsellModal.jsx'
import useAuth from '../hooks/useAuth.js'

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
    <div className="col gap">
      <h1>Dispositivos</h1>
      <div className="card">
        <form className="row gap" onSubmit={onAdd}>
          <input
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="Nombre"
            required
          />
          <input
            value={form.ip_address}
            onChange={(e) => setForm((f) => ({ ...f, ip_address: e.target.value }))}
            placeholder="IP"
            required
          />
          <input
            type="number"
            value={form.port}
            onChange={(e) => setForm((f) => ({ ...f, port: e.target.value }))}
            placeholder="Puerto"
          />
          {/* Campos de credenciales (no se muestran luego y no se guardan en cliente) */}
          <input
            value={form.username}
            onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
            placeholder="Usuario MikroTik"
            required
          />
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            placeholder="Password MikroTik"
            required
          />
          <button
            className="btn btn-primary"
            type="submit"
            disabled={isSuspended}
            title={isSuspended ? 'Acción bloqueada: cuenta suspendida' : undefined}
          >
            + Agregar equipo
          </button>
        </form>
        {isSuspended && (
          <div className="muted small mt">
            ℹ️ Modo solo lectura: no puedes agregar equipos mientras la cuenta esté suspendida.
          </div>
        )}
      </div>

      <div className="card">
        <h3>Lista</h3>
        {loading && <div className="muted">Cargando...</div>}
        {error && <div className="error">{error}</div>}
        <div className="table">
          <div className="thead row">
            <div>Nombre</div>
            <div>IP</div>
            <div>Puerto</div>
            <div>Salud</div>
          </div>
          {devices.map((d) => (
            <div key={d.id} className="row">
              <div>{d.name}</div>
              <div>{d.ip_address}</div>
              <div>{d.port}</div>
              <div><DeviceHealthIndicator healthStatus={d.health_status || 'verde'} /></div>
            </div>
          ))}
          {!devices.length && !loading && <div className="muted">Sin dispositivos.</div>}
        </div>
      </div>

      <UpsellModal open={showUpsell} onClose={() => setShowUpsell(false)} />
    </div>
  )
}