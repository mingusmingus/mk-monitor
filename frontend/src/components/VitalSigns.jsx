import React from 'react'
import PropTypes from 'prop-types'
import { Zap, Thermometer, Cpu } from 'lucide-react'
import '../styles/components/glass.css'

/**
 * VitalSigns
 *
 * Muestra los signos vitales del hardware (Voltaje, Temperatura, CPU)
 * inspirados en las complicaciones del Apple Watch.
 */
const VitalSigns = ({ health, cpuLoad }) => {
  // Defensive checks
  if (!health && cpuLoad === undefined) return null

  const voltage = health?.voltage
  const temperature = health?.temperature

  // Helpers para colores
  const getVoltageColor = (v) => {
      if (v === undefined || v === null) return 'var(--color-text-muted)'
      if (v < 24) return 'var(--color-accent-warning)' // Naranja si bajo voltaje (asumiendo std 24V)
      return 'var(--color-accent-secondary)' // Verde OK
  }

  const getTempColor = (t) => {
      if (t === undefined || t === null) return 'var(--color-text-muted)'
      if (t < 40) return '#007AFF' // Azul fresco
      if (t < 60) return 'var(--color-accent-secondary)' // Verde normal
      return 'var(--color-accent-danger)' // Rojo caliente
  }

  const getCpuColor = (load) => {
      if (load === undefined || load === null) return 'var(--color-text-muted)'
      if (load < 50) return 'var(--color-accent-secondary)'
      if (load < 80) return 'var(--color-accent-warning)'
      return 'var(--color-accent-danger)'
  }

  return (
    <div className="grid-cols-3 fade-in" style={{ marginTop: '16px' }}>
        {/* Salud Eléctrica (Voltaje) */}
        <div className="glass-panel" style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={20} color={getVoltageColor(voltage)} style={{ marginBottom: '4px' }} />
            <span className="body-sm text-muted" style={{ fontSize: '11px' }}>Voltaje</span>
            <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--color-text-primary)' }}>
                {voltage ? `${voltage}V` : 'N/A'}
            </span>
        </div>

        {/* Temperatura */}
        <div className="glass-panel" style={{ padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <Thermometer size={20} color={getTempColor(temperature)} style={{ marginBottom: '4px' }} />
            <span className="body-sm text-muted" style={{ fontSize: '11px' }}>Temp</span>
            <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--color-text-primary)' }}>
                {temperature ? `${temperature}°C` : 'N/A'}
            </span>
        </div>

        {/* Carga Cognitiva (CPU) - Circular Progress Ring */}
        <div className="glass-panel" style={{ padding: '8px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
            <div style={{ position: 'relative', width: '44px', height: '44px', marginBottom: '4px' }}>
                <svg width="44" height="44" viewBox="0 0 36 36">
                    <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke="var(--color-border)"
                        strokeWidth="3"
                    />
                    <path
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                        fill="none"
                        stroke={getCpuColor(cpuLoad)}
                        strokeWidth="3"
                        strokeDasharray={`${cpuLoad || 0}, 100`}
                        strokeLinecap="round"
                        transform="rotate(0 18 18)"
                    />
                </svg>
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                     <Cpu size={14} color="var(--color-text-secondary)" />
                </div>
            </div>
            <span className="body-sm text-muted" style={{ fontSize: '11px', lineHeight: 1 }}>CPU</span>
            <span style={{ fontWeight: 600, fontSize: '12px', color: 'var(--color-text-primary)' }}>
                {cpuLoad !== undefined && cpuLoad !== null ? `${cpuLoad}%` : 'N/A'}
            </span>
        </div>
    </div>
  )
}

VitalSigns.propTypes = {
    health: PropTypes.shape({
        voltage: PropTypes.number,
        temperature: PropTypes.number
    }),
    cpuLoad: PropTypes.number
}

export default VitalSigns
