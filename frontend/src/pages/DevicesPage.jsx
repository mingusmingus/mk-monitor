import React, { useEffect, useState } from 'react'
import { getDevices, createDevice } from '../api/deviceApi.js'
import DeviceHealthIndicator from '../components/DeviceHealthIndicator.jsx'
import UpsellModal from '../components/UpsellModal.jsx'

// Listado y alta de equipos. Si supera límite -> Upsell.
export default function DevicesPage() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [form, setForm] = useState({ name: '', ip_address: '', port: 22 })
  const [showUpsell, setShowUpsell] = useState(false)

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
    try {
      // NOTA: backend requiere credenciales cifradas, aquí solo placeholder.
      await createDevice({
        name: form.name,
        ip_address: form.ip_address,
        port: Number(form.port) || 22,
        username_encrypted: 'TODO',
        password_encrypted: 'TODO'
      })
      setForm({ name: '', ip_address: '', port: 22 })
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
          <button className="btn btn-primary" type="submit">+ Agregar equipo</button>
        </form>
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