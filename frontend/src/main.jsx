import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './styles/theme.css'
import { ThemeProvider } from './providers/ThemeProvider.jsx'
import { AuthProvider } from './context/AuthContext.jsx'

// Punto de entrada del frontend (Vite + React).
createRoot(
  document.getElementById('root') || document.body.appendChild(document.createElement('div'))
).render(
  <React.StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  </React.StrictMode>
)
