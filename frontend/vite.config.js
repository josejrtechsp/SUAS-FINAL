import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(async ({ mode }) => {
  const analyze = process.env.ANALYZE === 'true' || mode === 'analyze'

  const plugins = [react()]

  if (analyze) {
    const { visualizer } = await import('rollup-plugin-visualizer')
    plugins.push(
      visualizer({
        filename: 'dist/stats.html',
        template: 'treemap',
        gzipSize: true,
        brotliSize: true,
        open: false,
      }),
    )
  }

  return {
    base: '/SUAS-FINAL/',   // 👈 necessário para GitHub Pages
    plugins,
  }
})
