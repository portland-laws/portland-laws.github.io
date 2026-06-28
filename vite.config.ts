import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

const transformersOrtBundle = path.resolve(
  __dirname,
  'node_modules/@huggingface/transformers/node_modules/onnxruntime-web/dist/ort.webgpu.bundle.min.mjs',
);

// https://vitejs.dev/config/
export default defineConfig({
  base: '/',
  plugins: [react()],
  resolve: {
    alias: [
      { find: /^onnxruntime-web$/, replacement: transformersOrtBundle },
    ],
  },
  server: {
    allowedHosts: ['portland-laws.github.io', 'localhost', '127.0.0.1'],
    watch: {
      ignored: ['**/ppd/**', '**/ipfs_datasets_py/**', '**/.cache/**', '**/dist/**'],
    },
    headers: {
      // Enable SharedArrayBuffer for WebAssembly threading
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Opener-Policy': 'same-origin',
    },
  },
  build: {
    target: 'es2020', // Ensure modern browser features are supported
    rollupOptions: {
      onwarn(warning, warn) {
        // All warnings are now processed normally
        warn(warning);
      },
    },
  },
  worker: {
    format: 'es',
  },
  optimizeDeps: {
    entries: ['index.html'],
    exclude: ['@huggingface/transformers'], // Exclude transformers.js from pre-bundling to avoid issues with WASM
  },
  // define: {
  //   global: 'globalThis', // Commented out to avoid breaking module name resolution
  // },
});
