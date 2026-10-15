/** Carga de imágenes y sonidos. Lo que falle al cargar queda en null y el juego sigue sin ello. */
import { Mixer } from './audio';
import { context2d, createCanvas, type Canvas } from './gfx';

export const IMAGE_NAMES = ['titulo', 'losa', 'profundo', 'espada', 'antorcha', 'sangre', 'atlas_barbaro'] as const;
export const SOUND_NAMES = [
  'abominacion',
  'adagio',
  'alataque',
  'antorchas',
  'cthulhu',
  'dos-gotas',
  'espada',
  'gota',
  'grunido',
  'intro',
  'mordisco',
  'murcielago',
  'paso1',
  'paso2',
  'rafaga',
  'sangre',
  'viento',
  'zumbido_espada',
] as const;

/** Resultado de la carga de sonidos, para diagnosticar el audio en dispositivos concretos. */
export interface AudioDiag {
  /** Formato con el que se cargó cada sonido (null si no se pudo). */
  formats: Record<string, 'ogg' | 'm4a' | null>;
  errors: string[];
  oggSupported: boolean;
}

export interface Assets {
  mixer: Mixer;
  images: Record<string, HTMLImageElement | null>;
  buffers: Record<string, AudioBuffer | null>;
  audioDiag: AudioDiag;
}

function loadImage(url: string): Promise<HTMLImageElement | null> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => {
      console.warn(`No se pudo cargar ${url}`);
      resolve(null);
    };
    img.src = url;
  });
}

/** Safari/iOS (incluido Chrome en iPhone) no reproduce OGG Vorbis: se usa M4A directamente. */
function oggSupported(): boolean {
  try {
    return document.createElement('audio').canPlayType('audio/ogg; codecs="vorbis"') !== '';
  } catch {
    return true;
  }
}

/** Falla si la promesa no se resuelve a tiempo (en iOS una decodificación puede quedarse colgada). */
function withTimeout<T>(promise: Promise<T>, ms: number, what: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`${what}: sin respuesta en ${ms} ms`)), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

async function fetchDecode(mixer: Mixer, url: string): Promise<AudioBuffer> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return await mixer.decode(await response.arrayBuffer());
}

/** Carga un sonido en el mejor formato soportado, con el otro como respaldo. */
async function loadSound(mixer: Mixer, name: string, diag: AudioDiag): Promise<AudioBuffer | null> {
  const order: Array<'ogg' | 'm4a'> = diag.oggSupported ? ['ogg', 'm4a'] : ['m4a', 'ogg'];
  for (const ext of order) {
    const url = `sound/${name}.${ext}`;
    try {
      const buffer = await withTimeout(fetchDecode(mixer, url), 15000, url);
      diag.formats[name] = ext;
      return buffer;
    } catch (error) {
      const message = `${url}: ${error instanceof Error ? error.message : String(error)}`;
      diag.errors.push(message);
      console.warn(`No se pudo cargar ${message}`);
    }
  }
  diag.formats[name] = null;
  return null;
}

/** Carga todos los recursos informando del progreso (0..1). */
export async function loadAssets(onProgress: (fraction: number) => void): Promise<Assets> {
  const mixer = new Mixer();
  const images: Assets['images'] = {};
  const buffers: Assets['buffers'] = {};
  const audioDiag: AudioDiag = { formats: {}, errors: [], oggSupported: oggSupported() };
  const total = IMAGE_NAMES.length + SOUND_NAMES.length;
  let done = 0;
  const tick = () => onProgress(++done / total);

  await Promise.all([
    ...IMAGE_NAMES.map(async (name) => {
      images[name] = await loadImage(`images/${name}.png`);
      tick();
    }),
    ...SOUND_NAMES.map(async (name) => {
      buffers[name] = await loadSound(mixer, name, audioDiag);
      tick();
    }),
  ]);
  return { mixer, images, buffers, audioDiag };
}

/** Escala una imagen a (w, h) con suavizado de calidad alta. */
export function scaleImage(img: HTMLImageElement, w: number, h: number): Canvas {
  const canvas = createCanvas(w, h);
  const ctx = context2d(canvas);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  return canvas;
}

/** Escala `img` para que quepa en (maxW, maxH) manteniendo la proporción. */
export function fitImage(img: HTMLImageElement, maxW: number, maxH: number): Canvas {
  const scale = Math.min(maxW / img.width, maxH / img.height);
  return scaleImage(img, Math.trunc(img.width * scale), Math.trunc(img.height * scale));
}
