/**
 * Sprites vectoriales del guerrero y de los Profundos, en el estilo de dibujo animado de
 * las imágenes de los pensamientos (contornos gruesos, colores cálidos y apagados).
 *
 * Cada sprite se dibuja en un cuadro de 100×100 unidades centrado en (0, 0) y se escala
 * con `size`, así que todas las medidas de aquí son relativas al tamaño del personaje.
 */
import type { Ctx, RGB } from './gfx';
import { rgb } from './gfx';

type Pt = readonly [number, number];

// ---------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------

const OUTLINE: RGB = [38, 22, 16];

function shade(c: RGB, k: number): RGB {
  return [Math.min(255, c[0] * k), Math.min(255, c[1] * k), Math.min(255, c[2] * k)];
}

function path(ctx: Ctx, points: readonly Pt[], close = true): void {
  ctx.beginPath();
  points.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
  if (close) ctx.closePath();
}

function oval(ctx: Ctx, cx: number, cy: number, rx: number, ry: number, rotation = 0): void {
  ctx.beginPath();
  ctx.ellipse(cx, cy, Math.max(0.01, rx), Math.max(0.01, ry), rotation, 0, Math.PI * 2);
}

type Paint = string | CanvasGradient | RGB;

/** Rellena el trazado actual y le pone el contorno grueso del estilo. */
function fillStroke(ctx: Ctx, fill: Paint, width = 2, stroke: RGB = OUTLINE): void {
  ctx.fillStyle = typeof fill === 'string' || !Array.isArray(fill) ? (fill as string | CanvasGradient) : rgb(fill as RGB);
  ctx.fill();
  if (width > 0) {
    ctx.strokeStyle = rgb(stroke);
    ctx.lineWidth = width;
    ctx.lineJoin = 'round';
    ctx.stroke();
  }
}

function line(ctx: Ctx, color: RGB, width: number, ...points: Pt[]): void {
  ctx.strokeStyle = rgb(color);
  ctx.lineWidth = width;
  ctx.beginPath();
  points.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
  ctx.stroke();
}

/** Degradado suave arriba→abajo, para dar volumen sin perder el aire de dibujo animado. */
function vGradient(ctx: Ctx, y0: number, y1: number, top: RGB, bottom: RGB): CanvasGradient {
  const gradient = ctx.createLinearGradient(0, y0, 0, y1);
  gradient.addColorStop(0, rgb(top));
  gradient.addColorStop(1, rgb(bottom));
  return gradient;
}

function hGradient(ctx: Ctx, x0: number, x1: number, light: RGB, dark: RGB): CanvasGradient {
  const gradient = ctx.createLinearGradient(x0, 0, x1, 0);
  gradient.addColorStop(0, rgb(light));
  gradient.addColorStop(1, rgb(dark));
  return gradient;
}

function rGradient(ctx: Ctx, x: number, y: number, r: number, light: RGB, dark: RGB): CanvasGradient {
  const gradient = ctx.createRadialGradient(x - r * 0.3, y - r * 0.35, r * 0.1, x, y, r);
  gradient.addColorStop(0, rgb(light));
  gradient.addColorStop(1, rgb(dark));
  return gradient;
}

