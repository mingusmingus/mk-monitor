import React, { useEffect, useState } from 'react'
import { getSubscriptionStatus } from '../api/subscriptionApi.js'

// Estado del plan y opciones de upgrade.
export default function SubscriptionPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getSubscriptionStatus()
      .then((res) => setData(res.data))
      .catch((e) => setError('Error al cargar suscripción'))
  }, [])

  return (
    <div className="col gap">
      <h1>Suscripción</h1>
      {!data && !error && <div className="muted">Cargando...</div>}
      {error && <div className="error">{error}</div>}
      {data && (
        <div className="card">
          <div className="row gap">
            <div><strong>Plan:</strong> {data.plan}</div>
            <div><strong>Dispositivos:</strong> {data.used} / {data.max_devices}</div>
            <div><strong>Pago:</strong> {data.status_pago}</div>
          </div>
          <div className="mt">
            <button className="btn btn-primary">Actualizar plan</button>
          </div>
        </div>
      )}
    </div>
  )
}
