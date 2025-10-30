import React, { useContext } from 'react'
import { ThemeContext } from '../../context/ThemeContext.jsx'

// Botón para alternar tema claro/oscuro.
export default function ThemeToggle() {
  const { theme, toggleTheme } = useContext(ThemeContext)
  return (
    <button className="btn" onClick={toggleTheme}>
      Tema: {theme === 'dark' ? 'Oscuro' : 'Claro'}
    </button>
  )
}
