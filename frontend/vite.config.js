import { defineConfig } from 'vite';
const backend = process.env.PROMPTELIER_BACKEND_URL || 'http://127.0.0.1:8002';
export default defineConfig({ server: { port: 5173, strictPort: true, proxy: { '/api': backend } }, preview: { proxy: { '/api': backend } } });
