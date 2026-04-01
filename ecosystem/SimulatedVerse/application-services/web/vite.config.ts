import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    port: 5000,
    host: '0.0.0.0'
  },
  build: {
    target: 'es2020',
    outDir: 'dist'
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
})