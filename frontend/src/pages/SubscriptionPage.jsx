import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getSubscriptionStatus } from '../api/subscriptionApi.js'
import UpsellModal from '../components/UpsellModal.jsx'
import Button from '../components/ui/Button.jsx'

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
    <div className="col gap-6">
      <h1 className="h1">Suscripción</h1>
      {!data && !error && <div className="muted">Cargando...</div>}
      {error && <div className="text-danger">{error}</div>}
      {data && (
        <div className="card">
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="col gap-1">
              <span className="small muted uppercase">Plan actual</span>
              <span className="h2">{data.plan}</span>
            </div>
            <div className="col gap-1">
              <span className="small muted uppercase">Estado de pago</span>
              <span className="bold">{data.status_pago}</span>
            </div>
            <div className="col gap-1">
              <span className="small muted uppercase">Uso de dispositivos</span>
              <span className="h3">{data.used} <span className="text-muted text-base font-normal">/ {data.max_devices}</span></span>
            </div>
          </div>

          <div className="row justify-end">
            <Button variant="primary" onClick={() => setShowUpsell(true)}>
              Actualizar plan
            </Button>
          </div>
        </div>
      )}
      <UpsellModal open={showUpsell} onClose={() => setShowUpsell(false)} />
    </div>
  )
}
