import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Output goes directly into the Django app's static directory so that
// `python manage.py runserver` can serve the built files without any extra copy step.
const DJANGO_STATIC_DIR = path.resolve(
  __dirname,
  '../apps/react_app/static/react_app',
)

export default defineConfig({
  plugins: [react(), tailwindcss()],

  // Base URL must match where Django serves static files.
  base: '/static/react_app/',

  build: {
    outDir: DJANGO_STATIC_DIR,
    emptyOutDir: true,
    // Use predictable (non-hashed) filenames so the Django template can reference
    // them directly with {% static %} tags.
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'),
      output: {
        entryFileNames: 'index.js',
        chunkFileNames: 'chunks/[name].js',
        assetFileNames: (info) => {
          if (info.names?.some((n) => n.endsWith('.css'))) return 'index.css'
          return 'assets/[name][extname]'
        },
      },
    },
  },
})

