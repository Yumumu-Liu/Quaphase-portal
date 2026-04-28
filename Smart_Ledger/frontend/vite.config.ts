import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  base: '/Quaphase-portal/Smart_Ledger/frontend/dist/',
  plugins: [
    tailwindcss(),
    react()
  ],
})