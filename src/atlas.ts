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

/** Fotogramas con nombre propio. */
export const POSE = {
  ALERT: 0,
  REST: 1,
  ALERT_TO_REST: 2,
  REST_TO_ALERT: 3,
  SWAGGER_1: 4,
  SWAGGER_2: 5,
  WAVE_1: 6,
  WAVE_2: 7,
  HURT_ALERT: 24,
  HURT_REST: 25,
  DYING_1: 48,
  DYING_2: 49,
  DYING_3: 50,
  DEAD: 51,
  ATTACK_1: 52,
  ATTACK_2: 53,
  SCARED: 54,
  AMAZED: 55,
  STUMBLE: 56,
  FALL: 57,
  POWER: 58,
  TRAIT: 59,
  LOOK_AROUND: 60,
  TIRED: 61,
  VICTORY: 62,
  PORTRAIT: 63,
} as const;

/** Icono que se muestra mientras se mueve en cada dirección: siempre uno con las armas a la vista. */
const MOVE_ICON = { S: POSE.ALERT_TO_REST, N: 12, E: 17, O: 20 } as const;
/** Desplazamiento del bloque equivalente cuando el personaje está herido. */
const HURT_OFFSET = 24;

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
export function pickFrame(look: Pick<WarriorLook, 'facing' | 'moving' | 'walkAngle' | 'hurt' | 'alerted' | 'pose'>): FramePick {
  if (look.pose !== undefined) return { index: look.pose, mirror: false, hop: 0 };
  const shift = look.hurt === true ? HURT_OFFSET : 0;
  if (look.moving) {
    return { index: MOVE_ICON[look.facing], mirror: false, hop: Math.abs(Math.sin(look.walkAngle * 2)) * 0.035 };
  }
  return { index: (look.alerted ? POSE.ALERT : POSE.REST) + shift, mirror: false, hop: 0 };
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
