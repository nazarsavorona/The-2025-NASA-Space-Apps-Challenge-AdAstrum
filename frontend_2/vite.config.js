import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  server: {
    port: 3000,
    open: true,
    fs: {
      // Allow serving files from node_modules
      allow: ['..']
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  resolve: {
    alias: {
      'spacekit-assets': resolve(__dirname, 'node_modules/spacekit.js/src/assets')
    }
  },
  optimizeDeps: {
    exclude: ['spacekit.js']
  }
});