/** Halo luminoso (mezcla aditiva) para ojos y hoja de la espada. */
function glow(ctx: Ctx, x: number, y: number, r: number, color: RGB, alpha: number): void {
  const gradient = ctx.createRadialGradient(x, y, 0, x, y, r);
  gradient.addColorStop(0, rgb(color, alpha));
  gradient.addColorStop(1, rgb(color, 0));
  ctx.save();
  ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

/** Trama de malla (cota de mallas) recortada al trazado actual. */
function mesh(ctx: Ctx, x0: number, y0: number, x1: number, y1: number, color: RGB): void {
  ctx.save();
  ctx.clip();
  ctx.strokeStyle = rgb(color, 0.75);
  ctx.lineWidth = 0.7;
  ctx.beginPath();
  for (let x = Math.floor(x0); x <= x1; x += 3) {
    ctx.moveTo(x, y0);
    ctx.lineTo(x, y1);
  }
  for (let y = Math.floor(y0); y <= y1; y += 3) {
    ctx.moveTo(x0, y);
    ctx.lineTo(x1, y);
  }
  ctx.stroke();
  ctx.restore();
}

/** Prepara el cuadro de 100×100 unidades. */
function frame(ctx: Ctx, cx: number, cy: number, size: number, draw: () => void): void {
  ctx.save();
  ctx.translate(cx, cy);
  const k = Math.max(8, size) / 100;
  ctx.scale(k, k);
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  draw();
  ctx.restore();
}

// ---------------------------------------------------------------------------
// Guerrero
// ---------------------------------------------------------------------------

export interface WarriorLook {
  /** Oscilación del paso, de -1 a 1 (0 si está parado). */
  phase: number;
  /** Mirada a los lados durante la introducción: -1, 0 o 1. */
  headTurn: number;
  showWeapons: boolean;
  swordPower: boolean;
  /** Reloj del juego en ms, para el vaivén del penacho. */
  now: number;
}

const ARMOR: RGB = [128, 128, 112];
const ARMOR_LIGHT: RGB = [158, 158, 140];
const ARMOR_DARK: RGB = [84, 84, 72];
const MAIL: RGB = [116, 114, 100];
const RED: RGB = [196, 52, 42];
const RED_DARK: RGB = [128, 28, 28];
const SKIN: RGB = [238, 164, 62];
const SKIN_DARK: RGB = [206, 128, 40];
const LEATHER: RGB = [142, 90, 52];
const LEATHER_DARK: RGB = [96, 58, 34];
const GOLD: RGB = [236, 178, 56];
const GOLD_DARK: RGB = [160, 104, 24];
const BLADE: RGB = [206, 210, 200];

export function drawWarrior(ctx: Ctx, cx: number, cy: number, size: number, look: WarriorLook): void {
  const { phase, headTurn, showWeapons, swordPower, now } = look;
  frame(ctx, cx, cy, size, () => {
    const sway = Math.sin(now * 0.004) * 1.4;
    const stride = phase * 4.5;

    // Sombra en el suelo
    ctx.fillStyle = 'rgba(0,0,0,0.38)';
    oval(ctx, 0, 47.5, 27, 6);
    ctx.fill();

    // Piernas: calzas de malla y botas con vuelta
    for (const side of [-1, 1] as const) {
      const lift = side * stride;
      const x = side * 8;
      const bottom = 40 + lift * 0.4;
      path(ctx, [[x - 5.5, 24], [x + 5.5, 24], [x + 5, bottom - 4], [x - 5, bottom - 4]]);
      fillStroke(ctx, MAIL);
      mesh(ctx, x - 6, 24, x + 6, bottom, ARMOR_DARK);
      // Bota
      ctx.beginPath();
      ctx.moveTo(x - 6.5, bottom - 6);
      ctx.lineTo(x + 6.5, bottom - 6);
      ctx.lineTo(x + 6, bottom + 1);
      ctx.quadraticCurveTo(x + 11, bottom + 1.5, x + 10.5, bottom + 6.5);
      ctx.lineTo(x - 10.5, bottom + 6.5);
      ctx.quadraticCurveTo(x - 11, bottom + 1.5, x - 6, bottom + 1);
      ctx.closePath();
      fillStroke(ctx, vGradient(ctx, bottom - 6, bottom + 6.5, LEATHER, LEATHER_DARK));
      // Vuelta de la bota
      path(ctx, [[x - 8, bottom - 10], [x + 8, bottom - 10], [x + 7, bottom - 3.5], [x - 7, bottom - 3.5]]);
      fillStroke(ctx, vGradient(ctx, bottom - 10, bottom - 3.5, shade(LEATHER, 1.2), LEATHER));
    }

    // Faldón rojo de la túnica
    path(ctx, [[-13, 12], [13, 12], [17, 28], [3, 30], [0, 25], [-3, 30], [-17, 28]]);
    fillStroke(ctx, vGradient(ctx, 12, 30, RED, RED_DARK));
    line(ctx, RED_DARK, 1, [0, 25], [0, 14]);

    // Coraza gris con bisel
    ctx.beginPath();
    ctx.moveTo(-15, -6);
    ctx.quadraticCurveTo(-17, 4, -13, 15);
    ctx.lineTo(13, 15);
    ctx.quadraticCurveTo(17, 4, 15, -6);
    ctx.quadraticCurveTo(0, -11, -15, -6);
    ctx.closePath();
    fillStroke(ctx, hGradient(ctx, -16, 16, ARMOR_LIGHT, ARMOR));
    ctx.beginPath();
    ctx.moveTo(-11, -3);
    ctx.quadraticCurveTo(-12, 5, -9, 12);
    ctx.lineTo(-1, 12);
    ctx.lineTo(-1, -4);
    ctx.closePath();
    ctx.fillStyle = rgb(ARMOR_LIGHT, 0.35);
    ctx.fill();
    line(ctx, ARMOR_DARK, 1.2, [0, -4], [0, 13]);
    // Cinturón con hebilla cuadrada
    path(ctx, [[-14, 11], [14, 11], [14, 16], [-14, 16]]);
    fillStroke(ctx, LEATHER, 1.8);
    path(ctx, [[-4, 10.2], [4, 10.2], [4, 16.8], [-4, 16.8]]);
    fillStroke(ctx, GOLD, 1.6);
    path(ctx, [[-1.8, 12], [1.8, 12], [1.8, 15], [-1.8, 15]]);
    fillStroke(ctx, LEATHER_DARK, 0.8);

    // Brazos: mangas de malla con hombrera redondeada
    for (const side of [-1, 1] as const) {
      const swing = -side * stride * 0.5;
      path(ctx, [[side * 14, -5], [side * 24, -2 + swing * 0.4], [side * 25, 10 + swing], [side * 19, 11 + swing], [side * 15, 3]]);
      fillStroke(ctx, MAIL);
      mesh(ctx, 14, -5, 26, 12, ARMOR_DARK);
      // Hombrera
      ctx.beginPath();
      ctx.moveTo(side * 12.5, -9);
      ctx.quadraticCurveTo(side * 23, -16, side * 26, -4);
      ctx.quadraticCurveTo(side * 21, -6, side * 13.5, -2);
      ctx.closePath();
      fillStroke(ctx, hGradient(ctx, 12, 26, ARMOR_LIGHT, ARMOR_DARK));
    }

    // Bufanda roja
    ctx.beginPath();
    ctx.moveTo(-12, -11);
    ctx.quadraticCurveTo(0, -4, 12, -11);
    ctx.lineTo(10, -5);
    ctx.quadraticCurveTo(0, 1, -10, -5);
    ctx.closePath();
    fillStroke(ctx, vGradient(ctx, -11, 1, RED, RED_DARK), 1.8);

    // Manos (naranja, como la cara)
    for (const side of [-1, 1] as const) {
      const swing = -side * stride * 0.5;
      oval(ctx, side * 23, 13 + swing, 5, 4.6);
      fillStroke(ctx, vGradient(ctx, 8, 18, SKIN, SKIN_DARK), 1.8);
    }

    // Escudo en forma de cometa, delante del hombro izquierdo
    if (showWeapons) {
      const sx = -28;
      const sy = 6 - stride * 0.6;
      ctx.beginPath();
      ctx.moveTo(sx - 15, sy - 14);
      ctx.quadraticCurveTo(sx, sy - 19, sx + 15, sy - 14);
      ctx.bezierCurveTo(sx + 17, sy + 6, sx + 9, sy + 18, sx, sy + 25);
      ctx.bezierCurveTo(sx - 9, sy + 18, sx - 17, sy + 6, sx - 15, sy - 14);
      ctx.closePath();
      fillStroke(ctx, hGradient(ctx, sx - 15, sx + 16, ARMOR_LIGHT, ARMOR_DARK), 2.2);
      // Bisel interior
      ctx.beginPath();
      ctx.moveTo(sx - 10.5, sy - 10.5);
      ctx.quadraticCurveTo(sx, sy - 14, sx + 10.5, sy - 10.5);
      ctx.bezierCurveTo(sx + 12, sy + 5, sx + 6, sy + 14, sx, sy + 19.5);
      ctx.bezierCurveTo(sx - 6, sy + 14, sx - 12, sy + 5, sx - 10.5, sy - 10.5);
      ctx.closePath();
      ctx.fillStyle = rgb(ARMOR, 1);
      ctx.fill();
      ctx.strokeStyle = rgb(ARMOR_DARK);
      ctx.lineWidth = 1.4;
      ctx.stroke();
      line(ctx, ARMOR_DARK, 1, [sx - 1, sy - 12], [sx - 1, sy + 17]);
    }

    // Espada recta de guarda dorada, delante del hombro derecho
    if (showWeapons) {
      const sx = 29;
      const handY = 12 + stride * 0.5;
      const tipY = handY - 54;
      if (swordPower) {
        glow(ctx, sx, (handY + tipY) / 2, 34, [190, 235, 255], 0.5);
        ctx.strokeStyle = 'rgba(190,230,255,0.85)';
        ctx.lineWidth = 1.3;
        for (let i = 0; i < 6; i++) {
          const y = tipY + 10 + i * 8.5;
          ctx.beginPath();
          ctx.moveTo(sx + 7, y);
          ctx.lineTo(sx + 12 + (i % 2) * 3, y - 2);
          ctx.moveTo(sx - 7, y);
          ctx.lineTo(sx - 12 - (i % 2) * 3, y - 2);
          ctx.stroke();
        }
      }
      // Hoja facetada
      path(ctx, [[sx - 3.8, handY - 3], [sx + 3.8, handY - 3], [sx + 3.4, tipY + 6], [sx, tipY], [sx - 3.4, tipY + 6]]);
      fillStroke(ctx, swordPower ? [222, 246, 255] : BLADE, 2);
      path(ctx, [[sx + 0.4, handY - 3], [sx + 3.8, handY - 3], [sx + 3.4, tipY + 6], [sx + 0.4, tipY + 1]]);
      ctx.fillStyle = rgb([120, 146, 160], 0.55);
      ctx.fill();
      line(ctx, [96, 104, 100], 0.9, [sx, handY - 5], [sx, tipY + 7]);
      // Guarda dorada curvada hacia arriba
      ctx.beginPath();
      ctx.moveTo(sx - 11, handY - 6.5);
      ctx.quadraticCurveTo(sx - 9, handY - 1, sx - 3, handY - 1.4);
      ctx.lineTo(sx + 3, handY - 1.4);
      ctx.quadraticCurveTo(sx + 9, handY - 1, sx + 11, handY - 6.5);
      ctx.quadraticCurveTo(sx + 6, handY - 4.2, sx, handY - 4.2);
      ctx.quadraticCurveTo(sx - 6, handY - 4.2, sx - 11, handY - 6.5);
      ctx.closePath();
      fillStroke(ctx, vGradient(ctx, handY - 7, handY - 1, GOLD, GOLD_DARK), 1.8);
      // Empuñadura y pomo
      path(ctx, [[sx - 2, handY - 1.4], [sx + 2, handY - 1.4], [sx + 2, handY + 8], [sx - 2, handY + 8]]);
      fillStroke(ctx, LEATHER, 1.6);
      oval(ctx, sx, handY + 10.5, 3.1, 3.1);
      fillStroke(ctx, rGradient(ctx, sx, handY + 10.5, 4, [255, 214, 110], GOLD_DARK), 1.6);
      // La mano empuña la espada, por delante de la empuñadura
      oval(ctx, sx, handY + 3.5, 4.8, 4.4);
      fillStroke(ctx, vGradient(ctx, handY - 1, handY + 8, SKIN, SKIN_DARK), 1.8);
      line(ctx, SKIN_DARK, 0.9, [sx - 3, handY + 2.2], [sx + 3, handY + 2.2]);
      line(ctx, SKIN_DARK, 0.9, [sx - 3, handY + 4.6], [sx + 3, handY + 4.6]);
    }

    // Cabeza grande, de dibujo animado: cara naranja y yelmo con ranuras
    const hx = headTurn * 3;
    const hy = -25;
    oval(ctx, hx, hy + 3, 15, 14.5);
    fillStroke(ctx, rGradient(ctx, hx, hy + 3, 18, [250, 190, 92], SKIN_DARK), 2);
    // Ojos grandes con pupila y brillo
    for (const side of [-1, 1] as const) {
      const ex = hx + side * 6.4 + headTurn * 1.2;
      oval(ctx, ex, hy + 2, 4.3, 5);
      fillStroke(ctx, [252, 246, 226], 1.5);
      oval(ctx, ex + headTurn * 1.3 + side * 0.3, hy + 2.6, 2.1, 2.5);
      ctx.fillStyle = rgb([30, 18, 14]);
      ctx.fill();
      oval(ctx, ex + headTurn * 1.3 - 0.6, hy + 1.8, 0.7, 0.7);
      ctx.fillStyle = 'rgba(255,255,255,0.95)';
      ctx.fill();
    }
    // Cejas
    line(ctx, OUTLINE, 1.4, [hx - 10.4, hy - 4.8], [hx - 3.4, hy - 3.8]);
    line(ctx, OUTLINE, 1.4, [hx + 10.4, hy - 4.8], [hx + 3.4, hy - 3.8]);
    // Nariz redonda y boca
    oval(ctx, hx, hy + 8, 3.3, 3);
    fillStroke(ctx, vGradient(ctx, hy + 5, hy + 11, [250, 182, 84], SKIN_DARK), 1.5);
    ctx.strokeStyle = rgb(OUTLINE);
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(hx - 4.4, hy + 13);
    ctx.quadraticCurveTo(hx, hy + 15.6, hx + 4.4, hy + 13);
    ctx.stroke();

    // Penacho rojo, curvado hacia atrás, con vaivén
    const plume = sway + phase * 3;
    ctx.beginPath();
    ctx.moveTo(hx + 2, hy - 15);
    ctx.bezierCurveTo(hx + 4, hy - 35, hx + 20 + plume, hy - 31, hx + 26 + plume * 1.5, hy - 13 + Math.abs(plume) * 0.6);
    ctx.bezierCurveTo(hx + 21 + plume, hy - 21, hx + 14, hy - 22, hx + 9, hy - 14);
    ctx.closePath();
    fillStroke(ctx, vGradient(ctx, hy - 34, hy - 12, [214, 68, 54], RED_DARK), 1.9);
    line(ctx, [236, 110, 88], 0.9, [hx + 4, hy - 17], [hx + 14 + plume, hy - 28], [hx + 22 + plume * 1.3, hy - 16]);
    line(ctx, RED_DARK, 0.9, [hx + 6, hy - 15], [hx + 17 + plume, hy - 22], [hx + 24 + plume * 1.4, hy - 13]);

    // Yelmo gris: cúpula con ranuras, ala frontal y remache en la sien
    ctx.beginPath();
    ctx.moveTo(hx - 16.5, hy + 1);
    ctx.bezierCurveTo(hx - 17, hy - 20, hx + 17, hy - 20, hx + 16.5, hy + 1);
    ctx.quadraticCurveTo(hx + 12, hy - 4, hx, hy - 4.5);
    ctx.quadraticCurveTo(hx - 12, hy - 4, hx - 16.5, hy + 1);
    ctx.closePath();
    fillStroke(ctx, hGradient(ctx, hx - 17, hx + 17, ARMOR_LIGHT, ARMOR_DARK), 2.2);
    // Ranuras de la cúpula
    ctx.strokeStyle = rgb(OUTLINE);
    ctx.lineWidth = 1.5;
    for (let i = -2; i <= 2; i++) {
      ctx.beginPath();
      ctx.moveTo(hx + i * 5, hy - 13 + Math.abs(i) * 1.2);
      ctx.lineTo(hx + i * 5 + i * 0.8, hy - 8 + Math.abs(i) * 0.7);
      ctx.stroke();
    }
    // Remates
    oval(ctx, hx + 0.5, hy - 17.5, 3.1, 2.7);
    fillStroke(ctx, vGradient(ctx, hy - 20, hy - 15, ARMOR_LIGHT, ARMOR_DARK), 1.6);
    for (const side of [-1, 1] as const) {
      oval(ctx, hx + side * 15, hy + 1.5, 2.5, 2.9);
      fillStroke(ctx, rGradient(ctx, hx + side * 15, hy + 1.5, 3, ARMOR_LIGHT, ARMOR_DARK), 1.5);
    }
  });
}

// ---------------------------------------------------------------------------
// Profundo
// ---------------------------------------------------------------------------

export interface DeepOneLook {
  /** Oscilación del paso, de -1 a 1 (0 si está quieto). */
  walkPhase: number;
  roaring: boolean;
  /** Milisegundos desde que empezó a rugir. */
  roarT: number;
  alerted: boolean;
  dead: boolean;
  now: number;
}

const GREEN: RGB = [96, 110, 58];
const GREEN_LIGHT: RGB = [128, 142, 76];
const GREEN_DARK: RGB = [58, 70, 36];
const BELLY: RGB = [150, 156, 92];
const EYE: RGB = [252, 164, 32];
const EYE_DARK: RGB = [214, 100, 14];
const TOOTH: RGB = [250, 226, 176];
const MAW: RGB = [90, 20, 24];
const TONGUE: RGB = [196, 58, 62];

export function drawDeepOne(ctx: Ctx, cx: number, cy: number, size: number, look: DeepOneLook): void {
  const { walkPhase, roaring, roarT, alerted, dead, now } = look;
  frame(ctx, cx, cy, size, () => {
    const breath = dead ? 0 : Math.sin(now * 0.003) * 1.3;
    const stride = walkPhase * 4;

    // Sombra
    ctx.fillStyle = 'rgba(0,0,0,0.4)';
    oval(ctx, 0, 47.5, 29, 6.2);
    ctx.fill();

    // Piernas cortas con pies palmeados
    for (const side of [-1, 1] as const) {
      const lift = side * stride;
      const x = side * 10;
      const fy = 41 + lift * 0.4;
      path(ctx, [[x - 6, 26], [x + 6, 26], [x + 5.5, fy], [x - 5.5, fy]]);
      fillStroke(ctx, hGradient(ctx, x - 6, x + 6, GREEN_LIGHT, GREEN_DARK));
      // Pie palmeado: tres dedos unidos por membrana
      ctx.beginPath();
      ctx.moveTo(x - 8, fy - 1);
      ctx.quadraticCurveTo(x - 12, fy + 6, x - 9, fy + 6.5);
      ctx.quadraticCurveTo(x - 6, fy + 3.5, x - 3.6, fy + 7);
      ctx.quadraticCurveTo(x, fy + 4, x + 3.6, fy + 7);
      ctx.quadraticCurveTo(x + 6, fy + 3.5, x + 9, fy + 6.5);
      ctx.quadraticCurveTo(x + 12, fy + 6, x + 8, fy - 1);
      ctx.closePath();
      fillStroke(ctx, vGradient(ctx, fy - 1, fy + 7, GREEN, GREEN_DARK), 1.8);
    }

    // Brazos largos y musculosos con manos palmeadas
    for (const side of [-1, 1] as const) {
      const sx = side * 17;
      const sy = 0 + breath;
      const ex = side * (roaring ? 33 : 29);
      const ey = roaring ? -12 - Math.abs(Math.sin(roarT * 0.02)) * 4 : 27 - side * stride * 0.5;
      const mx = side * 34;
      const my = roaring ? 8 : 10;
      ctx.strokeStyle = rgb(OUTLINE);
      ctx.lineWidth = 12.5;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.quadraticCurveTo(mx, my, ex, ey);
      ctx.stroke();
      ctx.strokeStyle = rgb(GREEN);
      ctx.lineWidth = 9;
      ctx.stroke();
      ctx.strokeStyle = rgb(GREEN_LIGHT, 0.55);
      ctx.lineWidth = 2.6;
      ctx.stroke();
      // Mano
      const dir = roaring ? -1 : 1;
      ctx.beginPath();
      ctx.moveTo(ex - 6.5, ey);
      ctx.quadraticCurveTo(ex - 9, ey + dir * 10, ex - 4.5, ey + dir * 11);
      ctx.quadraticCurveTo(ex - 2.5, ey + dir * 8, ex, ey + dir * 12);
      ctx.quadraticCurveTo(ex + 2.5, ey + dir * 8, ex + 4.5, ey + dir * 11);
      ctx.quadraticCurveTo(ex + 9, ey + dir * 10, ex + 6.5, ey);
      ctx.closePath();
      fillStroke(ctx, vGradient(ctx, ey, ey + dir * 11, GREEN_LIGHT, GREEN_DARK), 1.8);
      ctx.strokeStyle = rgb(GREEN_DARK, 0.8);
      ctx.lineWidth = 0.9;
      ctx.beginPath();
      ctx.moveTo(ex - 2.5, ey + dir * 2);
      ctx.lineTo(ex - 2.5, ey + dir * 8);
      ctx.moveTo(ex + 2.5, ey + dir * 2);
      ctx.lineTo(ex + 2.5, ey + dir * 8);
      ctx.stroke();
    }

    // Torso rechoncho con panza clara
    oval(ctx, 0, 10 + breath * 0.5, 19, 21);
    fillStroke(ctx, hGradient(ctx, -19, 19, GREEN_LIGHT, GREEN_DARK), 2.2);
    oval(ctx, 0, 14 + breath * 0.5, 11, 14.5);
    fillStroke(ctx, vGradient(ctx, -1, 28, BELLY, shade(BELLY, 0.7)), 1.6);
    ctx.strokeStyle = rgb(GREEN_DARK, 0.5);
    ctx.lineWidth = 0.9;
    for (let i = 0; i < 4; i++) {
      const y = 7 + i * 5.5 + breath * 0.5;
      ctx.beginPath();
      ctx.moveTo(-8, y);
      ctx.quadraticCurveTo(0, y + 2.6, 8, y);
      ctx.stroke();
    }
    // Manchas de la piel
    ctx.fillStyle = rgb(GREEN_DARK, 0.7);
    for (const [x, y, r] of [[-15, 4, 1.5], [-13, 15, 1.2], [14, 6, 1.6], [13, 17, 1.1], [-16, 22, 1.2], [16, 24, 1.3]] as const) {
      oval(ctx, x, y + breath * 0.5, r, r * 0.85);
      ctx.fill();
    }

    // Cabeza abultada
    const hy = -19 + breath;

    // Aletas de las sienes, como alas de murciélago
    for (const side of [-1, 1] as const) {
      ctx.beginPath();
      ctx.moveTo(side * 16, hy - 6);
      ctx.lineTo(side * 33, hy - 24);
      ctx.quadraticCurveTo(side * 31, hy - 10, side * 36, hy - 4);
      ctx.quadraticCurveTo(side * 27, hy - 4, side * 29, hy + 4);
      ctx.quadraticCurveTo(side * 22, hy + 1, side * 17, hy + 6);
      ctx.closePath();
      fillStroke(ctx, hGradient(ctx, side * 16, side * 36, GREEN, GREEN_DARK), 2);
      line(ctx, GREEN_DARK, 1, [side * 17, hy - 3], [side * 32, hy - 20]);
      line(ctx, GREEN_DARK, 1, [side * 18, hy], [side * 33, hy - 4]);
    }

    ctx.beginPath();
    ctx.moveTo(-20, hy + 4);
    ctx.bezierCurveTo(-23, hy - 22, 23, hy - 22, 20, hy + 4);
    ctx.bezierCurveTo(20, hy + 16, 10, hy + 21, 0, hy + 21);
    ctx.bezierCurveTo(-10, hy + 21, -20, hy + 16, -20, hy + 4);
    ctx.closePath();
    fillStroke(ctx, rGradient(ctx, 0, hy, 24, GREEN_LIGHT, GREEN_DARK), 2.4);
    ctx.fillStyle = rgb(GREEN_DARK, 0.65);
    for (const [x, y, r] of [[-9, -12, 1.5], [-3, -14, 1.1], [7, -13, 1.4], [13, -8, 1.1], [-14, -6, 1.1], [1, -9, 0.9]] as const) {
      oval(ctx, x, hy + y, r, r * 0.85);
      ctx.fill();
    }

    // Boca con colmillos y lengua
    const mouthY = hy + 9.5;
    const open = dead ? 3 : roaring ? 8 + Math.abs(Math.sin(roarT * 0.012)) * 4 : 5.5;
    ctx.beginPath();
    ctx.moveTo(-11.5, mouthY - 1);
    ctx.quadraticCurveTo(0, mouthY - 4.5, 11.5, mouthY - 1);
    ctx.quadraticCurveTo(10, mouthY + open + 3, 0, mouthY + open + 4.5);
    ctx.quadraticCurveTo(-10, mouthY + open + 3, -11.5, mouthY - 1);
    ctx.closePath();
    fillStroke(ctx, vGradient(ctx, mouthY - 4, mouthY + open + 4, MAW, [48, 8, 12]), 2);
    if (!dead) {
      oval(ctx, 0, mouthY + open + 0.5, 5.6, 2.8 + open * 0.15);
      ctx.fillStyle = rgb(TONGUE);
      ctx.fill();
    }
    for (const x of [-8, -4.6, -1.6, 1.6, 4.6, 8]) {
      const ty = mouthY - 3 + Math.abs(x) * 0.28;
      path(ctx, [[x - 1.5, ty], [x + 1.5, ty], [x, ty + 4.4]]);
      fillStroke(ctx, TOOTH, 0.9);
    }
    for (const x of [-6, -2.2, 2.2, 6]) {
      const by = mouthY + open + 2.2 - Math.abs(x) * 0.2;
      path(ctx, [[x - 1.3, by], [x + 1.3, by], [x, by - 3.6]]);
      fillStroke(ctx, TOOTH, 0.8);
    }

    // Fosas nasales y bultito
    oval(ctx, 0, hy + 4, 2.4, 1.8);
    fillStroke(ctx, GREEN_LIGHT, 1.2);
    ctx.fillStyle = rgb(OUTLINE);
    for (const side of [-1, 1] as const) {
      oval(ctx, side * 1.1, hy + 4.2, 0.6, 0.9);
      ctx.fill();
    }

    // Ojos naranjas con pupila vertical y cejas enfadadas
    for (const side of [-1, 1] as const) {
      const ex = side * 10.5;
      const ey = hy - 5.5;
      if (!dead) glow(ctx, ex, ey, 14, EYE, 0.35);
      oval(ctx, ex, ey, 7.2, 7.4);
      fillStroke(ctx, rGradient(ctx, ex, ey, 9, dead ? [170, 170, 140] : EYE, dead ? [110, 110, 90] : EYE_DARK), 2);
      if (dead) {
        line(ctx, OUTLINE, 1.5, [ex - 3, ey - 3], [ex + 3, ey + 3]);
        line(ctx, OUTLINE, 1.5, [ex + 3, ey - 3], [ex - 3, ey + 3]);
      } else {
        const jitter = roaring ? Math.sin(roarT * 0.015) * 1.3 : 0;
        oval(ctx, ex + jitter - side * 0.8, ey + 0.6, 1.8, 5.2);
        ctx.fillStyle = rgb([14, 8, 6]);
        ctx.fill();
        oval(ctx, ex - 2.4, ey - 2.6, 1.1, 1.1);
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        ctx.fill();
      }
      // Ceja pesada, inclinada hacia el centro
      ctx.beginPath();
      ctx.moveTo(side * 17.5, ey - 9.2);
      ctx.lineTo(side * 3.6, ey - 3.4);
      ctx.lineTo(side * 3.6, ey - 8);
      ctx.lineTo(side * 17.5, ey - 12.4);
      ctx.closePath();
      fillStroke(ctx, GREEN_DARK, 1.8);
    }

    // Indicador de alerta
    if (alerted && !dead) {
      const bob = Math.sin(now * 0.01) * 2;
      const y = hy - 34 + bob;
      path(ctx, [[-2.8, y - 12.5], [2.8, y - 12.5], [1.7, y], [-1.7, y]]);
      fillStroke(ctx, [255, 40, 30], 1.4);
      ctx.beginPath();
      ctx.arc(0, y + 4.6, 2.3, 0, Math.PI * 2);
      fillStroke(ctx, [255, 40, 30], 1.4);
    }
  });
}
