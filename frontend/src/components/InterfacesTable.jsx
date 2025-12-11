import React, { useState } from 'react'
import PropTypes from 'prop-types'
import { Activity, AlertCircle, CheckCircle, Info } from 'lucide-react'
import '../styles/components/glass.css'

/**
 * InterfacesTable
 *
 * Componente que muestra una tabla con las interfaces de red del dispositivo.
 * Incluye una columna de "Estado Físico" que alerta visualmente sobre errores.
 */
const InterfacesTable = ({ interfaces }) => {
  if (!interfaces || interfaces.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
        [INFO] No se detectaron interfaces.
      </div>
    )
  }

  // Estado para el popover de detalles de error
  const [selectedError, setSelectedError] = useState(null)

  return (
    <div style={{ overflowX: 'auto' }} className="fade-in">
      {/* Simple Popover/Dialog for Errors */}
      {selectedError && (
          <div style={{
              position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
              backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100,
              display: 'flex', alignItems: 'center', justifyContent: 'center'
          }} onClick={() => setSelectedError(null)}>
              <div style={{
                  backgroundColor: 'var(--color-bg-primary)', padding: '24px', borderRadius: '12px',
                  maxWidth: '400px', width: '90%', boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
              }} onClick={e => e.stopPropagation()}>
                  <h3 className="h3" style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Activity color="var(--color-accent-warning)" />
                      Detalle de Integridad Física
                  </h3>
                  <div style={{ whiteSpace: 'pre-line', fontSize: '14px', lineHeight: '1.5', color: 'var(--color-text-secondary)' }}>
                      {selectedError}
                  </div>
                  <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                          onClick={() => setSelectedError(null)}
                          style={{
                              background: 'var(--color-accent-primary)', color: 'white', border: 'none',
                              padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 600
                          }}
                      >
                          Cerrar
                      </button>
                  </div>
              </div>
          </div>
      )}

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Nombre</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Tipo</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>MAC</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>TX / RX</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600, textAlign: 'center' }}>Integridad Física</th>
          </tr>
        </thead>
        <tbody>
          {interfaces.map((iface, index) => {
             const stats = iface.stats || iface

             // Detección de errores físicos
             const fcsErrors = Number(stats.rx_fcs_error ?? stats.fcs_error ?? 0)
             const collisions = Number(stats.collisions ?? 0)
             const blits = Number(stats.blits ?? 0) // Assuming blits is a stat if available

             const hasPhysicalError = fcsErrors > 0 || collisions > 0 || blits > 0

             const errorMessages = []
             if (fcsErrors > 0) errorMessages.push(`${fcsErrors} Errores de FCS (CRC). Posible cable dañado o interferencia.`)
             if (collisions > 0) errorMessages.push(`${collisions} Colisiones detectadas. Posible problema de Duplex o congestión.`)
             if (blits > 0) errorMessages.push(`${blits} Blits detectados.`)

             const errorDetail = errorMessages.join('\n')

             return (
              <tr key={iface.id || index} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 8px', fontWeight: 500 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {iface.running === 'true' || iface.running === true ? (
                             <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-accent-secondary)', boxShadow: '0 0 4px var(--color-accent-secondary)' }}></div>
                        ) : (
                             <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-text-muted)' }}></div>
                        )}
                        {iface.name}
                    </div>
                </td>
                <td style={{ padding: '12px 8px', color: 'var(--color-text-secondary)' }}>{iface.type}</td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace', color: 'var(--color-text-muted)' }}>{iface.mac_address || iface.mac}</td>
                <td style={{ padding: '12px 8px', color: 'var(--color-text-secondary)' }}>
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <span style={{ fontSize: '12px' }}>↑ {formatBytes(iface.tx_byte)}</span>
                        <span style={{ fontSize: '12px' }}>↓ {formatBytes(iface.rx_byte)}</span>
                    </div>
                </td>
                <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                    {hasPhysicalError ? (
                        <button
                            onClick={() => setSelectedError(errorDetail)}
                            style={{
                                background: 'none', border: 'none', cursor: 'pointer',
                                display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto',
                                animation: 'pulse 2s infinite'
                            }}
                            title="Problemas Físicos Detectados"
                        >
                            <Activity size={18} color="var(--color-accent-warning)" />
                        </button>
                    ) : (
                        <div title="Enlace Saludable" style={{ display: 'flex', justifyContent: 'center' }}>
                             <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--color-accent-secondary)', opacity: 0.5 }}></div>
                        </div>
                    )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      <style>{`
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
            100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  )
}

function formatBytes(bytes, decimals = 1) {
    if (!+bytes) return '0 B'
    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

InterfacesTable.propTypes = {
  interfaces: PropTypes.arrayOf(PropTypes.object)
}

export default InterfacesTable
