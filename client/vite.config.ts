import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/cv-api': {
        target: 'https://dev-search.cancervariants.org',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/cv-api/, ''),
        secure: true,
      },
    },
  },
})
