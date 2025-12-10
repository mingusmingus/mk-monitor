import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getSubscriptionStatus } from '../api/subscriptionApi.js'
import UpsellModal from '../components/UpsellModal.jsx'
import Button from '../components/ui/Button.jsx'
import Card from '../components/ui/Card.jsx'

/**
 * Subscription Page Redesign
 */
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

  useEffect(() => {
    function openUpsell() {
      setShowUpsell(true)
    }
    window.addEventListener('subscription:upsell', openUpsell)
    return () => window.removeEventListener('subscription:upsell', openUpsell)
  }, [])

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <header>
          <h1 className="h1">Tu Suscripción</h1>
          <p className="body-sm text-muted">Gestiona tu plan y límites de facturación</p>
      </header>

      {!data && !error && <div className="text-muted">Cargando detalles...</div>}
      {error && <div className="text-danger">{error}</div>}

      {data && (
        <Card elevated>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
                <div>
                    <span style={{ fontSize: '13px', textTransform: 'uppercase', color: 'var(--color-text-muted)', fontWeight: 600 }}>Plan Actual</span>
                    <div style={{ fontSize: '32px', fontWeight: 700, color: 'var(--color-text-primary)' }}>{data.plan}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '13px', textTransform: 'uppercase', color: 'var(--color-text-muted)', fontWeight: 600 }}>Estado</span>
                    <div style={{
                        fontSize: '14px', fontWeight: 600,
                        color: data.status_pago === 'Al día' ? 'var(--color-accent-secondary)' : 'var(--color-accent-danger)',
                        background: data.status_pago === 'Al día' ? 'rgba(52, 199, 89, 0.1)' : 'rgba(255, 59, 48, 0.1)',
                        padding: '4px 12px', borderRadius: '16px', display: 'inline-block', marginTop: '4px'
                    }}>
                        {data.status_pago}
                    </div>
                </div>
            </div>

            <div style={{ background: 'var(--color-bg-tertiary)', padding: '24px', borderRadius: '8px', marginBottom: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ fontWeight: 600 }}>Uso de Dispositivos</span>
                    <span style={{ fontWeight: 600 }}>{data.used} / {data.max_devices}</span>
                </div>
                {/* Progress Bar */}
                <div style={{ height: '8px', background: 'var(--color-border)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                        height: '100%',
                        width: `${Math.min((data.used / data.max_devices) * 100, 100)}%`,
                        background: 'var(--color-accent-primary)',
                        transition: 'width 0.5s ease'
                    }}></div>
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '8px' }}>
                    Has utilizado el {Math.round((data.used / data.max_devices) * 100)}% de tu cupo disponible.
                </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <Button variant="secondary" onClick={() => {}}>Gestionar Métodos de Pago</Button>
                <Button variant="primary" onClick={() => setShowUpsell(true)}>Mejorar Plan</Button>
            </div>
        </Card>
      )}

      <UpsellModal open={showUpsell} onClose={() => setShowUpsell(false)} />
    </div>
  )
}
