import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Configuración mínima de Vite para React.
// Proxy opcional si prefieres usar rutas relativas /api* en desarrollo.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // proxy: { '/api': 'http://localhost:5000' }
  }
})
