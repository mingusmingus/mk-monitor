import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getSubscriptionStatus } from '../api/subscriptionApi.js'
import UpsellModal from '../components/UpsellModal.jsx'

// Estado del plan y opciones de upgrade.
export default function SubscriptionPage() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const location = useLocation()
  const [showUpsell, setShowUpsell] = useState(
    () => new URLSearchParams(location.search).get('upsell') === '1'
  )

  useEffect(() => {
    getSubscriptionStatus()
      .then((res) => setData(res.data))
      .catch((e) => setError('Error al cargar suscripción'))
  }, [])

  // Escucha evento para abrir UpsellModal cuando interceptor lo dispare estando ya en /subscription
  useEffect(() => {
    function openUpsell() {
      setShowUpsell(true)
    }
    window.addEventListener('subscription:upsell', openUpsell)
    return () => window.removeEventListener('subscription:upsell', openUpsell)
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
            <button className="btn btn-primary" onClick={() => setShowUpsell(true)}>Actualizar plan</button>
          </div>
        </div>
      )}
      <UpsellModal open={showUpsell} onClose={() => setShowUpsell(false)} />
    </div>
  )
}
