/**
 * Sprites vectoriales del guerrero y de los Profundos.
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

const OUTLINE: RGB = [14, 10, 12];

function shade(c: RGB, k: number): RGB {
  return [Math.min(255, c[0] * k), Math.min(255, c[1] * k), Math.min(255, c[2] * k)];
}

function path(ctx: Ctx, points: readonly Pt[], close = true): void {
  ctx.beginPath();
  points.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
  if (close) ctx.closePath();
}

function fillStroke(ctx: Ctx, fill: string | CanvasGradient | RGB, stroke: RGB = OUTLINE, width = 1.6): void {
  ctx.fillStyle = typeof fill === 'string' || !Array.isArray(fill) ? (fill as string | CanvasGradient) : rgb(fill as RGB);
  ctx.fill();
  if (width > 0) {
    ctx.strokeStyle = rgb(stroke);
    ctx.lineWidth = width;
    ctx.lineJoin = 'round';
    ctx.stroke();
  }
}

function hGradient(ctx: Ctx, x0: number, x1: number, stops: ReadonlyArray<readonly [number, RGB]>): CanvasGradient {
  const gradient = ctx.createLinearGradient(x0, 0, x1, 0);
  for (const [t, c] of stops) gradient.addColorStop(t, rgb(c));
  return gradient;
}

function vGradient(ctx: Ctx, y0: number, y1: number, stops: ReadonlyArray<readonly [number, RGB]>): CanvasGradient {
  const gradient = ctx.createLinearGradient(0, y0, 0, y1);
  for (const [t, c] of stops) gradient.addColorStop(t, rgb(c));
  return gradient;
}

function rGradient(ctx: Ctx, x: number, y: number, r: number, stops: ReadonlyArray<readonly [number, RGB, number?]>): CanvasGradient {
  const gradient = ctx.createRadialGradient(x - r * 0.3, y - r * 0.3, r * 0.1, x, y, r);
  for (const [t, c, a] of stops) gradient.addColorStop(t, rgb(c, a ?? 1));
  return gradient;
}

function oval(ctx: Ctx, cx: number, cy: number, rx: number, ry: number, rotation = 0): void {
  ctx.beginPath();
  ctx.ellipse(cx, cy, Math.max(0.01, rx), Math.max(0.01, ry), rotation, 0, Math.PI * 2);
}

/** Halo luminoso (mezcla aditiva) para ojos, hoja de la espada... */
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
  /** Reloj del juego en ms, para el vaivén de la capa y el penacho. */
  now: number;
}

const STEEL: RGB = [150, 158, 170];
const STEEL_DARK: RGB = [62, 68, 80];
const STEEL_LIGHT: RGB = [226, 232, 240];
const CLOTH: RGB = [158, 32, 30];
const CLOTH_DARK: RGB = [92, 16, 20];
const LEATHER: RGB = [96, 58, 34];
const GOLD: RGB = [222, 178, 70];
const SKIN: RGB = [226, 184, 150];

