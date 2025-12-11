import React, { useState } from 'react'
import PropTypes from 'prop-types'
import StatusBadge from './StatusBadge.jsx'
import { CheckCircle2, ShieldAlert, ChevronRight, ChevronDown, AlertTriangle } from 'lucide-react'
import '../styles/components/glass.css'

/**
 * AIDiagnosisCard
 *
 * Componente que visualiza el diagnóstico forense generado por el sistema de IA.
 * Implementa efecto Glassmorphism, Skeleton Loader y Alertas de Seguridad.
 */
const AIDiagnosisCard = ({ data, loading }) => {
  // Estado Loading: Skeleton Loader con efecto shimmer
  if (loading) {
      return (
          <div className="glass-panel" style={{ padding: '20px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                  <div className="skeleton-shimmer" style={{ width: '24px', height: '24px', borderRadius: '50%' }}></div>
                  <div className="skeleton-shimmer" style={{ width: '150px', height: '24px' }}></div>
              </div>
              <div className="skeleton-shimmer" style={{ width: '100%', height: '16px', marginBottom: '8px' }}></div>
              <div className="skeleton-shimmer" style={{ width: '80%', height: '16px', marginBottom: '24px' }}></div>
              <div className="skeleton-shimmer" style={{ width: '100%', height: '60px' }}></div>
          </div>
      )
  }

  // Renderizado defensivo
  if (!data || !data.analysis) {
    return null
  }

  const { analysis, telemetry, security_audit } = data
  const { root_cause, severity, recommendations, summary } = analysis

  const [isEvidenceOpen, setIsEvidenceOpen] = useState(false)

  // Mapeo de severidad
  const mapSeverity = (sev) => {
    const s = sev?.toLowerCase()
    if (s?.includes('critical') || s?.includes('crítica')) return 'Alerta Crítica'
    if (s?.includes('major') || s?.includes('severa')) return 'Alerta Severa'
    if (s?.includes('minor') || s?.includes('menor')) return 'Alerta Menor'
    return 'Aviso'
  }

  const displaySeverity = mapSeverity(severity)
  const isHealthy = displaySeverity === 'Aviso' || displaySeverity === 'Healthy'

  // Detectar puertos inseguros
  const insecurePorts = security_audit?.insecure_ports || []
  const hasSecurityRisk = insecurePorts.length > 0 || (security_audit?.risk_score > 5)

  return (
    <div className="glass-panel fade-in" style={{ padding: '24px', marginBottom: '24px', position: 'relative', overflow: 'hidden' }}>

      {/* Decorative colored border left */}
      <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0, width: '4px',
          backgroundColor: `var(--color-accent-${getSeverityColorToken(displaySeverity)})`
      }}></div>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px', paddingLeft: '12px' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
           {isHealthy ? (
               <CheckCircle2 size={24} color="var(--color-accent-secondary)" />
           ) : (
               <ShieldAlert size={24} color={`var(--color-accent-${getSeverityColorToken(displaySeverity)})`} />
           )}
           <div>
               <h3 className="h3" style={{ marginBottom: '4px' }}>Diagnóstico IA</h3>
               <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                   <StatusBadge estado={displaySeverity} />
                   <span className="body-sm text-muted">Ingeniero Certificado Virtual</span>
               </div>
           </div>
        </div>
      </div>

      <div style={{ paddingLeft: '12px' }}>

        {/* Security Alert Banner */}
        {hasSecurityRisk && (
            <div style={{
                backgroundColor: 'rgba(255, 59, 48, 0.1)',
                border: '1px solid var(--color-accent-danger)',
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
            }}>
                <AlertTriangle size={20} color="var(--color-accent-danger)" />
                <div>
                    <strong style={{ color: 'var(--color-accent-danger)', fontSize: '13px' }}>Riesgo de Seguridad Detectado</strong>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-primary)' }}>
                        {insecurePorts.length > 0
                            ? `Puertos inseguros abiertos: ${insecurePorts.join(', ')}. `
                            : 'Configuración vulnerable detectada. '}
                        Recomendamos cerrar accesos no utilizados.
                    </div>
                </div>
            </div>
        )}

        {/* Body: Summary & Root Cause */}
        <div style={{ marginBottom: '20px' }}>
            <h4 className="body-md" style={{ fontWeight: 600, marginBottom: '8px' }}>
                {root_cause || 'Análisis completado'}
            </h4>
            <p className="body-md text-secondary" style={{ lineHeight: '1.6' }}>
                {summary || root_cause || 'El sistema no detecta anomalías críticas en este momento.'}
            </p>
        </div>

        {/* Recommendations */}
        {recommendations && recommendations.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
                <h5 className="body-sm" style={{ fontWeight: 600, color: 'var(--color-text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Recomendaciones
                </h5>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {recommendations.map((rec, index) => (
                        <span
                            key={index}
                            style={{
                                fontSize: '12px',
                                padding: '4px 10px',
                                borderRadius: '12px',
                                backgroundColor: 'var(--color-bg-secondary)',
                                color: 'var(--color-text-primary)',
                                border: '1px solid var(--color-border)'
                            }}
                        >
                            {rec}
                        </span>
                    ))}
                </div>
            </div>
        )}

        {/* Technical Evidence Accordion */}
        <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '12px' }}>
            <button
                onClick={() => setIsEvidenceOpen(!isEvidenceOpen)}
                style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--color-text-muted)',
                    fontSize: '13px',
                    fontWeight: 500,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    padding: 0,
                    transition: 'color 0.2s'
                }}
            >
                {isEvidenceOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                {isEvidenceOpen ? 'Ocultar Evidencia Técnica' : 'Ver Evidencia Técnica'}
            </button>

            {isEvidenceOpen && (
                <div className="fade-in" style={{ marginTop: '12px', background: 'var(--color-bg-tertiary)', padding: '16px', borderRadius: '8px', overflowX: 'auto' }}>
                    {telemetry ? (
                        <>
                            <div style={{ marginBottom: '8px', fontSize: '11px', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Raw Telemetry</div>
                            <pre className="font-mono" style={{ margin: 0, fontSize: '11px', color: 'var(--color-text-primary)' }}>
                                {JSON.stringify(telemetry, null, 2)}
                            </pre>
                        </>
                    ) : (
                        <p className="caption text-muted">No hay telemetría raw disponible.</p>
                    )}
                </div>
            )}
        </div>
      </div>
    </div>
  )
}

function getSeverityColorToken(severity) {
    switch(severity) {
        case 'Alerta Crítica': return 'danger';
        case 'Alerta Severa': return 'warning';
        case 'Alerta Menor': return 'warning'; // Orange usually
        default: return 'secondary'; // Green/Blue
    }
}

AIDiagnosisCard.propTypes = {
  data: PropTypes.object,
  loading: PropTypes.bool
}

export default AIDiagnosisCard
