import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Configuración de Vite para React + mk-monitor
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // Permite acceso desde la red local
    // Proxy opcional para evitar CORS en desarrollo
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
