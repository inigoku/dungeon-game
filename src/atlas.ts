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

/** Primer fotograma (el de "mirando") de cada dirección; la hoja trae el oeste dibujado. */
const DIRECTION_BASE = { S: 8, N: 12, E: 16, O: 20 } as const;
/** Desplazamiento del bloque equivalente cuando el personaje está herido. */
const HURT_OFFSET = 24;
/** Ciclo de marcha sobre los tres fotogramas de movimiento: paso A, pasada, paso B, pasada. */
const WALK_CYCLE = [1, 2, 3, 2] as const;

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
}

/** Elige el fotograma según el estado del personaje. */
export function pickFrame(look: Pick<WarriorLook, 'facing' | 'moving' | 'walkAngle' | 'hurt' | 'alerted' | 'pose'>): FramePick {
  const mirror = false;
  if (look.pose !== undefined) return { index: look.pose, mirror: false };
  const hurt = look.hurt === true;
  const base = DIRECTION_BASE[look.facing] + (hurt ? HURT_OFFSET : 0);
  if (look.moving) {
    const turn = Math.PI * 2;
    const phase = Math.floor((((look.walkAngle % turn) + turn) % turn) / turn * WALK_CYCLE.length) % WALK_CYCLE.length;
    return { index: base + WALK_CYCLE[phase], mirror };
  }
  if (look.facing === 'S') {
    const index = look.alerted ? POSE.ALERT : POSE.REST;
    return { index: index + (hurt ? HURT_OFFSET : 0), mirror: false };
  }
  return { index: base, mirror };
}

/** Dibuja un fotograma del atlas con los pies en (cx, cy + 0,47·size), igual que los sprites vectoriales. */
export function drawAtlasFrame(ctx: Ctx, id: string, pick: FramePick, cx: number, cy: number, size: number, power: boolean): boolean {
  const atlas = atlases.get(id);
  if (!atlas) return false;
  const drawSize = size * 1.18;
  const row = Math.floor(pick.index / COLUMNS);
  const col = pick.index % COLUMNS;
  const feetY = cy + size * 0.47;
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
