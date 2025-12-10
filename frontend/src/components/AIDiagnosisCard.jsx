import React, { useState } from 'react'
import PropTypes from 'prop-types'
import StatusBadge from './StatusBadge.jsx'

/**
 * AIDiagnosisCard
 * Visualizes forensic data analysis from the AI Provider.
 *
 * Props:
 * - data: Object (The full forensic data JSON)
 */
const AIDiagnosisCard = ({ data }) => {
  // Defensive Rendering
  if (!data || !data.analysis) {
    return null
  }

  const { analysis, telemetry } = data
  const { root_cause, severity, recommendations } = analysis

  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false)

  // Determine severity for badge (mapping from analysis severity to StatusBadge expected string if needed)
  // Assuming analysis.severity matches StatusBadge expectations or we pass it directly.
  // StatusBadge expects: 'Alerta Crítica', 'Alerta Severa', 'Alerta Menor', or defaults to info.
  // The memory says AI analysis severity levels are: 'warning', 'minor', 'major', 'critical'.
  // And they map to database states: 'Aviso', 'Alerta Menor', 'Alerta Severa', 'Alerta Crítica'.
  // We should map them here or assume the backend sends the mapped string.
  // Let's implement a mapper just in case the backend sends the English key.

  const mapSeverity = (sev) => {
    const s = sev?.toLowerCase()
    if (s === 'critical' || s === 'alerta crítica') return 'Alerta Crítica'
    if (s === 'major' || s === 'alerta severa') return 'Alerta Severa'
    if (s === 'minor' || s === 'alerta menor') return 'Alerta Menor'
    return 'Aviso'
  }

  const displaySeverity = mapSeverity(severity)

  return (
    <div className="card" style={{ borderLeft: `4px solid var(--color-accent-${getSeverityColorToken(displaySeverity)})`, marginBottom: '24px' }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
        <div>
           <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
               <h3 className="h3">Diagnóstico IA</h3>
               <StatusBadge estado={displaySeverity} />
           </div>
           <p className="body-sm text-muted">Análisis Forense Automático</p>
        </div>
      </div>

      {/* Body: Root Cause */}
      <div style={{ marginBottom: '24px' }}>
         <h4 className="body-md" style={{ fontWeight: 600, marginBottom: '8px' }}>Causa Raíz Detectada:</h4>
         <p className="body-md text-secondary" style={{ lineHeight: '1.6' }}>
             {root_cause || 'No se ha determinado una causa raíz específica.'}
         </p>
      </div>

      {/* Actions: Recommendations */}
      {recommendations && recommendations.length > 0 && (
          <div style={{ marginBottom: '24px' }}>
              <h4 className="body-md" style={{ fontWeight: 600, marginBottom: '8px' }}>Recomendaciones:</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {recommendations.map((rec, index) => (
                      <button
                        key={index}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '12px' }}
                      >
                        {rec}
                      </button>
                  ))}
              </div>
          </div>
      )}

      {/* Footer: Technical Evidence Accordion */}
      <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '12px' }}>
          <button
            onClick={() => setIsEvidenceOpen(!isEvidenceOpen)}
            style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-text-muted)',
                fontSize: '12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: 0
            }}
          >
              {isEvidenceOpen ? '▼ Ocultar Evidencia Técnica' : '▶ Ver Evidencia Técnica'}
          </button>

          {isEvidenceOpen && (
              <div style={{ marginTop: '12px', background: 'var(--color-bg-tertiary)', padding: '12px', borderRadius: 'var(--radius-sm)', overflowX: 'auto' }}>
                  {telemetry ? (
                      <pre style={{ margin: 0, fontSize: '11px', fontFamily: 'monospace', color: 'var(--color-text-primary)' }}>
                          {JSON.stringify(telemetry, null, 2)}
                      </pre>
                  ) : (
                      <p className="caption text-muted">No raw telemetry available.</p>
                  )}
              </div>
          )}
      </div>

    </div>
  )
}

function getSeverityColorToken(severity) {
    switch(severity) {
        case 'Alerta Crítica': return 'danger';
        case 'Alerta Severa': return 'warning'; // Using warning for severe as per design usually orange/yellow, but could be 'danger' too. Theme has 'warning' (orange) and 'danger' (red).
        case 'Alerta Menor': return 'secondary'; // Green? Or maybe 'warning' if yellow. Theme has 'secondary' (green).
        default: return 'primary'; // Blue
    }
}

AIDiagnosisCard.propTypes = {
  data: PropTypes.shape({
    analysis: PropTypes.shape({
      root_cause: PropTypes.string,
      severity: PropTypes.string,
      recommendations: PropTypes.arrayOf(PropTypes.string)
    }),
    telemetry: PropTypes.object
  })
}

export default AIDiagnosisCard
