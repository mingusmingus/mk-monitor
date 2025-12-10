import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'

// Global Styles
import './styles/theme.css'
import './styles/layout.css'

// Component Styles
import './styles/components/button.css'
import './styles/components/input.css'

// Page Styles
import './styles/pages/login.css'
import './styles/pages/dashboard.css'
import './styles/pages/devices.css'
import './styles/pages/detail.css'

import { ThemeProvider } from './providers/ThemeProvider.jsx'
import { AuthProvider } from './context/AuthContext.jsx'

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
