import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // TODO: Change 'beautify_comments' to your repository name if it's different
  base: '/beautify_comments/',
})
