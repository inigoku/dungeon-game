/**
 * Personajes dibujados con bitmaps: un atlas de 8×8 fotogramas de 128×128 por clase.
 * Los 64 fotogramas siguen el orden descrito en art/README.md (índice = fila × 8 + columna).
 */
import type { Ctx } from './gfx';
import { glow, oval } from './sprites';
import type { WarriorLook } from './warrior';

export const CELL = 128;
export const COLUMNS = 8;
/** Fila del fotograma donde apoyan los pies y columna donde se centra el personaje. */
const BASELINE = 122;
const CENTER_X = 64;

/** Qué fotograma de la hoja de cada clase hace cada papel (cada hoja generada ordena las poses a su manera). */
export interface AtlasLayout {
  /** En guardia (armas a la vista) y en reposo. */
  guard: number;
  rest: number;
  /** Fotogramas en guardia y en reposo cuando está herido (si la hoja los distingue). */
  hurt?: { guard: number; rest: number };
  /** Icono de movimiento por dirección; `mirror` para dibujarlo reflejado. */
  move: Record<'N' | 'E' | 'S' | 'O', { index: number; mirror: boolean }>;
  /** Muerte (cuatro fotogramas seguidos) y caída por el barranco (tropiezo, caída). */
  dying: readonly [number, number, number, number];
  stumble: number;
  fall: number;
}

export const LAYOUTS: Record<string, AtlasLayout> = {
  barbaro: {
    guard: 0,
    rest: 1,
    hurt: { guard: 24, rest: 25 },
    move: { N: { index: 12, mirror: false }, E: { index: 17, mirror: false }, S: { index: 2, mirror: false }, O: { index: 20, mirror: false } },
    dying: [48, 49, 50, 51],
    stumble: 56,
    fall: 57,
  },
  // Caballero: de frente solo el 0-3 enseña la espada; en reposo se usa el fotograma neutro con la espada envainada
  guerrero: {
    guard: 0,
    rest: 8,
    hurt: { guard: 24, rest: 25 },
    move: { N: { index: 12, mirror: false }, E: { index: 18, mirror: false }, S: { index: 2, mirror: false }, O: { index: 22, mirror: false } },
    dying: [48, 49, 50, 51],
    stumble: 56,
    fall: 57,
  },
  // Dafne, la exploradora: siempre con el arco a la vista
  exploradora: {
    guard: 0,
    rest: 1,
    hurt: { guard: 24, rest: 25 },
    move: { N: { index: 11, mirror: false }, E: { index: 17, mirror: false }, S: { index: 9, mirror: false }, O: { index: 21, mirror: false } },
    dying: [48, 49, 50, 51],
    stumble: 56,
    fall: 57,
  },
  // Duelista: modelo 3D de dos espadas prerrenderizado; cada pose tiene su vista, y la caída se ve de perfil
  duelista: {
    guard: 0,
    rest: 1,
    hurt: { guard: 24, rest: 25 },
    move: { N: { index: 12, mirror: false }, E: { index: 17, mirror: false }, S: { index: 2, mirror: false }, O: { index: 20, mirror: false } },
    dying: [48, 49, 50, 51],
    stumble: 56,
    fall: 57,
  },
};

const atlases = new Map<string, HTMLImageElement>();

export function setAtlas(id: string, image: HTMLImageElement | null): void {
  if (image) atlases.set(id, image);
  else atlases.delete(id);
}

export function hasAtlas(id: string): boolean {
  return atlases.has(id);
}

export interface FramePick {
  index: number;
  /** Dibujar reflejado (para atlas que solo traen un lado). */
  mirror: boolean;
  /** Salto vertical (0..1 del tamaño) para dar sensación de paso con un solo icono. */
  hop: number;
}

/**
 * Elige el fotograma. Secuencia: en guardia → icono de movimiento → en guardia; pasados 3 s sin
 * enemigos cerca (`alerted` falso) se pasa a reposo.
 */
export function pickFrame(layout: AtlasLayout, look: Pick<WarriorLook, 'facing' | 'moving' | 'walkAngle' | 'hurt' | 'alerted' | 'pose'>): FramePick {
  if (look.pose !== undefined) return { index: look.pose, mirror: false, hop: 0 };
  if (look.moving) {
    const icon = layout.move[look.facing];
    return { index: icon.index, mirror: icon.mirror, hop: Math.abs(Math.sin(look.walkAngle * 2)) * 0.035 };
  }
  const frames = look.hurt === true && layout.hurt ? layout.hurt : layout;
  return { index: look.alerted ? frames.guard : frames.rest, mirror: false, hop: 0 };
}

/** Fotograma de la muerte según los ms transcurridos desde que cayó. */
export function dyingFrame(layout: AtlasLayout, ms: number): number {
  return layout.dying[ms < 350 ? 0 : ms < 700 ? 1 : ms < 1050 ? 2 : 3];
}

/** Fotograma de la caída por el barranco según su progreso (0..1). */
export function fallFrame(layout: AtlasLayout, t: number): number {
  return t < 0.3 ? layout.stumble : layout.fall;
}

/** Dibuja un fotograma del atlas con los pies en (cx, cy + 0,47·size), igual que los sprites vectoriales. */
export function drawAtlasFrame(ctx: Ctx, id: string, pick: FramePick, cx: number, cy: number, size: number, power: boolean): boolean {
  const atlas = atlases.get(id);
  if (!atlas) return false;
  const drawSize = size * 1.18;
  const row = Math.floor(pick.index / COLUMNS);
  const col = pick.index % COLUMNS;
  const feetY = cy + size * 0.47 - pick.hop * size;
  const dy = feetY - (BASELINE / CELL) * drawSize;

  // Sombra en el suelo
  ctx.fillStyle = 'rgba(0,0,0,0.34)';
  ctx.save();
  ctx.translate(cx, feetY + size * 0.005);
  ctx.scale(size / 100, size / 100);
  oval(ctx, 0, 0, 24, 5.4);
  ctx.fill();
  ctx.restore();
  if (power) glow(ctx, cx, cy - size * 0.08, size * 0.5, [190, 235, 255], 0.42);

  ctx.save();
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  if (pick.mirror) {
    ctx.translate(cx, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(atlas, col * CELL, row * CELL, CELL, CELL, -(CENTER_X / CELL) * drawSize, dy, drawSize, drawSize);
  } else {
    ctx.drawImage(atlas, col * CELL, row * CELL, CELL, CELL, cx - (CENTER_X / CELL) * drawSize, dy, drawSize, drawSize);
  }
  ctx.restore();
  return true;
}

/** Dibuja una imagen suelta (p. ej. un busto) ajustada al lienzo y apoyada abajo. false si no está cargada. */
export function drawPortraitImage(ctx: Ctx, id: string, width: number, height: number): boolean {
  const image = atlases.get(id);
  if (!image) return false;
  const k = Math.min(width / image.width, height / image.height);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(image, (width - image.width * k) / 2, height - image.height * k, image.width * k, image.height * k);
  return true;
}
