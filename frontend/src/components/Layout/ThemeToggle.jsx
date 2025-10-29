import React, { useContext } from 'react'
import { ThemeContext } from '../../context/ThemeContext.jsx'

// Botón para alternar tema claro/oscuro (placeholder).
export default function ThemeToggle() {
  const { theme, toggleTheme } = useContext(ThemeContext)
  return <button onClick={toggleTheme}>Tema: {theme}</button>
}
