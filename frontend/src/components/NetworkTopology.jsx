import React from 'react'
import PropTypes from 'prop-types'
import { Network, Server, Wifi, Box } from 'lucide-react'
import '../styles/components/glass.css'

/**
 * NetworkTopology
 *
 * Renderiza la lista de vecinos (CDP/LLDP/MNDP) con badges de fabricante.
 */
const NetworkTopology = ({ neighbors }) => {
  if (!neighbors || neighbors.length === 0) {
      return (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-text-muted)', fontStyle: 'italic' }} className="fade-in">
              [INFO] No se detectaron vecinos en la red.
          </div>
      )
  }

  // Helper para identificar fabricante
  const getVendorBadge = (item) => {
      const text = `${item.platform || ''} ${item.identity || ''} ${item.board || ''}`.toLowerCase()

      if (text.includes('cisco')) return { label: 'CISCO', color: '#00bceb', icon: <Server size={12} /> }
      if (text.includes('ubiquiti') || text.includes('u7') || text.includes('unifi')) return { label: 'UBIQUITI', color: '#0559C9', icon: <Wifi size={12} /> }
      if (text.includes('mikrotik') || text.includes('routeros')) return { label: 'MIKROTIK', color: '#E53935', icon: <Box size={12} /> }

      return null
  }

  return (
    <div className="fade-in">
        <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border)', textAlign: 'left' }}>
                        <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Interfaz</th>
                        <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>IP Address</th>
                        <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Identidad & Plataforma</th>
                        <th style={{ padding: '12px 8px', color: 'var(--color-text-secondary)', fontWeight: 600 }}>MAC</th>
                    </tr>
                </thead>
                <tbody>
                    {neighbors.map((n, i) => {
                        const vendor = getVendorBadge(n)
                        return (
                            <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                                <td style={{ padding: '12px 8px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <Network size={14} color="var(--color-text-muted)" />
                                    {n.interface}
                                </td>
                                <td style={{ padding: '12px 8px', fontFamily: 'monospace' }}>
                                    {n.address || n.ip || '-'}
                                </td>
                                <td style={{ padding: '12px 8px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span style={{ fontWeight: 500, color: 'var(--color-text-primary)' }}>{n.identity || 'Desconocido'}</span>
                                        {vendor && (
                                            <span style={{
                                                display: 'flex', alignItems: 'center', gap: '4px',
                                                fontSize: '10px', fontWeight: 700,
                                                color: 'white', backgroundColor: vendor.color,
                                                padding: '2px 6px', borderRadius: '4px',
                                                letterSpacing: '0.5px'
                                            }}>
                                                {vendor.icon}
                                                {vendor.label}
                                            </span>
                                        )}
                                    </div>
                                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                                        {n.platform} {n.version} {n.board}
                                    </div>
                                </td>
                                <td style={{ padding: '12px 8px', fontFamily: 'monospace', color: 'var(--color-text-muted)' }}>
                                    {n['mac-address'] || n.mac_address || '-'}
                                </td>
                            </tr>
                        )
                    })}
                </tbody>
            </table>
        </div>
    </div>
  )
}

NetworkTopology.propTypes = {
    neighbors: PropTypes.arrayOf(PropTypes.object)
}

export default NetworkTopology
