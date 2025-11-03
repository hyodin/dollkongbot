import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/dollkongbot/',
  plugins: [react()],
  server: {
    port: 3005,
    proxy: {
      '/api/dollkongbot/': {
        target: 'http://127.0.0.1:5000/',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      }
    },
    allowedHosts: ['www.yncsmart.com', 'yncsmart.com']
  },
  build: {
    outDir: '/opt/dollkongbot/frontend/dist',
    sourcemap: true
  }
})
