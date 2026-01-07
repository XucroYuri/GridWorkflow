import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // rewrite: (path) => path.replace(/^\/api/, ''), // 取决于后端是否带 /api 前缀，FastAPI 通常会有 /api/v1 或直接路由。
        // 根据 backend/app/main.py，如果包含 api router，通常前缀在后端定义。
        // 假设后端是 /api/health，则不需要 rewrite。如果是 /health，则需要。
        // 我先不 rewrite，通常规范是后端处理 /api 前缀。
      }
    }
  }
})
