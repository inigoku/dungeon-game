/** Errores inesperados: se registran y se muestran en pantalla (una sola vez) para poder diagnosticarlos en el móvil. */
let shown = false;

export function reportError(error: unknown): void {
  console.error(error);
  if (shown || typeof document === 'undefined') return;
  shown = true;
  const text = error instanceof Error ? `${error.name}: ${error.message}\n${(error.stack ?? '').split('\n').slice(0, 4).join('\n')}` : String(error);
  const box = document.createElement('pre');
  box.textContent = `Error del juego (toca para ocultar)\n${text}`;
  box.style.cssText =
    'position:fixed;left:8px;right:8px;top:8px;z-index:99999;margin:0;padding:8px;max-height:40vh;overflow:auto;' +
    'background:rgba(120,0,0,.92);color:#fff;font:11px/1.35 monospace;white-space:pre-wrap;border-radius:6px;';
  box.addEventListener('pointerdown', () => box.remove());
  document.body.append(box);
}
