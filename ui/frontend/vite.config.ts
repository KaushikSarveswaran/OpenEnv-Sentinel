import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: path.resolve(__dirname, '../backend/static'),
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/run-api': {
        target: 'http://localhost:8502',
        rewrite: (path: string) => path.replace(/^\/run-api/, ''),
      },
      '/api': 'http://localhost:8501',
    },
  },
})
