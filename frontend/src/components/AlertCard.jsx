import React from 'react'
import Button from './ui/Button.jsx'

/**
 * AlertCard (Refactorizado)
 *
 * Componente para mostrar una tarjeta de alerta individual en el listado.
 * Adaptado al sistema de diseño con bordes de color según severidad.
 *
 * Props:
 * - alert: Object (Objeto de alerta).
 * - onAction: Function (Callback para acciones de botones).
 */
export default function AlertCard({ alert, onAction }) {
  const isCritical = alert?.estado === 'Alerta Crítica'
  const isSevere = alert?.estado === 'Alerta Severa'

  const borderColor = isCritical
      ? 'var(--color-accent-danger)'
      : isSevere
          ? 'var(--color-accent-warning)'
          : 'var(--color-accent-primary)'

  return (
    <div style={{
        display: 'flex', flexDirection: 'column', gap: '8px',
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)',
        borderLeft: `4px solid ${borderColor}`,
        borderRadius: 'var(--radius-sm)',
        padding: '16px',
        boxShadow: 'var(--shadow-sm)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{
                    fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
                    color: borderColor
                }}>
                    {alert?.estado || 'ALERTA'}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                    {alert?.created_at ? new Date(alert.created_at).toLocaleString() : ''}
                </span>
            </div>
            <div style={{ fontWeight: 600, fontSize: '15px' }}>{alert?.titulo || alert?.mensaje || 'Sin título'}</div>
        </div>
        <div style={{ fontSize: '12px', background: 'var(--color-bg-tertiary)', padding: '2px 8px', borderRadius: '4px', fontWeight: 500 }}>
            {alert?.status_operativo || 'Pendiente'}
        </div>
      </div>

      <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
        {alert?.descripcion}
      </div>

      {alert?.accion_recomendada && (
        <div style={{ fontSize: '12px', background: 'rgba(0,122,255,0.05)', color: 'var(--color-accent-primary)', padding: '8px', borderRadius: '4px' }}>
            <strong>Recomendación:</strong> {alert.accion_recomendada}
        </div>
      )}

      <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
        <Button size="sm" variant="secondary" onClick={() => onAction?.(alert.id, 'en_revision')}>En Revisión</Button>
        <Button size="sm" variant="primary" onClick={() => onAction?.(alert.id, 'resuelto')}>Resolver</Button>
      </div>
    </div>
  )
}
