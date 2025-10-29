import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Configuración mínima de Vite para React.
// Ajustar proxy si se desea reenviar /api al backend Flask.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
    // proxy: { '/api': 'http://localhost:8000' }
  }
})
