import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 4040,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5040',
        changeOrigin: true,
      },
    },
  },
});
