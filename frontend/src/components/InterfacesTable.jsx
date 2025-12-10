import React from 'react'
import PropTypes from 'prop-types'

/**
 * InterfacesTable
 * Displays a table of network interfaces with status and stats.
 * Includes a "Physical State" column with visual warnings for errors.
 *
 * Props:
 * - interfaces: Array of interface objects
 */
const InterfacesTable = ({ interfaces }) => {
  if (!interfaces || interfaces.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
        No interfaces detected.
      </div>
    )
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Nombre</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Tipo</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>MAC</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>MTU</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>TX / RX (Bytes)</th>
            <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600, textAlign: 'center' }}>Estado Físico</th>
          </tr>
        </thead>
        <tbody>
          {interfaces.map((iface, index) => {
             // Logic for Physical State Error
             // Assuming stats are in iface.stats or directly on iface if flattened.
             // The prompt says: const hasPhysicalError = stats.fcs_error > 0 || stats.collisions > 0;
             // I'll assume `stats` property exists or check root properties if flattened.
             // Common mikrotik structure might put stats in a sub-object or flat.
             // I'll check both with nullish coalescing.
             const stats = iface.stats || iface

             const fcsErrors = Number(stats.fcs_error ?? 0)
             const collisions = Number(stats.collisions ?? 0)
             const hasPhysicalError = fcsErrors > 0 || collisions > 0

             const errorDetail = []
             if (fcsErrors > 0) errorDetail.push(`FCS Errors: ${fcsErrors}`)
             if (collisions > 0) errorDetail.push(`Collisions: ${collisions}`)
             const errorTooltip = errorDetail.join(', ')

             return (
              <tr key={iface.id || index} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 8px', fontWeight: 500 }}>
                    {iface.name}
                    {iface.running === 'true' || iface.running === true ? (
                        <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-accent-secondary)', marginLeft: '6px', verticalAlign: 'middle' }} title="Running"></span>
                    ) : (
                         <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-text-muted)', marginLeft: '6px', verticalAlign: 'middle' }} title="Not Running"></span>
                    )}
                </td>
                <td style={{ padding: '12px 8px', color: 'var(--color-text-secondary)' }}>{iface.type}</td>
                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>{iface.mac_address}</td>
                <td style={{ padding: '12px 8px' }}>{iface.mtu}</td>
                <td style={{ padding: '12px 8px', color: 'var(--color-text-secondary)' }}>
                    <div>TX: {formatBytes(iface.tx_byte)}</div>
                    <div>RX: {formatBytes(iface.rx_byte)}</div>
                </td>
                <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                    {hasPhysicalError ? (
                        <span title={errorTooltip} style={{ cursor: 'help', color: 'var(--color-accent-warning)' }}>
                            ⚠️
                        </span>
                    ) : (
                        <span title="OK" style={{ color: 'var(--color-accent-secondary)' }}>
                            ✓
                        </span>
                    )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function formatBytes(bytes, decimals = 2) {
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
