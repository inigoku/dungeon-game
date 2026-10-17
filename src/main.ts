/** Punto de entrada: carga los recursos, espera un gesto del usuario (audio) y lanza el juego. */
import { setAtlas } from './atlas';
import { loadAssets, type Assets } from './assets';
import { CLASSES, CLASS_IDS, initialClass, rememberClass, type PlayerClass } from './classes';
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
const classBox = element<HTMLDivElement>('classes');

let selectedClass: PlayerClass = initialClass();
element<HTMLDivElement>('version').textContent = `versión ${__BUILD__}`;

/** Botones de clase con un pequeño retrato de cada una. */
function buildClassPicker(): void {
  for (const id of CLASS_IDS) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.cls = id;
    button.setAttribute('role', 'radio');
    const canvas = document.createElement('canvas');
    canvas.width = 110;
    canvas.height = 134;
    const ctx = canvas.getContext('2d');
    ctx?.clearRect(0, 0, 110, 134);
    CLASSES[id].draw(ctx as CanvasRenderingContext2D, 55, 70, 118, { walkAngle: 0, moving: false, facing: 'S', headTurn: 0, showWeapons: true, swordPower: false, now: 0 });
    button.append(canvas, document.createTextNode(CLASSES[id].label));
    button.addEventListener('click', () => {
      selectedClass = id;
      rememberClass(id);
      refreshClassPicker();
    });
    classBox.append(button);
  }
  refreshClassPicker();
}

function refreshClassPicker(): void {
  for (const button of classBox.querySelectorAll<HTMLButtonElement>('button')) {
    const on = button.dataset.cls === selectedClass;
    button.classList.toggle('on', on);
    button.setAttribute('aria-checked', String(on));
  }
}

function showOverlay(title: string, text: string, button: string | null, pickClass = false): Promise<void> {
  overlayTitle.textContent = title;
  overlayText.textContent = text;
  bar.hidden = true;
  action.hidden = button === null;
  classBox.hidden = !pickClass;
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
    const game = new Game(canvas, assets, selectedClass);
    // ?debug expone la partida en la consola del navegador (window.__game)
    if (new URLSearchParams(location.search).has('debug')) (window as unknown as { __game: Game }).__game = game;
    const restart = await game.run();
    if (restart) continue;
    // Salir lleva de nuevo a la selección de personaje
    await showOverlay('Dungeon Explorer 2D', 'Explora la mazmorra, encuentra la salida y sobrevive. Mejor con auriculares.', 'Empezar', true);
  }
}

/** Panel para diagnosticar el audio en el móvil: se abre con `?audio` en la dirección. */
function showAudioPanel(assets: Assets): void {
  const panel = document.createElement('div');
  panel.style.cssText =
    'position:fixed;left:6px;top:6px;right:6px;z-index:10;padding:8px;border-radius:6px;background:rgba(0,0,0,.82);color:#9f9;font:11px/1.35 monospace;white-space:pre-wrap;max-height:55vh;overflow:auto';
  const text = document.createElement('div');
  const beep = document.createElement('button');
  beep.textContent = 'Probar sonido';
  beep.style.cssText = 'margin-top:6px;padding:6px 10px;font:inherit';
  panel.append(text, beep);
  document.body.append(panel);

  const { mixer, audioDiag } = assets;
  beep.addEventListener('click', () => {
    void mixer.unlock().then(() => {
      const osc = mixer.ctx.createOscillator();
      const gain = mixer.ctx.createGain();
      gain.gain.value = 0.25;
      osc.frequency.value = 440;
      osc.connect(gain).connect(mixer.ctx.destination);
      osc.start();
      osc.stop(mixer.ctx.currentTime + 0.4);
    });
  });
  const refresh = () => {
    const formats = Object.values(audioDiag.formats);
    const session = (navigator as unknown as { audioSession?: { type: string } }).audioSession;
    text.textContent = [
      `contexto: ${mixer.ctx.state} @ ${mixer.ctx.sampleRate} Hz`,
      `audioSession: ${session ? session.type : 'no disponible'}`,
      `ogg soportado: ${audioDiag.oggSupported}`,
      `sonidos: ${formats.filter(Boolean).length}/${formats.length} (ogg ${formats.filter((f) => f === 'ogg').length}, m4a ${formats.filter((f) => f === 'm4a').length})`,
      ...audioDiag.errors.slice(0, 6).map((e) => `! ${e}`),
    ].join('\n');
  };
  refresh();
  setInterval(refresh, 500);
}

async function boot(): Promise<void> {
  const assets = await loadAssets((fraction) => {
    barFill.style.width = `${Math.round(fraction * 100)}%`;
  });
  setAtlas('barbaro', assets.images['atlas_barbaro'] ?? null);
  setAtlas('retrato_barbaro', assets.images['retrato_barbaro'] ?? null);
  setAtlas('guerrero', assets.images['atlas_guerrero'] ?? null);
  setAtlas('retrato_guerrero', assets.images['retrato_guerrero'] ?? null);
  setAtlas('exploradora', assets.images['atlas_exploradora'] ?? null);
  setAtlas('retrato_exploradora', assets.images['retrato_exploradora'] ?? null);
  if (new URLSearchParams(location.search).has('audio')) showAudioPanel(assets);
  // Los navegadores solo dejan sonar el audio tras un gesto del usuario
  buildClassPicker();
  await showOverlay('Dungeon Explorer 2D', 'Explora la mazmorra, encuentra la salida y sobrevive. Mejor con auriculares.', 'Empezar', true);
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
