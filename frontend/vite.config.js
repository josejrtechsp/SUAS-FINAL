import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// Dica: para gerar um relatório visual do bundle, rode:
//   npm run analyze
// e abra o arquivo: dist/stats.html
export default defineConfig(async ({ mode }) => {
  const analyze = process.env.ANALYZE === 'true' || mode === 'analyze'

  const plugins = [react()]

  if (analyze) {
    // Import lazy para não exigir a dependência em builds normais.
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

  return { plugins }
})
