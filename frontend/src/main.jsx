import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'

// Estilos Globales
import './styles/theme.css'
import './styles/layout.css'

// Estilos de Componentes
import './styles/components/button.css'
import './styles/components/input.css'

// Estilos de Páginas
import './styles/pages/login.css'
import './styles/pages/dashboard.css'
import './styles/pages/devices.css'
import './styles/pages/detail.css'

import { ThemeProvider } from './providers/ThemeProvider.jsx'
import { AuthProvider } from './context/AuthContext.jsx'

/**
 * Punto de entrada principal de la aplicación React.
 * Configura los proveedores de contexto globales (Router, Auth, Theme).
 */
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ThemeProvider>
          <App />
        </ThemeProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
