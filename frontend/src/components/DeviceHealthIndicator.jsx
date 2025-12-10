import React from 'react';

/**
 * HealthWidget
 *
 * Renders vital signs (Voltage, Temperature) with discrete status indicators.
 * Used in Device Details header or info card.
 */
export default function HealthWidget({ health }) {
    if (!health) return null;

    const { voltage, temperature } = health;

    // Helper to determine status color
    const getStatusColor = (val, type) => {
        if (!val) return 'var(--color-text-muted)';
        const num = parseFloat(val);

        if (type === 'voltage') {
            // Rough heuristic: assuming 24V system, below 20 might be bad?
            // Or just check if it exists for now as neutral unless critical flag is passed.
            // Let's stick to neutral unless specifically low (e.g. < 10 for 12V/24V systems)
            if (num < 10) return 'var(--color-accent-danger)';
            return 'var(--color-text-secondary)';
        }
        if (type === 'temp') {
            if (num > 70) return 'var(--color-accent-danger)'; // Hot
            if (num > 50) return 'var(--color-accent-warning)'; // Warm
            return 'var(--color-text-secondary)';
        }
        return 'var(--color-text-secondary)';
    };

    return (
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            {voltage && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: 'var(--font-size-sm)' }}>
                    <span role="img" aria-label="voltage">⚡</span>
                    <span style={{ color: getStatusColor(voltage, 'voltage'), fontWeight: 500 }}>
                        {voltage}V
                    </span>
                </div>
            )}
            {temperature && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: 'var(--font-size-sm)' }}>
                    <span role="img" aria-label="temp">🌡️</span>
                    <span style={{ color: getStatusColor(temperature, 'temp'), fontWeight: 500 }}>
                        {temperature}C
                    </span>
                </div>
            )}
        </div>
    );
}
