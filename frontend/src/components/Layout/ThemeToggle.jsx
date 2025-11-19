import React, { useContext } from 'react'
import { ThemeContext } from '../../providers/ThemeProvider.jsx'

// Botón accesible para alternar tema (28–32px) con icono Sol/Luna.
export default function ThemeToggle() {
  const { theme, isDark, toggleTheme } = useContext(ThemeContext)

  return (
    <button
      type="button"
      className="btn glass"
      onClick={toggleTheme}
      aria-pressed={isDark}
      aria-label={isDark ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
      title={isDark ? 'Tema oscuro (click para claro)' : 'Tema claro (click para oscuro)'}
      style={{ width: 36, height: 36, display: 'inline-grid', placeItems: 'center', padding: 0 }}
    >
      {isDark ? (
        // Sol (tema oscuro activo -> ofrece pasar a claro)
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 4V2M12 22v-2M4 12H2m20 0h-2M5 5 3.5 3.5M20.5 20.5 19 19M5 19 3.5 20.5M20.5 3.5 19 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
          <circle cx="12" cy="12" r="4.5" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      ) : (
        // Luna (tema claro activo -> ofrece pasar a oscuro)
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" stroke="currentColor" strokeWidth="1.6" fill="currentColor"/>
        </svg>
      )}
    </button>
  )
}
