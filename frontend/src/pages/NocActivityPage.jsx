import React from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import Card from '../components/ui/Card.jsx'

/**
 * NOC Activity Page Redesign
 * - Focus on "En curso" alerts
 * - High contrast or clear visibility for NOC screens
 */
export default function NocActivityPage() {
  const { alerts, loading } = useFetchAlerts({ status_operativo: 'En curso' })

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <header>
        <h1 className="h1">Actividad NOC</h1>
        <p className="body-sm text-muted">Monitoreo en tiempo real de incidentes activos</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px' }}>
        {loading && <div style={{ padding: 20, textAlign: 'center' }}>Cargando datos NOC...</div>}

        {!loading && alerts.length === 0 && (
          <Card style={{ padding: '48px', textAlign: 'center', gridColumn: '1 / -1' }}>
            <div style={{ fontSize: '18px', fontWeight: 600, color: 'var(--color-accent-secondary)' }}>
                Todo normal. Sin incidentes en curso.
            </div>
          </Card>
        )}

        {alerts.map((a) => (
          <Card key={a.id} elevated statusColor="warning">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span style={{
                  background: 'var(--color-accent-warning)', color: 'white',
                  padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700
              }}>
                EN CURSO
              </span>
              <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
                #{a.id}
              </span>
            </div>

            <h3 className="h3" style={{ marginBottom: '8px', color: 'var(--color-text-primary)' }}>
                {a.mensaje || 'Incidente sin descripción'}
            </h3>

            <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: 'var(--color-text-muted)', marginTop: '16px', borderTop: '1px solid var(--color-border)', paddingTop: '12px' }}>
                <div>
                    <span style={{ display: 'block', fontSize: '10px', textTransform: 'uppercase' }}>Dispositivo</span>
                    <span style={{ fontWeight: 500 }}>ID {a.device_id}</span>
                </div>
                <div>
                    <span style={{ display: 'block', fontSize: '10px', textTransform: 'uppercase' }}>Iniciado</span>
                    <span style={{ fontWeight: 500 }}>{new Date(a.fecha_detectado).toLocaleTimeString()}</span>
                </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
