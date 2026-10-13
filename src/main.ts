/** Punto de entrada: carga los recursos, espera un gesto del usuario (audio) y lanza el juego. */
import { loadAssets, type Assets } from './assets';
import { Game } from './game';

function element<T extends HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Falta el elemento #${id}`);
  return el as T;
}

const canvas = element<HTMLCanvasElement>('game');
const overlay = element<HTMLDivElement>('overlay');
const overlayTitle = element<HTMLHeadingElement>('overlay-title');
const overlayText = element<HTMLParagraphElement>('overlay-text');
const bar = element<HTMLDivElement>('bar');
const barFill = element<HTMLDivElement>('bar-fill');
const action = element<HTMLButtonElement>('action');

function showOverlay(title: string, text: string, button: string | null): Promise<void> {
  overlayTitle.textContent = title;
  overlayText.textContent = text;
  bar.hidden = true;
  action.hidden = button === null;
  overlay.hidden = false;
  if (button === null) return Promise.resolve();

  action.textContent = button;
  action.focus();
  return new Promise((resolve) => {
    const done = () => {
      window.removeEventListener('keydown', onKey);
      action.removeEventListener('click', done);
      resolve();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ' || e.key.length === 1) {
        e.preventDefault();
        done();
      }
    };
    window.addEventListener('keydown', onKey);
    action.addEventListener('click', done);
  });
}

async function playLoop(assets: Assets): Promise<void> {
  for (;;) {
    overlay.hidden = true;
    canvas.focus();
    const game = new Game(canvas, assets);
    // ?debug expone la partida en la consola del navegador (window.__game)
    if (new URLSearchParams(location.search).has('debug')) (window as unknown as { __game: Game }).__game = game;
    const restart = await game.run();
    if (restart) continue;
    await showOverlay('Has salido de la mazmorra', 'Gracias por jugar.', 'Jugar de nuevo');
  }
}

async function boot(): Promise<void> {
  const assets = await loadAssets((fraction) => {
    barFill.style.width = `${Math.round(fraction * 100)}%`;
  });
  // Los navegadores solo dejan sonar el audio tras un gesto del usuario
  await showOverlay('Dungeon Explorer 2D', 'Explora la mazmorra, encuentra la salida y sobrevive. Mejor con auriculares.', 'Empezar');
  await assets.mixer.unlock();
  await playLoop(assets);
}

// Controles táctiles: cada botón lanza la tecla equivalente
for (const button of document.querySelectorAll<HTMLButtonElement>('#touch button')) {
  button.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    window.dispatchEvent(new KeyboardEvent('keydown', { key: button.dataset.key }));
  });
}
boot().catch((error) => {
  console.error(error);
  overlayTitle.textContent = 'Error';
  overlayText.textContent = 'No se pudo iniciar el juego. Revisa la consola del navegador.';
  bar.hidden = true;
  overlay.hidden = false;
});
