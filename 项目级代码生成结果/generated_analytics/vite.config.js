import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "./src/assets/styles/main.scss";`
      }
    }
  },
  server: {
    port: 3000,
    host: true
  },
  build: {
    target: 'esnext',
    minify: 'esbuild'
  }
})