export function drawWarrior(ctx: Ctx, cx: number, cy: number, size: number, look: WarriorLook): void {
  const { phase, headTurn, showWeapons, swordPower, now } = look;
  frame(ctx, cx, cy, size, () => {
    const sway = Math.sin(now * 0.004) * 1.2;
    const stride = phase * 5;

    // Sombra en el suelo
    ctx.fillStyle = 'rgba(0,0,0,0.38)';
    oval(ctx, 0, 47, 28, 6.5);
    ctx.fill();

    // Capa roja detrás del cuerpo
    path(ctx, [[-17, -14], [17, -14], [26 + phase * 3, 38], [10, 43 + stride * 0.3], [0, 40], [-10, 43 - stride * 0.3], [-26 + phase * 3, 38]]);
    fillStroke(ctx, vGradient(ctx, -14, 43, [[0, CLOTH], [1, CLOTH_DARK]]));

    // Piernas: grebas y botas
    for (const side of [-1, 1] as const) {
      const lift = side * stride;
      const x = side * 8;
      const top = 19;
      const bottom = 41 + lift * 0.5;
      path(ctx, [[x - 6, top], [x + 6, top], [x + 5, bottom - 6], [x - 5, bottom - 6]]);
      fillStroke(ctx, hGradient(ctx, x - 6, x + 6, [[0, STEEL_DARK], [0.4, STEEL], [1, STEEL_DARK]]));
      // Rodillera
      oval(ctx, x, top + 9, 4.6, 3.4);
      fillStroke(ctx, rGradient(ctx, x, top + 9, 5, [[0, STEEL_LIGHT], [1, STEEL]]), OUTLINE, 1.2);
      // Bota
      path(ctx, [[x - 6, bottom - 6], [x + 6, bottom - 6], [x + 8, bottom + 3], [x - 8, bottom + 3]]);
      fillStroke(ctx, vGradient(ctx, bottom - 6, bottom + 3, [[0, LEATHER], [1, shade(LEATHER, 0.55)]]));
    }

    // Faldón de tela
    path(ctx, [[-14, 12], [14, 12], [18, 27], [0, 30], [-18, 27]]);
    fillStroke(ctx, vGradient(ctx, 12, 30, [[0, CLOTH], [1, CLOTH_DARK]]));

    // Peto de acero
    path(ctx, [[-17, -14], [17, -14], [14, 4], [12, 17], [-12, 17], [-14, 4]]);
    fillStroke(ctx, hGradient(ctx, -17, 17, [[0, STEEL_DARK], [0.28, STEEL], [0.5, STEEL_LIGHT], [0.75, STEEL], [1, STEEL_DARK]]));
    // Relieve del pecho y brillo
    ctx.strokeStyle = rgb(STEEL_DARK, 0.7);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, -12);
    ctx.lineTo(0, 15);
    ctx.moveTo(-9, -4);
    ctx.quadraticCurveTo(0, 2, 9, -4);
    ctx.stroke();
    // Cinturón con hebilla
    path(ctx, [[-13, 13], [13, 13], [13, 18], [-13, 18]]);
    fillStroke(ctx, LEATHER, OUTLINE, 1.2);
    path(ctx, [[-3.5, 12.5], [3.5, 12.5], [3.5, 18.5], [-3.5, 18.5]]);
    fillStroke(ctx, GOLD, OUTLINE, 1);

    // Brazo del escudo (izquierda) y del arma (derecha)
    for (const side of [-1, 1] as const) {
      const swing = -side * stride * 0.5;
      path(ctx, [[side * 17, -12], [side * 25, -8 + swing], [side * 24, 8 + swing], [side * 17, 6]]);
      fillStroke(ctx, hGradient(ctx, 17, 25, [[0, STEEL], [1, STEEL_DARK]]));
    }

    if (showWeapons) {
      // Espada
      const sx = 29;
      const handY = 11 + stride * 0.5;
      const tipY = handY - 52;
      if (swordPower) glow(ctx, sx, (handY + tipY) / 2, 38, [170, 225, 255], 0.55);
      const bladeColor: RGB = swordPower ? [226, 248, 255] : [212, 218, 226];
      path(ctx, [[sx - 3.2, handY - 3], [sx + 3.2, handY - 3], [sx + 2.6, tipY + 7], [sx, tipY], [sx - 2.6, tipY + 7]]);
      fillStroke(ctx, hGradient(ctx, sx - 3, sx + 3, [[0, shade(bladeColor, 0.7)], [0.5, bladeColor], [1, shade(bladeColor, 0.75)]]), OUTLINE, 1.3);
      ctx.strokeStyle = rgb([255, 255, 255], 0.7);
      ctx.lineWidth = 0.9;
      ctx.beginPath();
      ctx.moveTo(sx, handY - 5);
      ctx.lineTo(sx, tipY + 8);
      ctx.stroke();
      // Guarda y empuñadura
      path(ctx, [[sx - 8, handY - 3], [sx + 8, handY - 3], [sx + 7, handY], [sx - 7, handY]]);
      fillStroke(ctx, GOLD, OUTLINE, 1.2);
      path(ctx, [[sx - 2.2, handY], [sx + 2.2, handY], [sx + 2.2, handY + 9], [sx - 2.2, handY + 9]]);
      fillStroke(ctx, LEATHER, OUTLINE, 1.1);
      oval(ctx, sx, handY + 11, 3, 3);
      fillStroke(ctx, GOLD, OUTLINE, 1);
    }

    // Hombreras
    for (const side of [-1, 1] as const) {
      oval(ctx, side * 19, -12, 9, 7.5);
      fillStroke(ctx, rGradient(ctx, side * 19, -12, 10, [[0, STEEL_LIGHT], [0.6, STEEL], [1, STEEL_DARK]]), OUTLINE, 1.5);
      ctx.strokeStyle = rgb(GOLD, 0.8);
      ctx.lineWidth = 1;
      oval(ctx, side * 19, -12, 6.2, 4.8);
      ctx.stroke();
    }

    // Escudo delante del hombro
    if (showWeapons) {
      // Escudo redondo
      const shx = -29;
      const shy = 4 - stride * 0.6;
      oval(ctx, shx, shy, 16, 17);
      fillStroke(ctx, rGradient(ctx, shx, shy, 18, [[0, [120, 130, 96]], [0.7, [72, 82, 62]], [1, [40, 46, 38]]]), OUTLINE, 2);
      oval(ctx, shx, shy, 13, 14);
      ctx.strokeStyle = rgb(GOLD, 0.9);
      ctx.lineWidth = 1.8;
      ctx.stroke();
      // Cruz y ombligo
      ctx.strokeStyle = rgb(STEEL_LIGHT, 0.55);
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(shx, shy - 12);
      ctx.lineTo(shx, shy + 12);
      ctx.moveTo(shx - 11, shy);
      ctx.lineTo(shx + 11, shy);
      ctx.stroke();
      oval(ctx, shx, shy, 4.8, 4.8);
      fillStroke(ctx, rGradient(ctx, shx, shy, 6, [[0, STEEL_LIGHT], [1, STEEL_DARK]]), OUTLINE, 1.2);
    }

    // Manoplas
    for (const side of [-1, 1] as const) {
      const swing = -side * stride * 0.5;
      oval(ctx, side * 22, 9 + swing, 4.6, 4.2);
      fillStroke(ctx, STEEL, OUTLINE, 1.2);
    }

    // Cabeza: cuello, rostro y yelmo
    const hx = headTurn * 3;
    const hy = -29;
    path(ctx, [[-5, -19], [5, -19], [6, -13], [-6, -13]]);
    fillStroke(ctx, shade(STEEL_DARK, 1.1), OUTLINE, 1.2);

    // Penacho rojo (detrás del yelmo), con vaivén
    const plumeSway = sway + phase * 4;
    ctx.beginPath();
    ctx.moveTo(hx - 3, hy - 14);
    ctx.bezierCurveTo(hx - 6, hy - 34, hx + 16 + plumeSway, hy - 34, hx + 22 + plumeSway * 1.6, hy - 6 + Math.abs(plumeSway));
    ctx.bezierCurveTo(hx + 14 + plumeSway, hy - 14, hx + 8, hy - 12, hx + 3, hy - 12);
    ctx.closePath();
    fillStroke(ctx, vGradient(ctx, hy - 34, hy - 6, [[0, [236, 86, 40]], [1, [138, 18, 20]]]), OUTLINE, 1.5);
    ctx.strokeStyle = rgb([255, 150, 90], 0.6);
    ctx.lineWidth = 0.9;
    ctx.beginPath();
    ctx.moveTo(hx, hy - 17);
    ctx.quadraticCurveTo(hx + 10 + plumeSway, hy - 28, hx + 18 + plumeSway * 1.4, hy - 8);
    ctx.stroke();

    // Rostro
    oval(ctx, hx, hy + 2, 9, 10);
    fillStroke(ctx, vGradient(ctx, hy - 8, hy + 12, [[0, SKIN], [1, shade(SKIN, 0.8)]]), OUTLINE, 1.3);

    // Yelmo (cúpula) con nasal y ceja
    ctx.beginPath();
    ctx.moveTo(hx - 11.5, hy + 1);
    ctx.bezierCurveTo(hx - 12, hy - 20, hx + 12, hy - 20, hx + 11.5, hy + 1);
    ctx.lineTo(hx + 7.5, hy - 3);
    ctx.lineTo(hx - 7.5, hy - 3);
    ctx.closePath();
    fillStroke(ctx, hGradient(ctx, hx - 12, hx + 12, [[0, STEEL_DARK], [0.35, STEEL_LIGHT], [0.7, STEEL], [1, STEEL_DARK]]), OUTLINE, 1.6);
    // Banda frontal y remache
    ctx.strokeStyle = rgb(GOLD, 0.9);
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(hx - 11, hy - 3);
    ctx.lineTo(hx + 11, hy - 3);
    ctx.stroke();
    // Nasal
    path(ctx, [[hx - 1.6, hy - 3], [hx + 1.6, hy - 3], [hx + 1.6, hy + 7], [hx - 1.6, hy + 7]]);
    fillStroke(ctx, STEEL, OUTLINE, 1);
    // Ojos y ceño
    ctx.fillStyle = rgb([24, 18, 18]);
    for (const side of [-1, 1] as const) {
      oval(ctx, hx + side * 4.6 + headTurn * 0.8, hy + 1.2, 1.5, 1.8);
      ctx.fill();
    }
    ctx.strokeStyle = rgb([70, 40, 30]);
    ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.moveTo(hx - 7, hy - 1.2);
    ctx.lineTo(hx - 2.8, hy + 0.2);
    ctx.moveTo(hx + 7, hy - 1.2);
    ctx.lineTo(hx + 2.8, hy + 0.2);
    ctx.stroke();
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

const SKIN_BACK: RGB = [14, 62, 66];
const SKIN_MID: RGB = [34, 112, 100];
const SKIN_LIGHT: RGB = [86, 160, 128];
const BELLY: RGB = [150, 190, 146];
const FIN: RGB = [92, 52, 110];
const FIN_LIGHT: RGB = [168, 96, 170];
const EYE: RGB = [255, 232, 70];
const EYE_RIM: RGB = [232, 120, 24];
const TOOTH: RGB = [238, 232, 204];
const MAW: RGB = [74, 10, 22];

export function drawDeepOne(ctx: Ctx, cx: number, cy: number, size: number, look: DeepOneLook): void {
  const { walkPhase, roaring, roarT, alerted, dead, now } = look;
  frame(ctx, cx, cy, size, () => {
    const breath = dead ? 0 : Math.sin(now * 0.003) * 1.4;
    const stride = walkPhase * 4.5;
    const slime = dead ? 0 : (Math.sin(now * 0.005) + 1) / 2;

    // Sombra y charco de baba
    ctx.fillStyle = 'rgba(0,0,0,0.4)';
    oval(ctx, 0, 47, 30, 6.5);
    ctx.fill();
    ctx.fillStyle = 'rgba(70,170,130,0.16)';
    oval(ctx, 0, 47, 24, 4.5);
    ctx.fill();

    // Espinas de la espalda, a ambos lados del torso
    for (const side of [-1, 1] as const) {
      for (let i = 0; i < 4; i++) {
        const y = -6 + i * 10 + breath;
        const x = side * (17 - i * 0.6);
        path(ctx, [[x, y - 3], [x + side * 9, y + 4], [x, y + 5]]);
        fillStroke(ctx, vGradient(ctx, y - 3, y + 5, [[0, FIN_LIGHT], [1, FIN]]), OUTLINE, 1.1);
      }
    }

    // Piernas arqueadas con pies palmeados
    for (const side of [-1, 1] as const) {
      const lift = side * stride;
      const x = side * 11;
      ctx.beginPath();
      ctx.moveTo(x - 6, 20);
      ctx.quadraticCurveTo(x + side * 7, 30 + lift * 0.3, x + side * 3, 40 + lift * 0.4);
      ctx.lineTo(x - side * 4, 40 + lift * 0.4);
      ctx.quadraticCurveTo(x - side * 1, 30, x + 6, 22);
      ctx.closePath();
      fillStroke(ctx, hGradient(ctx, x - 8, x + 8, [[0, SKIN_BACK], [0.5, SKIN_MID], [1, SKIN_BACK]]));
      // Pie palmeado de tres dedos
      const fy = 40 + lift * 0.4;
      const fx = x + side * 3;
      path(ctx, [[fx - 7, fy], [fx - 9, fy + 7], [fx - 3, fy + 5], [fx, fy + 8], [fx + 3, fy + 5], [fx + 9, fy + 7], [fx + 7, fy]]);
      fillStroke(ctx, vGradient(ctx, fy, fy + 8, [[0, SKIN_MID], [1, SKIN_BACK]]), OUTLINE, 1.2);
      ctx.strokeStyle = rgb(FIN, 0.7);
      ctx.lineWidth = 0.8;
      ctx.beginPath();
      ctx.moveTo(fx - 3, fy + 1);
      ctx.lineTo(fx - 3, fy + 5);
      ctx.moveTo(fx + 3, fy + 1);
      ctx.lineTo(fx + 3, fy + 5);
      ctx.stroke();
    }

    // Brazos largos que casi arrastran (alzados al rugir)
    for (const side of [-1, 1] as const) {
      const raise = roaring ? 1 + Math.sin(roarT * 0.02) * 0.15 : 0;
      const sx = side * 16;
      const sy = -2 + breath;
      const ex = side * (roaring ? 33 : 27);
      const ey = roaring ? -20 - raise * 6 : 26 - side * stride * 0.5;
      const mx = side * (roaring ? 29 : 29);
      const my = roaring ? -2 : 8;
      // Brazo
      ctx.strokeStyle = rgb(OUTLINE);
      ctx.lineWidth = 9.5;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.quadraticCurveTo(mx, my, ex, ey);
      ctx.stroke();
      ctx.strokeStyle = rgb(SKIN_MID);
      ctx.lineWidth = 7;
      ctx.stroke();
      ctx.strokeStyle = rgb(SKIN_LIGHT, 0.45);
      ctx.lineWidth = 2;
      ctx.stroke();
      // Mano con membrana y garras
      const dir = roaring ? -1 : 1;
      for (let k = -1; k <= 1; k++) {
        const tx = ex + k * 5 + side * 1.5;
        const ty = ey + dir * 9 + Math.abs(k) * -dir * 1.5;
        path(ctx, [[ex + k * 2.2 - 1.6, ey], [tx, ty], [ex + k * 2.2 + 1.6, ey]]);
        fillStroke(ctx, rgb(TOOTH), OUTLINE, 0.9);
      }
      oval(ctx, ex, ey, 5.6, 4.6);
      fillStroke(ctx, rGradient(ctx, ex, ey, 6, [[0, SKIN_LIGHT], [1, SKIN_BACK]]), OUTLINE, 1.2);
    }

    // Torso encorvado: espalda oscura, vientre claro con placas
    oval(ctx, 0, 6 + breath * 0.5, 18, 24);
    fillStroke(ctx, hGradient(ctx, -18, 18, [[0, SKIN_BACK], [0.35, SKIN_MID], [0.5, SKIN_LIGHT], [0.7, SKIN_MID], [1, SKIN_BACK]]));
    oval(ctx, 0, 10 + breath * 0.5, 9.5, 17);
    fillStroke(ctx, vGradient(ctx, -7, 27, [[0, BELLY], [1, shade(BELLY, 0.62)]]), OUTLINE, 1.1);
    ctx.strokeStyle = rgb([60, 100, 70], 0.55);
    ctx.lineWidth = 0.9;
    for (let i = 0; i < 5; i++) {
      const y = -1 + i * 6 + breath * 0.5;
      ctx.beginPath();
      ctx.moveTo(-8, y);
      ctx.quadraticCurveTo(0, y + 3, 8, y);
      ctx.stroke();
    }
    // Escamas sueltas
    ctx.strokeStyle = rgb(SKIN_BACK, 0.6);
    for (const [x, y] of [[-13, 2], [-11, 14], [-14, 22], [13, 4], [12, 16], [14, 22]] as const) {
      ctx.beginPath();
      ctx.arc(x, y + breath * 0.5, 2.4, 0.15 * Math.PI, 0.85 * Math.PI);
      ctx.stroke();
    }
    // Branquias del costado
    ctx.strokeStyle = rgb([8, 34, 38], 0.9);
    ctx.lineWidth = 1.2;
    for (const side of [-1, 1] as const) {
      for (let i = 0; i < 3; i++) {
        const y = -2 + i * 4 + breath * 0.5;
        ctx.beginPath();
        ctx.moveTo(side * 14, y);
        ctx.quadraticCurveTo(side * 11.5, y + 1.5, side * 12.5, y + 3.2);
        ctx.stroke();
      }
    }

    // Cabeza de pez-rana, ancha y baja
    const hy = -27 + breath;

    // Cresta dorsal: abanico de espinas con membrana
    const spikes = [-19, -13, -7, -1, 5, 11, 17];
    ctx.beginPath();
    ctx.moveTo(-18, hy - 3);
    spikes.forEach((x, i) => {
      const h = 17 - Math.abs(i - 3) * 2.8 + Math.sin(now * 0.004 + i) * (dead ? 0 : 0.8);
      ctx.lineTo(x * 0.92, hy - 7 - h);
      ctx.lineTo(x * 0.92 + 3.1, hy - 7);
    });
    ctx.lineTo(18, hy - 3);
    ctx.closePath();
    fillStroke(ctx, vGradient(ctx, hy - 30, hy - 4, [[0, FIN_LIGHT], [0.5, FIN], [1, shade(FIN, 0.6)]]), OUTLINE, 1.3);

    // Aletas laterales (orejas)
    for (const side of [-1, 1] as const) {
      path(ctx, [[side * 15, hy - 5], [side * 28, hy - 12], [side * 24, hy - 1], [side * 29, hy + 5], [side * 15, hy + 6]]);
      fillStroke(ctx, hGradient(ctx, 15, 29, [[0, SKIN_MID], [1, FIN_LIGHT]]), OUTLINE, 1.2);
    }

    // Cráneo
    ctx.beginPath();
    ctx.moveTo(-19, hy + 2);
    ctx.bezierCurveTo(-21, hy - 16, 21, hy - 16, 19, hy + 2);
    ctx.bezierCurveTo(19, hy + 14, 10, hy + 18, 0, hy + 18);
    ctx.bezierCurveTo(-10, hy + 18, -19, hy + 14, -19, hy + 2);
    ctx.closePath();
    fillStroke(ctx, hGradient(ctx, -20, 20, [[0, SKIN_BACK], [0.3, SKIN_MID], [0.5, SKIN_LIGHT], [0.7, SKIN_MID], [1, SKIN_BACK]]), OUTLINE, 1.7);
    // Manchas de la piel
    ctx.fillStyle = rgb(SKIN_BACK, 0.55);
    for (const [x, y, r] of [[-12, -6, 1.6], [-7, -9, 1.1], [11, -7, 1.5], [7, -10, 1], [0, -11, 1.2]] as const) {
      oval(ctx, x, hy + y, r, r * 0.8);
      ctx.fill();
    }

    // Boca ancha con dientes
    const mouthY = hy + 8;
    if (roaring) {
      const open = 7 + Math.abs(Math.sin(roarT * 0.012)) * 4;
      ctx.beginPath();
      ctx.moveTo(-14, mouthY - 1);
      ctx.quadraticCurveTo(0, mouthY - 4, 14, mouthY - 1);
      ctx.quadraticCurveTo(12, mouthY + open + 4, 0, mouthY + open + 5);
      ctx.quadraticCurveTo(-12, mouthY + open + 4, -14, mouthY - 1);
      ctx.closePath();
      fillStroke(ctx, vGradient(ctx, mouthY - 4, mouthY + open + 5, [[0, MAW], [1, [24, 2, 8]]]), OUTLINE, 1.3);
      ctx.fillStyle = rgb([186, 54, 70]);
      oval(ctx, 0, mouthY + open, 6, 2.6);
      ctx.fill();
      for (let i = -3; i <= 3; i++) {
        const x = i * 3.6;
        path(ctx, [[x - 1.5, mouthY - 2.4 + Math.abs(i) * 0.25], [x + 1.5, mouthY - 2.4 + Math.abs(i) * 0.25], [x, mouthY + 3.4]]);
        fillStroke(ctx, rgb(TOOTH), OUTLINE, 0.6);
        path(ctx, [[x - 1.3, mouthY + open + 3.2], [x + 1.3, mouthY + open + 3.2], [x, mouthY + open - 1.6]]);
        fillStroke(ctx, rgb(TOOTH), OUTLINE, 0.6);
      }
    } else {
      ctx.strokeStyle = rgb(MAW);
      ctx.lineWidth = 2.6;
      ctx.beginPath();
      ctx.moveTo(-14, mouthY - 1);
      ctx.quadraticCurveTo(0, mouthY + 5, 14, mouthY - 1);
      ctx.stroke();
      // Colmillos asomando
      for (const x of [-9, -5, -1.5, 1.5, 5, 9]) {
        const y = mouthY + 2.2 - Math.abs(x) * 0.2 + (Math.abs(x) < 2 ? 1.4 : 0);
        path(ctx, [[x - 1.3, y], [x + 1.3, y], [x, y + 3.2]]);
        fillStroke(ctx, rgb(TOOTH), OUTLINE, 0.6);
      }
    }
    // Fosas nasales
    ctx.fillStyle = rgb([6, 28, 30]);
    for (const side of [-1, 1] as const) {
      oval(ctx, side * 2.6, hy + 3.4, 0.9, 1.4);
      ctx.fill();
    }

    // Barbillas con baba
    ctx.strokeStyle = rgb(SKIN_MID);
    ctx.lineWidth = 1.8;
    for (const side of [-1, 1] as const) {
      ctx.beginPath();
      ctx.moveTo(side * 6, hy + 16);
      ctx.quadraticCurveTo(side * 9, hy + 22, side * 6 + Math.sin(now * 0.004 + side) * 2, hy + 26);
      ctx.stroke();
    }
    if (!dead) {
      ctx.fillStyle = 'rgba(140,230,190,0.5)';
      oval(ctx, -3, hy + 20 + slime * 6, 1.3, 2 + slime);
      ctx.fill();
    }

    // Ojos saltones
    for (const side of [-1, 1] as const) {
      const ex = side * 11.5;
      const ey = hy - 4;
      if (!dead) glow(ctx, ex, ey, 14, EYE, 0.45);
      oval(ctx, ex, ey, 7.2, 7.2);
      fillStroke(ctx, rGradient(ctx, ex, ey, 8, [[0, dead ? [150, 150, 130] : EYE], [0.75, dead ? [110, 110, 96] : [230, 190, 40]], [1, EYE_RIM]]), OUTLINE, 1.4);
      if (dead) {
        ctx.strokeStyle = rgb(OUTLINE);
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.moveTo(ex - 3, ey - 3);
        ctx.lineTo(ex + 3, ey + 3);
        ctx.moveTo(ex + 3, ey - 3);
        ctx.lineTo(ex - 3, ey + 3);
        ctx.stroke();
      } else {
        // Pupila vertical; tiembla al rugir
        const jitter = roaring ? Math.sin(roarT * 0.015) * 1.4 : 0;
        oval(ctx, ex + jitter, ey, 1.8, roaring ? 5.8 : 5.2);
        ctx.fillStyle = rgb([6, 4, 4]);
        ctx.fill();
        ctx.fillStyle = 'rgba(255,255,255,0.85)';
        oval(ctx, ex - 2.2, ey - 2.6, 1.2, 1.2);
        ctx.fill();
      }
      // Párpado pesado
      ctx.strokeStyle = rgb(SKIN_BACK);
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      ctx.arc(ex, ey, 7.4, Math.PI * 1.08, Math.PI * 1.92);
      ctx.stroke();
    }

    // Indicador de alerta
    if (alerted && !dead) {
      const bob = Math.sin(now * 0.01) * 2;
      const y = hy - 42 + bob;
      ctx.fillStyle = rgb([255, 40, 30]);
      ctx.strokeStyle = rgb(OUTLINE);
      ctx.lineWidth = 1.2;
      path(ctx, [[-2.6, y - 12], [2.6, y - 12], [1.6, y], [-1.6, y]]);
      ctx.fill();
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(0, y + 4.5, 2.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }
  });
}
