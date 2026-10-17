import { defineConfig, type Plugin } from 'vite';
import { cpSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

/** Copia las carpetas de recursos (imágenes y sonido) al directorio de salida. */
function copyAssets(): Plugin {
  return {
    name: 'copy-game-assets',
    apply: 'build',
    closeBundle() {
      for (const dir of ['images', 'sound']) {
        const from = resolve(__dirname, dir);
        if (existsSync(from)) cpSync(from, resolve(__dirname, 'dist', dir), { recursive: true });
      }
    },
  };
}

export default defineConfig({
  // Ruta relativa: funciona tanto en la raíz como en un subdirectorio (GitHub Pages)
  base: './',
  // `public/` solo lleva el manifiesto de la aplicación: se copia tal cual a la raíz de `dist`
  publicDir: 'public',
  plugins: [copyAssets()],
  build: { outDir: 'dist', target: 'es2022' },
});
