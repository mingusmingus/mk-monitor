import React, { useState } from 'react'
import useFetchAlerts from '../hooks/useFetchAlerts.js'
import { updateAlertStatus } from '../api/alertApi.js'
import useAuth from '../hooks/useAuth.js'
import Button from '../components/ui/Button.jsx'
import Input from '../components/ui/Input.jsx'
import Card from '../components/ui/Card.jsx'

/**
 * Alerts Page (Rediseñada)
 *
 * Página dedicada a la gestión de alertas e incidentes.
 * Permite filtrar por severidad, dispositivo y estado operativo.
 */
export default function AlertsPage() {
  const { tenantStatus } = useAuth()
  const [filters, setFilters] = useState({ estado: '', device_id: '', status_operativo: '' })
  const { alerts, loading, error, refetch } = useFetchAlerts(filters)

  const isSuspended = tenantStatus === 'suspendido'

  const onAction = async (alertId, newStatus) => {
    if (isSuspended) return
    await updateAlertStatus(alertId, { status_operativo: newStatus })
    refetch()
  }

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
            <h1 className="h1">Centro de Alertas</h1>
            <p className="body-sm text-muted">Gestión de incidentes y notificaciones</p>
        </div>
        <Button onClick={refetch} variant="ghost" size="sm">Actualizar</Button>
      </header>

      {/* Filtros */}
      <Card elevated>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'end' }}>
            <div style={{ flex: 1, minWidth: '180px' }}>
                <label className="info-label" style={{ marginBottom: 6, display: 'block' }}>Severidad</label>
                <select
                    className="custom-input"
                    value={filters.estado}
                    onChange={(e) => setFilters(f => ({ ...f, estado: e.target.value }))}
                >
                    <option value="">Todas</option>
                    <option>Aviso</option>
                    <option>Alerta Menor</option>
                    <option>Alerta Severa</option>
                    <option>Alerta Crítica</option>
                </select>
            </div>

            <div style={{ flex: 1, minWidth: '180px' }}>
                 <Input
                    label="ID Dispositivo"
                    value={filters.device_id}
                    onChange={e => setFilters(f => ({ ...f, device_id: e.target.value }))}
                    placeholder="Ej. 1"
                    style={{ marginBottom: 0 }}
                 />
            </div>

            <div style={{ flex: 1, minWidth: '180px' }}>
                <label className="info-label" style={{ marginBottom: 6, display: 'block' }}>Estado Operativo</label>
                <select
                    className="custom-input"
                    value={filters.status_operativo}
                    onChange={(e) => setFilters(f => ({ ...f, status_operativo: e.target.value }))}
                >
                    <option value="">Todos</option>
                    <option>Pendiente</option>
                    <option>En curso</option>
                    <option>Resuelta</option>
                </select>
            </div>

            <Button onClick={refetch} variant="secondary">Filtrar</Button>
        </div>
      </Card>

      {/* Lista de Alertas */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {loading && <div className="text-muted" style={{ textAlign: 'center', padding: '20px' }}>Cargando alertas...</div>}
        {error && <div style={{ color: 'var(--color-accent-danger)', textAlign: 'center' }}>Error al cargar alertas</div>}

        {!loading && !error && alerts.length === 0 && (
          <Card style={{ textAlign: 'center', padding: '40px' }}>
            <div className="text-muted">No se encontraron alertas con los filtros seleccionados.</div>
          </Card>
        )}

        {alerts.map((a) => (
          <AlertRow
            key={a.id}
            alert={a}
            onAction={onAction}
            isSuspended={isSuspended}
          />
        ))}
      </div>
    </div>
  )
}

function AlertRow({ alert, onAction, isSuspended }) {
    const isCritical = alert.estado === 'Alerta Crítica'
    const isSevere = alert.estado === 'Alerta Severa'

    const borderColor = isCritical
        ? 'var(--color-accent-danger)'
        : isSevere
            ? 'var(--color-accent-warning)'
            : 'var(--color-accent-primary)'

    const bgAlpha = isCritical ? 'rgba(255, 59, 48, 0.05)' : 'var(--color-bg-secondary)'

    return (
        <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            background: bgAlpha,
            border: '1px solid var(--color-border)',
            borderLeft: `4px solid ${borderColor}`,
            borderRadius: 'var(--radius-sm)',
            padding: '16px',
            transition: 'transform 0.2s',
            boxShadow: 'var(--shadow-sm)'
        }}>
            <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
                    <span style={{
                        fontSize: '11px', fontWeight: 700, textTransform: 'uppercase',
                        color: borderColor, border: `1px solid ${borderColor}`,
                        padding: '2px 6px', borderRadius: '4px'
                    }}>
                        {alert.estado}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                        {new Date(alert.fecha_detectado).toLocaleString()}
                    </span>
                </div>
                <div style={{ fontSize: '15px', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                    {alert.mensaje}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                    Dispositivo #{alert.device_id} • {alert.status_operativo || 'Pendiente'}
                </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                {!isSuspended && (
                   <>
                     {alert.status_operativo !== 'en_revision' && alert.status_operativo !== 'resuelto' && (
                        <Button size="sm" variant="secondary" onClick={() => onAction(alert.id, 'en_revision')}>Revisar</Button>
                     )}
                     {alert.status_operativo !== 'resuelto' && (
                        <Button size="sm" variant="primary" onClick={() => onAction(alert.id, 'resuelto')}>Resolver</Button>
                     )}
                     {alert.status_operativo === 'resuelto' && (
                        <span style={{ color: 'var(--color-accent-secondary)', fontWeight: 600, fontSize: '13px' }}>Resuelto</span>
                     )}
                   </>
                )}
            </div>
        </div>
    )
}
