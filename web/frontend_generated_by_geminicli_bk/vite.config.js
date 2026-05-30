import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/workers-api': {
        target: 'http://localhost:8788', // Wrangler dev server 的默认地址
        changeOrigin: true,
        rewrite: (path) => {
          const newPath = path.replace(/^\/workers-api/, '/api');

          // 关键日志：在终端里打印出路径重写的过程
          console.log(`[Vite Proxy] Rewriting path: "${path}"  ->  "${newPath}"`);

          return newPath;
        },
        // 新增 configure 钩子，用于监听代理事件，提供更详细的日志
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.error('[Vite Proxy] Error: ', err);

          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // 关键日志：打印出最终要请求到后端的完整 URL
            console.log(`[Vite Proxy] Sending request to: ${options.target}${proxyReq.path}`);

          });

        }
      },
    },
  },
})

