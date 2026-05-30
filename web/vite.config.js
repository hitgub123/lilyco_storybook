import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [react()],
	build: {
		terserOptions: {
			compress: {
				// a. 在生产环境中移除 console.log
				drop_console: true,
				// b. 移除 debugger
				drop_debugger: true,
			},
		},
	},
})