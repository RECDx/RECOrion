import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Docker içinde "backend:8000", local çalışırken "localhost:8000"
const target = process.env.BACKEND_URL || (process.env.NODE_ENV === 'production' ? 'http://backend:8000' : 'http://backend:8000');

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    watch: {
      usePolling: true,
      interval: 500,
    },
    proxy: {
      '/api': {
        target: process.env.BACKEND_URL || 'http://backend:8000',
        changeOrigin: true,
      }
    }
  }
})
