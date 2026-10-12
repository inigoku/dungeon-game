/** Carga de imágenes y sonidos. Lo que falle al cargar queda en null y el juego sigue sin ello. */
import { Mixer } from './audio';
import { context2d, createCanvas, type Canvas } from './gfx';

export const IMAGE_NAMES = ['titulo', 'losa', 'profundo', 'espada', 'antorcha', 'sangre'] as const;
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

export interface Assets {
  mixer: Mixer;
  images: Record<string, HTMLImageElement | null>;
  buffers: Record<string, AudioBuffer | null>;
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

async function loadSound(mixer: Mixer, url: string): Promise<AudioBuffer | null> {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await mixer.decode(await response.arrayBuffer());
  } catch (error) {
    console.warn(`No se pudo cargar ${url}:`, error);
    return null;
  }
}

/** Carga todos los recursos informando del progreso (0..1). */
export async function loadAssets(onProgress: (fraction: number) => void): Promise<Assets> {
  const mixer = new Mixer();
  const images: Assets['images'] = {};
  const buffers: Assets['buffers'] = {};
  const total = IMAGE_NAMES.length + SOUND_NAMES.length;
  let done = 0;
  const tick = () => onProgress(++done / total);

  await Promise.all([
    ...IMAGE_NAMES.map(async (name) => {
      images[name] = await loadImage(`images/${name}.png`);
      tick();
    }),
    ...SOUND_NAMES.map(async (name) => {
      buffers[name] = await loadSound(mixer, `sound/${name}.ogg`);
      tick();
    }),
  ]);
  return { mixer, images, buffers };
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
