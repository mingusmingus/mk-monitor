import React, { createContext, useEffect, useMemo, useRef, useState } from 'react'

export const ThemeContext = createContext({ theme: 'light', isDark: false, toggleTheme: () => {} })

export function ThemeProvider({ children }) {
  const userPrefKey = 'theme'
  const media = useRef(typeof window !== 'undefined'
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : { matches: false, addEventListener: () => {}, removeEventListener: () => {} }
  )

  // Si no hay preferencia del usuario, seguimos el sistema
  const [followSystem, setFollowSystem] = useState(() => !localStorage.getItem(userPrefKey))

  const getInitialTheme = () => {
    const saved = localStorage.getItem(userPrefKey)
    if (saved === 'light' || saved === 'dark') return saved
    return media.current.matches ? 'dark' : 'light'
  }

  const [theme, setTheme] = useState(getInitialTheme)

  // Aplica data-theme en <html> para que toda la app consuma tokens
  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', theme)
  }, [theme])

  // Escucha cambios del sistema solo si seguimos el sistema
  useEffect(() => {
    const onChange = (e) => {
      if (followSystem) setTheme(e.matches ? 'dark' : 'light')
    }
    media.current.addEventListener?.('change', onChange)
    return () => media.current.removeEventListener?.('change', onChange)
  }, [followSystem])

  const toggleTheme = () => {
    setFollowSystem(false)
    setTheme((t) => {
      const next = t === 'dark' ? 'light' : 'dark'
      localStorage.setItem(userPrefKey, next)
      return next
    })
  }

  const value = useMemo(() => ({
    theme,
    isDark: theme === 'dark',
    toggleTheme
  }), [theme])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}