import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup.js',
    include: ['src/tests/**/*.test.{js,jsx}'],
    // Tests must never call a real backend (CI has no server and no .env file),
    // so force the API client into mock mode for every test run.
    env: { VITE_USE_MOCK: 'true' },
  },
})
