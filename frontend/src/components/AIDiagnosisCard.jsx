import React, { useState } from 'react';
import Card from './ui/Card.jsx';
import Button from './ui/Button.jsx';

/**
 * AIDiagnosisCard
 *
 * Displays strict forensic analysis from the AI Provider.
 * Supports:
 * - Header: Title + Severity Badge
 * - Body: Root Cause (Analysis)
 * - Details: Technical Evidence (Collapsible)
 * - Actions: Recommendations
 */
export default function AIDiagnosisCard({ diagnosis, onAction }) {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!diagnosis) return null;

    // Mapping for severity badges
    const getSeverityBadge = (severity) => {
        const normalized = severity?.toLowerCase() || 'aviso';
        const styles = {
            'alerta crítica': { bg: 'var(--color-accent-danger)', color: 'white' },
            'alerta severa': { bg: 'var(--color-accent-warning)', color: 'white' },
            'alerta menor': { bg: 'var(--color-accent-secondary)', color: 'white' },
            'aviso': { bg: 'var(--color-bg-tertiary)', color: 'var(--color-text-secondary)' }
        };
        const style = styles[normalized] || styles['aviso'];

        return (
            <span style={{
                backgroundColor: style.bg,
                color: style.color,
                padding: '2px 8px',
                borderRadius: 'var(--radius-full)',
                fontSize: 'var(--font-size-caption)',
                fontWeight: 'var(--font-weight-bold)',
                textTransform: 'uppercase'
            }}>
                {severity}
            </span>
        );
    };

    // Parsing the raw technical evidence if it's a string
    const getTelemetryData = () => {
        const telemetry = diagnosis.telemetry || {};
        // If it's complex, we might just JSON stringify it for now
        // or try to render key tables.
        return telemetry;
    };

    const telemetry = getTelemetryData();
    const hasTelemetry = telemetry && Object.keys(telemetry).length > 0;

    return (
        <Card>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span role="img" aria-label="AI" style={{ fontSize: '18px' }}>🤖</span>
                    <h3 className="h3" style={{ margin: 0 }}>Análisis Forense IA</h3>
                </div>
                {getSeverityBadge(diagnosis.estado || diagnosis.severity)}
            </div>

            {/* Body: Root Cause / Analysis */}
            <div style={{ marginBottom: '16px' }}>
                <p className="body-md" style={{ color: 'var(--color-text-primary)' }}>
                    {diagnosis.analysis || diagnosis.descripcion}
                </p>
            </div>

            {/* Recommendations Actions */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                {diagnosis.recommendations && diagnosis.recommendations.map((rec, idx) => (
                    <Button key={idx} variant="secondary" size="sm" onClick={() => onAction && onAction(rec)}>
                        {rec}
                    </Button>
                ))}
                {/* Fallback if just one string in accion_recomendada */}
                {!diagnosis.recommendations && diagnosis.accion_recomendada && (
                    <Button variant="secondary" size="sm" onClick={() => onAction && onAction(diagnosis.accion_recomendada)}>
                        {diagnosis.accion_recomendada}
                    </Button>
                )}
            </div>

            {/* Footer: Technical Evidence Disclosure */}
            {hasTelemetry && (
                <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '12px' }}>
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--color-text-secondary)',
                            fontSize: 'var(--font-size-sm)',
                            fontWeight: 'var(--font-weight-medium)',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: 0
                        }}
                    >
                        {isExpanded ? '▼ Ocultar Evidencia Técnica' : '▶ Ver Evidencia Técnica'}
                    </button>

                    {isExpanded && (
                        <div style={{
                            marginTop: '12px',
                            backgroundColor: 'var(--color-bg-secondary)',
                            borderRadius: 'var(--radius-sm)',
                            padding: '12px',
                            overflowX: 'auto'
                        }}>
                            {/* Render Telemetry Tables */}
                            {telemetry.interface_errors && Object.keys(telemetry.interface_errors).length > 0 && (
                                <div style={{ marginBottom: '12px' }}>
                                    <h4 className="caption" style={{ textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Errores de Interfaz</h4>
                                    <pre style={{ margin: 0, fontSize: '11px', fontFamily: 'monospace' }}>
                                        {JSON.stringify(telemetry.interface_errors, null, 2)}
                                    </pre>
                                </div>
                            )}

                            {/* Generic Telemetry Fallback */}
                             <h4 className="caption" style={{ textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Data Cruda</h4>
                             <pre style={{ margin: 0, fontSize: '11px', fontFamily: 'monospace', color: 'var(--color-text-primary)' }}>
                                {JSON.stringify(telemetry, null, 2)}
                            </pre>
                        </div>
                    )}
                </div>
            )}
        </Card>
    );
}
