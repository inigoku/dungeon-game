/**
 * Bárbaro: luchador "chibi" con capucha, melena revuelta, ceño fruncido de dientes apretados,
 * traje ajustado que marca los músculos, brazaletes, cinturón con hebilla en X y dos dagas curvas.
 *
 * Mismo esqueleto articulado que el guerrero (cinemática inversa), visto de frente, de
 * espaldas o de perfil. Se dibuja en un cuadro de 100×100 unidades centrado en (0, 0).
 */
import type { Ctx, RGB } from './gfx';
import { rgb } from './gfx';
import { capsule, ik, joint } from './rig';
import { fillStroke, frame, glow, hGradient, line, OUTLINE, oval, path, rGradient, shade, vGradient, type Pt } from './sprites';
import type { WarriorLook } from './warrior';

// Paleta: piel curtida, melena negra con reflejos azulados, cuero castaño y acero
const SKIN: RGB = [226, 168, 122];
const SKIN_LIGHT: RGB = [246, 198, 154];
const SKIN_DARK: RGB = [176, 118, 82];
const MANE: RGB = [30, 28, 40];
const MANE_LIGHT: RGB = [88, 96, 130];
const MANE_DARK: RGB = [10, 9, 14];
const LEATHER: RGB = [124, 80, 46];
const LEATHER_DARK: RGB = [78, 48, 28];
const CLOTH: RGB = [150, 104, 62];
const CLOTH_DARK: RGB = [96, 62, 36];
const STEEL: RGB = [158, 164, 176];
const STEEL_DARK: RGB = [76, 82, 96];
const GOLD: RGB = [236, 178, 56];
const GOLD_DARK: RGB = [160, 104, 24];
const HAIR: RGB = MANE;
const HAIR_LIGHT: RGB = [70, 76, 104];
const BLADE: RGB = [212, 216, 208];

/** Cabeza enorme, hundida entre los hombros, como en la figura. */
const HEAD_K = 1.38;
const GROUND = 44;
const THIGH = 10;
const SHIN = 9.6;
const UPPER_ARM = 10.5;
const FOREARM = 9.6;

// ---------------------------------------------------------------------------
// Dagas, bolsas y hebilla
// ---------------------------------------------------------------------------

/** Daga curva con la mano en (0, 0) y la hoja hacia arriba; `curve` (-1/1) curva la punta hacia ese lado. */
function dagger(ctx: Ctx, x: number, y: number, tilt: number, curve: number, power: boolean, now: number): void {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(tilt);
  const c = curve;
  const tip: Pt = [c * 8, -37];
  if (power) {
    glow(ctx, c * 3, -18, 22, [190, 235, 255], 0.5 + Math.sin(now * 0.01) * 0.08);
    ctx.strokeStyle = 'rgba(190,230,255,0.85)';
    ctx.lineWidth = 1.1;
    for (let i = 0; i < 4; i++) {
      const yy = -32 + i * 8;
      ctx.beginPath();
      ctx.moveTo(6, yy);
      ctx.lineTo(10 + (i % 2) * 2.6, yy - 1.6);
      ctx.moveTo(-6, yy);
      ctx.lineTo(-10 - (i % 2) * 2.6, yy - 1.6);
      ctx.stroke();
    }
  }
  // Hoja curva de filo dentado
  ctx.beginPath();
  ctx.moveTo(-3, -4);
  ctx.quadraticCurveTo(c * 1 - 3.6, -22, tip[0], tip[1]);
  ctx.quadraticCurveTo(c * 4.6 + 4.4, -20, 3, -4);
  ctx.closePath();
  fillStroke(ctx, power ? [224, 247, 255] : BLADE, 1.8);
  // Brillo de la hoja y dientes de sierra en el lomo
  ctx.strokeStyle = rgb([255, 255, 255], 0.7);
  ctx.lineWidth = 0.8;
  ctx.beginPath();
  ctx.moveTo(c * -0.4, -6);
  ctx.quadraticCurveTo(c * 1.8, -20, c * 6.2, -34);
  ctx.stroke();
  ctx.fillStyle = rgb(OUTLINE);
  for (let i = 0; i < 5; i++) {
    const t = 0.18 + i * 0.15;
    const px = c * (4.4 + 3.4 * t) + (1 - t) * (c > 0 ? 1 : -1) * 0.2;
    const py = -4 - 33 * t;
    ctx.beginPath();
    ctx.moveTo(px - c * 0.4, py);
    ctx.lineTo(px + c * 2.4, py - 1.4);
    ctx.lineTo(px - c * 0.4, py - 3);
    ctx.fill();
  }
  // Guarda pequeña, empuñadura de cuero con vendas y anillo en el pomo
  path(ctx, [[-5.4, -4.6], [5.4, -4.6], [4.8, -2], [-4.8, -2]]);
  fillStroke(ctx, vGradient(ctx, -5, -2, STEEL, STEEL_DARK), 1.5);
  path(ctx, [[-2.2, -2], [2.2, -2], [2.2, 7], [-2.2, 7]]);
  fillStroke(ctx, LEATHER, 1.4);
  line(ctx, LEATHER_DARK, 0.8, [-2.2, 0.4], [2.2, 1.4]);
  line(ctx, LEATHER_DARK, 0.8, [-2.2, 2.8], [2.2, 3.8]);
  line(ctx, LEATHER_DARK, 0.8, [-2.2, 5.2], [2.2, 6.2]);
  oval(ctx, 0, 8.2, 2.7, 2.2);
  fillStroke(ctx, vGradient(ctx, 6, 10, STEEL, STEEL_DARK), 1.4);
  ctx.restore();
}

/** Bolsa de cuero con solapa y hebilla. */
function pouch(ctx: Ctx, x: number, y: number, w: number, h: number): void {
  path(ctx, [[x - w / 2, y], [x + w / 2, y], [x + w / 2 + 0.6, y + h], [x - w / 2 - 0.6, y + h]]);
  fillStroke(ctx, vGradient(ctx, y, y + h, shade(LEATHER, 1.2), LEATHER_DARK), 1.3);
  path(ctx, [[x - w / 2, y], [x + w / 2, y], [x + w / 2 - 0.4, y + h * 0.4], [x, y + h * 0.55], [x - w / 2 + 0.4, y + h * 0.4]]);
  fillStroke(ctx, shade(LEATHER, 0.95), 1);
  oval(ctx, x, y + h * 0.5, 0.9, 0.9);
  ctx.fillStyle = rgb(GOLD);
  ctx.fill();
}

/** Hebilla del cinturón con una X. */
function xBuckle(ctx: Ctx, x: number, y: number, r: number): void {
  oval(ctx, x, y, r, r);
  fillStroke(ctx, rGradient(ctx, x, y, r * 1.4, [255, 214, 110], GOLD_DARK), 1.4);
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = r * 0.34;
  ctx.lineCap = 'butt';
  ctx.beginPath();
  ctx.moveTo(x - r * 0.55, y - r * 0.55);
  ctx.lineTo(x + r * 0.55, y + r * 0.55);
  ctx.moveTo(x + r * 0.55, y - r * 0.55);
  ctx.lineTo(x - r * 0.55, y + r * 0.55);
  ctx.stroke();
  ctx.lineCap = 'round';
}

/** Banda de cuero que rodea un miembro en el punto `t` entre `a` y `b` (los cintos del bárbaro). */
function strap(ctx: Ctx, a: Pt, b: Pt, t: number, width: number): void {
  const px = a[0] + (b[0] - a[0]) * t;
  const py = a[1] + (b[1] - a[1]) * t;
  const nx = -(b[1] - a[1]);
  const ny = b[0] - a[0];
  const n = Math.hypot(nx, ny) || 1;
  const hw = width / 2 + 0.5;
  ctx.lineCap = 'round';
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = 3.8;
  ctx.beginPath();
  ctx.moveTo(px - (nx / n) * hw, py - (ny / n) * hw);
  ctx.lineTo(px + (nx / n) * hw, py + (ny / n) * hw);
  ctx.stroke();
  ctx.strokeStyle = rgb(LEATHER);
  ctx.lineWidth = 2.3;
  ctx.stroke();
  oval(ctx, px, py, 0.8, 0.8);
  ctx.fillStyle = rgb(GOLD);
  ctx.fill();
}

// ---------------------------------------------------------------------------
// Melena (coordenadas locales: origen en el centro de la cara)
// ---------------------------------------------------------------------------

/** Dibuja una melena como polígono de mechones con degradado y reflejos azulados. */
function maneShape(ctx: Ctx, points: ReadonlyArray<Pt>, top: number, bottom: number, strands: ReadonlyArray<readonly [number, number, number, number, number, number]>): void {
  path(ctx, points);
  fillStroke(ctx, vGradient(ctx, top, bottom, MANE_LIGHT, MANE_DARK), 1.9);
  ctx.strokeStyle = rgb(HAIR_LIGHT, 0.75);
  ctx.lineWidth = 0.9;
  for (const [x0, y0, cx1, cy1, x1, y1] of strands) {
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.quadraticCurveTo(cx1, cy1, x1, y1);
    ctx.stroke();
  }
}

/** Melena de frente, por detrás de la cara: enorme y revuelta, cae sobre los hombros. */
function maneFront(ctx: Ctx): void {
  ctx.save();
  ctx.scale(0.8, 0.82);
  ctx.translate(0, -2);
  maneShape(
    ctx,
    [
      [-8, -21], [-13, -19.4], [-17, -13.6], [-19.4, -6], [-22.4, -1], [-20.4, 5], [-23.4, 11], [-20.6, 16], [-23, 22.4], [-17.6, 19.4], [-15.4, 24], [-12, 17.6],
      [-9, 20.4], [-6, 15], [-3, 19.6], [0, 15.4], [3, 19.6], [6, 15], [9, 20.4], [12, 17.6], [15.4, 24], [17.6, 19.4], [23, 22.4], [20.6, 16], [23.4, 11],
      [20.4, 5], [22.4, -1], [19.4, -6], [17, -13.6], [13, -19.4], [8, -21], [4, -23.6], [0, -21.4], [-4, -23.6],
    ],
    -24,
    24,
    [
      [-4, -20, -10, -14, -17, -2], [4, -20, 10, -14, 17, -2], [-14, 0, -18, 10, -19, 20], [14, 0, 18, 10, 19, 20], [-10, 2, -12, 10, -11, 17], [10, 2, 12, 10, 11, 17],
    ],
  );
  ctx.restore();
}

/** Flequillo y volumen de la melena sobre la frente. */
function fringe(ctx: Ctx): void {
  maneShape(
    ctx,
    [
      [-12.8, 3.6], [-13.4, -6], [-9.4, -13.2], [0, -16.4], [9.4, -13.2], [13.4, -6], [12.8, 3.6], [10.4, -2.6], [8, 1.6], [5.4, -4.4], [2.4, 2.4], [0, -4.6], [-3, 2.4], [-5.4, -4.4], [-8, 1.6], [-10.4, -2.6],
    ],
    -16,
    4,
    [
      [-2, -15, -7, -10, -11, -3], [2, -15, 7, -10, 11, -3], [0, -14, -1, -8, 0, -4],
    ],
  );
}

/** Cara de frente: ceño muy fruncido, ojos entornados, nariz ancha y gruñido con dientes. */
function faceFront(ctx: Ctx, turn: number): void {
  // Mandíbula cuadrada
  ctx.beginPath();
  ctx.moveTo(-9.4, -4);
  ctx.bezierCurveTo(-10.4, 5, -8.4, 11, -4.8, 13);
  ctx.quadraticCurveTo(0, 14.6, 4.8, 13);
  ctx.bezierCurveTo(8.4, 11, 10.4, 5, 9.4, -4);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -10, 10, SKIN_LIGHT, SKIN_DARK), 1.7);
  ctx.fillStyle = rgb(HAIR, 0.18);
  oval(ctx, 0, 10, 7.4, 3.8);
  ctx.fill();
  ctx.fillStyle = rgb(SKIN_DARK, 0.3);
  oval(ctx, -6.6, 5.6, 2.6, 1.8);
  ctx.fill();
  oval(ctx, 6.6, 5.6, 2.6, 1.8);
  ctx.fill();

  // Ojos entornados y cejas muy bajas e inclinadas
  for (const side of [-1, 1] as const) {
    const ex = side * 4.3 + turn * 1.1;
    const ey = 1.6;
    ctx.beginPath();
    ctx.moveTo(ex - side * 3, ey + 0.9);
    ctx.quadraticCurveTo(ex, ey - 1.2, ex + side * 3, ey - 0.4);
    ctx.quadraticCurveTo(ex, ey + 1.5, ex - side * 3, ey + 0.9);
    ctx.closePath();
    ctx.fillStyle = rgb([248, 244, 232]);
    ctx.fill();
    ctx.strokeStyle = rgb(OUTLINE);
    ctx.lineWidth = 0.9;
    ctx.stroke();
    oval(ctx, ex + turn * 0.8, ey + 0.25, 1.1, 1);
    ctx.fillStyle = rgb([60, 38, 24]);
    ctx.fill();
    oval(ctx, ex + turn * 0.8, ey + 0.25, 0.5, 0.5);
    ctx.fillStyle = rgb([8, 6, 6]);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(side * 10, -4.2);
    ctx.lineTo(side * 1, 0.2);
    ctx.lineTo(side * 1, -2.4);
    ctx.lineTo(side * 10, -7);
    ctx.closePath();
    fillStroke(ctx, HAIR, 1);
  }
  line(ctx, SKIN_DARK, 0.8, [-1.3, -4], [-1.1, -2.2]);
  line(ctx, SKIN_DARK, 0.8, [1.3, -4], [1.1, -2.2]);

  // Nariz ancha con las aletas marcadas
  ctx.strokeStyle = rgb(SKIN_DARK, 0.95);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(-1, 1.6);
  ctx.quadraticCurveTo(-1.9, 5, -2.8, 6.7);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(-3.2, 7.3);
  ctx.quadraticCurveTo(0, 9, 3.2, 7.3);
  ctx.stroke();
  ctx.fillStyle = rgb(OUTLINE, 0.85);
  oval(ctx, -1.6, 7.6, 0.7, 0.5);
  ctx.fill();
  oval(ctx, 1.6, 7.6, 0.7, 0.5);
  ctx.fill();
  line(ctx, SKIN_DARK, 0.9, [-3.8, 6.4], [-5.2, 10.6]);
  line(ctx, SKIN_DARK, 0.9, [3.8, 6.4], [5.2, 10.6]);

  // Gruñido: labios retraídos y dientes apretados, con colmillos
  path(ctx, [[-5, 9.4], [5, 9.4], [4.2, 12.8], [-4.2, 12.8]]);
  fillStroke(ctx, [60, 20, 22], 1.1);
  ctx.save();
  ctx.clip();
  ctx.fillStyle = rgb([246, 240, 226]);
  ctx.fillRect(-5, 9.6, 10, 1.9);
  ctx.fillRect(-5, 11.5, 10, 1.3);
  ctx.strokeStyle = rgb([90, 70, 60]);
  ctx.lineWidth = 0.5;
  ctx.beginPath();
  for (let x = -3.4; x <= 3.5; x += 1.7) {
    ctx.moveTo(x, 9.6);
    ctx.lineTo(x, 12.8);
  }
  ctx.moveTo(-5, 11.5);
  ctx.lineTo(5, 11.5);
  ctx.stroke();
  ctx.restore();
  path(ctx, [[-4.6, 9.4], [-3.2, 9.4], [-3.9, 11.6]]);
  fillStroke(ctx, [250, 246, 232], 0.6);
  path(ctx, [[4.6, 9.4], [3.2, 9.4], [3.9, 11.6]]);
  fillStroke(ctx, [250, 246, 232], 0.6);
}

/** Cabeza de frente con melenón negro, cara de gruñido y flequillo. */
function headFront(ctx: Ctx, hx: number, hy: number, turn: number): void {
  ctx.save();
  ctx.translate(hx, hy);
  ctx.scale(HEAD_K, HEAD_K);
  maneFront(ctx);
  faceFront(ctx, turn);
  fringe(ctx);
  ctx.restore();
}

/** Cabeza de perfil mirando a +x, con la melena ondeando hacia atrás. */
function headSide(ctx: Ctx, hx: number, hy: number, sway: number): void {
  ctx.save();
  ctx.translate(hx, hy);
  ctx.scale(HEAD_K, HEAD_K);
  const w = sway;
  maneShape(
    ctx,
    [
      [3, -18], [-4, -22.4], [-12, -19.4], [-18, -12.4], [-22, -4], [-21.4 + w * 0.2, 4], [-25 + w * 0.4, 10], [-22 + w * 0.5, 15], [-26.4 + w * 0.7, 22], [-20 + w * 0.5, 19.4], [-18.4 + w * 0.7, 26], [-14 + w * 0.4, 18.6],
      [-10, 22], [-7, 14.6], [-3, 12], [1, 6],
    ],
    -22,
    26,
    [[-2, -19, -12, -14, -19, -3], [-6, -10, -16, 0, -21 + w * 0.3, 14], [-8, 4, -13, 12, -14, 20]],
  );
  // Cráneo y cara en perfil: frente, nariz ancha, gruñido y mandíbula cuadrada
  ctx.beginPath();
  ctx.moveTo(-8.4, -7);
  ctx.bezierCurveTo(-10, 4, -8, 11, -2, 13);
  ctx.quadraticCurveTo(4, 14, 7.2, 12);
  ctx.quadraticCurveTo(8.6, 11, 8, 9.6);
  ctx.quadraticCurveTo(9, 8.6, 8, 7.6);
  ctx.quadraticCurveTo(8.6, 6.8, 7.8, 6.2);
  ctx.quadraticCurveTo(12.6, 5, 9.2, 2.8);
  ctx.quadraticCurveTo(8.8, 0.6, 7.8, -1.6);
  ctx.quadraticCurveTo(8.2, -4, 7.2, -7);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -10, 11, SKIN_DARK, SKIN_LIGHT), 1.7);
  path(ctx, [[3.2, 1.8], [5.4, 0.7], [7.2, 1.7], [5.4, 2.9]]);
  ctx.fillStyle = rgb([248, 244, 232]);
  ctx.fill();
  oval(ctx, 5.9, 1.8, 0.95, 1);
  ctx.fillStyle = rgb([30, 20, 14]);
  ctx.fill();
  path(ctx, [[1.4, -2.6], [8.2, -0.2], [8.2, -3], [1.6, -5.4]]);
  fillStroke(ctx, HAIR, 1);
  path(ctx, [[8, 8.2], [4, 8.4], [4.2, 11.2], [7.8, 11]]);
  fillStroke(ctx, [60, 20, 22], 1);
  ctx.fillStyle = rgb([246, 240, 226]);
  ctx.fillRect(4.3, 8.7, 3.4, 1.8);
  line(ctx, SKIN_DARK, 0.9, [3.4, 6.2], [3, 9.8]);
  oval(ctx, -2.6, 4.8, 1.9, 3);
  fillStroke(ctx, SKIN_DARK, 1.2);
  ctx.fillStyle = rgb(HAIR, 0.2);
  oval(ctx, 2.4, 10.6, 5.4, 2.6);
  ctx.fill();
  // Flequillo y melena sobre la frente
  maneShape(
    ctx,
    [[-8, -8], [-7, -15], [-1, -19], [6, -17], [10.4, -11], [9.4, -5.4], [7, -1.6], [5.4, -5.6], [2.6, -0.8], [0.6, -6], [-2, -1.6], [-4.4, -6.6], [-6.4, -2]],
    -19,
    -2,
    [[-4, -15, 2, -12, 8, -8]],
  );
  ctx.restore();
}

/** Cabeza vista por detrás: la melena negra cae por la nuca y la espalda. */
function headBack(ctx: Ctx, hx: number, hy: number, sway: number): void {
  ctx.save();
  ctx.translate(hx, hy);
  ctx.scale(HEAD_K, HEAD_K);
  const w = sway * 0.4;
  ctx.save();
  ctx.translate(0, -24);
  ctx.scale(0.88, 0.7);
  ctx.translate(0, 24);
  maneShape(
    ctx,
    [
      [0, -23.6], [6, -21.4], [13, -16.4], [17, -8.4], [19.4, 0], [18, 8], [21, 14], [18.4, 20], [19.6, 25.6 + w * 0.3], [14.4, 22], [12.4, 27 + w * 0.5], [8, 21.6], [4.4, 28 + w * 0.5], [0, 22.4],
      [-3.6, 28 + w * 0.5], [-8, 21.6], [-12.4, 27 + w * 0.5], [-14.4, 22], [-19.6, 25.6 + w * 0.3], [-18.4, 20], [-21, 14], [-18, 8], [-19.4, 0], [-17, -8.4], [-13, -16.4], [-6, -21.4],
    ],
    -24,
    28,
    [
      [0, -20, 1, 2, 0, 22], [-5, -18, -9, 4, -8, 22], [5, -18, 9, 4, 8, 22], [-11, -12, -16, 6, -14, 22], [11, -12, 16, 6, 14, 22], [-15, -2, -19, 10, -18, 20], [15, -2, 19, 10, 18, 20],
    ],
  );
  ctx.restore();
  ctx.restore();
}

// ---------------------------------------------------------------------------
// Pies descalzos y taparrabos
// ---------------------------------------------------------------------------

function foot(ctx: Ctx, ankle: Pt, view: 'front' | 'back' | 'side'): void {
  const [x, y] = ankle;
  if (view === 'side') {
    ctx.beginPath();
    ctx.moveTo(x - 5, y - 2);
    ctx.quadraticCurveTo(x - 6.4, y + 4, x - 2, y + 4.4);
    ctx.lineTo(x + 9.6, y + 4.4);
    ctx.quadraticCurveTo(x + 13.4, y + 3.6, x + 12, y + 1);
    ctx.quadraticCurveTo(x + 6, y - 1.6, x + 3.4, y - 3.6);
    ctx.closePath();
    fillStroke(ctx, vGradient(ctx, y - 3, y + 5, SKIN_LIGHT, SKIN_DARK), 1.7);
    for (let i = 0; i < 4; i++) {
      line(ctx, SKIN_DARK, 0.7, [x + 6.4 + i * 1.7, y + 1.4], [x + 6.6 + i * 1.7, y + 4.2]);
    }
  } else if (view === 'back') {
    oval(ctx, x, y + 1, 6.4, 4.6);
    fillStroke(ctx, vGradient(ctx, y - 3, y + 6, SKIN_LIGHT, SKIN_DARK), 1.7);
  } else {
    oval(ctx, x, y + 1.2, 7.2, 4.4);
    fillStroke(ctx, vGradient(ctx, y - 3, y + 6, SKIN_LIGHT, SKIN_DARK), 1.7);
    for (let i = -2; i <= 2; i++) {
      oval(ctx, x + i * 2.9, y + 5, 1.7, 1.5);
      fillStroke(ctx, vGradient(ctx, y + 3.5, y + 6.5, SKIN_LIGHT, SKIN_DARK), 1.1);
    }
  }
  // Correa en el tobillo
  strap(ctx, [x - 4, y - 3.4], [x + 4, y - 3.4], 0.5, 6.4);
}

/** Taparrabos de cuero con el borde deshilachado; `swing` lo mece al andar. */
function loincloth(ctx: Ctx, topY: number, w: number, swing: number, dark: boolean): void {
  const k = dark ? 0.82 : 1;
  const pts: Pt[] = [
    [-w, topY], [w, topY], [w + 1 + swing, topY + 12], [w * 0.8 + swing, topY + 10.6], [w * 0.6 + swing, topY + 16.4], [w * 0.34 + swing * 0.8, topY + 12], [w * 0.1 + swing * 0.8, topY + 19.4], [-w * 0.18 + swing * 0.6, topY + 12.4],
    [-w * 0.46 + swing * 0.6, topY + 17.4], [-w * 0.72 + swing * 0.4, topY + 11.6], [-w * 0.9 + swing * 0.4, topY + 15], [-w - 1 + swing * 0.4, topY + 11],
  ];
  path(ctx, pts);
  fillStroke(ctx, vGradient(ctx, topY, topY + 19, shade(CLOTH, k), shade(CLOTH_DARK, k)), 1.8);
  line(ctx, shade(CLOTH_DARK, 0.8), 0.9, [0, topY + 1], [swing * 0.4, topY + 10]);
  ctx.strokeStyle = rgb(shade(CLOTH_DARK, 0.8), 0.9);
  ctx.lineWidth = 0.8;
  ctx.setLineDash([1.4, 1.2]);
  ctx.beginPath();
  ctx.moveTo(-w + 1, topY + 2.2);
  ctx.lineTo(w - 1, topY + 2.2);
  ctx.stroke();
  ctx.setLineDash([]);
}

// ---------------------------------------------------------------------------
// Bárbaro
// ---------------------------------------------------------------------------

export function drawBarbarian(ctx: Ctx, cx: number, cy: number, size: number, look: WarriorLook): void {
  const { walkAngle, moving, facing, headTurn, showWeapons, swordPower, now } = look;
  frame(ctx, cx, cy, size, () => {
    const side = facing === 'E' || facing === 'O';
    // La figura es muy alta de cabeza: se reduce un poco, manteniendo los pies en el suelo
    ctx.translate(0, 47);
    ctx.scale(0.9, 0.9);
    ctx.translate(0, -47);
    if (facing === 'O') ctx.scale(-1, 1);

    const breath = moving ? 0 : Math.sin(now * 0.003) * 0.5;
    const bob = moving ? -Math.abs(Math.sin(walkAngle)) * 1.8 : breath;
    const sway = moving ? Math.sin(walkAngle * 2 - 0.6) * 2.4 : Math.sin(now * 0.004) * 1.2;

    ctx.fillStyle = 'rgba(0,0,0,0.38)';
    oval(ctx, side ? 1 : 0, 47.5, side ? 19 : 27, 5.6);
    ctx.fill();

    if (side) drawSide(ctx, { walkAngle, moving, showWeapons, swordPower, now, bob, sway });
    else drawFrontBack(ctx, { walkAngle, moving, showWeapons, swordPower, now, bob, sway, back: facing === 'N', headTurn });
  });
}

interface RigBase {
  walkAngle: number;
  moving: boolean;
  showWeapons: boolean;
  swordPower: boolean;
  now: number;
  bob: number;
  sway: number;
}

// --- De frente y de espaldas ------------------------------------------------

function drawFrontBack(ctx: Ctx, r: RigBase & { back: boolean; headTurn: number }): void {
  const { walkAngle, moving, showWeapons, swordPower, now, bob, sway, back, headTurn } = r;
  const depth = back ? -1 : 1;
  const hipY = 21 + bob;
  const shoulderY = -7 + bob;

  // Piernas desnudas, gruesas y abiertas, en cuclillas
  const legs: Array<{ k: -1 | 1; knee: Pt; ankle: Pt }> = [];
  for (const k of [-1, 1] as const) {
    const a = moving ? walkAngle + (k === 1 ? Math.PI : 0) : 0;
    const swing = Math.sin(a);
    const swingLift = Math.max(0, Math.cos(a)) * 3.4;
    const fx = k * (11.4 + (moving ? 0 : 0.6));
    const fy = GROUND - 5 + depth * swing * 2.4 - (moving ? swingLift : 0);
    const { j, e } = ik(k * 7.4, hipY, fx, fy, THIGH, SHIN, k === 1 ? -1 : 1);
    legs.push({ k, knee: j, ankle: e });
  }
  for (const { k, knee, ankle } of legs) {
    capsule(ctx, [k * 7.4, hipY], knee, 12, SKIN);
    capsule(ctx, knee, ankle, 9.4, SKIN);
    joint(ctx, knee, 4.4, SKIN);
    strap(ctx, [k * 7.4, hipY], knee, 0.78, 11);
    strap(ctx, knee, ankle, 0.6, 9);
    foot(ctx, [ankle[0], ankle[1] + 3], back ? 'back' : 'front');
  }

  // Brazos abiertos y doblados, cada mano con una daga
  const arms = ([-1, 1] as const).map((k) => {
    const a = moving ? walkAngle + (k === -1 ? Math.PI : 0) : 0;
    const sx = k * 17.4;
    let tx = k * 26;
    let ty = shoulderY + 12 + (moving ? Math.sin(a) * 1.4 : 0);
    if (!showWeapons) {
      tx = k * 23;
      ty = shoulderY + 19 + (moving ? -Math.sin(a) * 2.2 : 0);
    }
    const { j, e } = ik(sx, shoulderY + 3, tx, ty, UPPER_ARM, FOREARM, k === 1 ? -1 : 1);
    return { k, sx, elbow: j, hand: e };
  });
  const drawArm = (arm: (typeof arms)[number]) => {
    capsule(ctx, [arm.sx, shoulderY + 3], arm.elbow, 11.8, SKIN);
    capsule(ctx, arm.elbow, arm.hand, 10, SKIN);
    joint(ctx, arm.elbow, 4.2, SKIN);
    strap(ctx, [arm.sx, shoulderY + 3], arm.elbow, 0.55, 11);
    strap(ctx, arm.elbow, arm.hand, 0.42, 9.6);
    strap(ctx, arm.elbow, arm.hand, 0.8, 9.2);
  };
  const drawHand = (arm: (typeof arms)[number]) => {
    oval(ctx, arm.hand[0], arm.hand[1], 5.2, 5);
    fillStroke(ctx, vGradient(ctx, arm.hand[1] - 5, arm.hand[1] + 5, SKIN_LIGHT, SKIN_DARK), 1.6);
    for (const dx of [-2.2, 0, 2.2]) line(ctx, SKIN_DARK, 0.7, [arm.hand[0] + dx, arm.hand[1] - 0.6], [arm.hand[0] + dx, arm.hand[1] + 1.6]);
  };
  const drawDaggers = () => {
    if (!showWeapons) return;
    for (const arm of arms) {
      // Hojas hacia arriba y hacia fuera, con la punta curvada hacia el cuerpo
      dagger(ctx, arm.hand[0], arm.hand[1] + 1, arm.k * 0.34 + (moving ? Math.sin(walkAngle + arm.k) * 0.04 : 0), -arm.k, swordPower, now);
    }
  };

  // Taparrabos trasero (de espaldas) detrás del torso
  const cloth = moving ? Math.sin(walkAngle) * 2.2 : 0;
  if (back) loincloth(ctx, 14 + bob, 10.6, cloth, true);

  // De espaldas las dagas quedan detrás de brazos y torso
  if (back) {
    drawDaggers();
    arms.forEach(drawArm);
  }

  // Torso desnudo y ancho, con los músculos marcados
  ctx.beginPath();
  ctx.moveTo(-18, shoulderY + 1);
  ctx.quadraticCurveTo(0, shoulderY - 4, 18, shoulderY + 1);
  ctx.bezierCurveTo(18.6, shoulderY + 10, 13.4, 10 + bob, 11.4, 17 + bob);
  ctx.lineTo(-11.4, 17 + bob);
  ctx.bezierCurveTo(-13.4, 10 + bob, -18.6, shoulderY + 10, -18, shoulderY + 1);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -18, 18, SKIN_LIGHT, SKIN), 2);
  ctx.strokeStyle = rgb(SKIN_DARK, 0.9);
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  if (!back) {
    // Pectorales, esternón y abdominales
    ctx.moveTo(-1.2, shoulderY + 8);
    ctx.quadraticCurveTo(-9, shoulderY + 13, -15, shoulderY + 5);
    ctx.moveTo(1.2, shoulderY + 8);
    ctx.quadraticCurveTo(9, shoulderY + 13, 15, shoulderY + 5);
    ctx.moveTo(0, shoulderY + 4);
    ctx.lineTo(0, 15 + bob);
    for (let i = 0; i < 3; i++) {
      ctx.moveTo(-6.4, 6 + i * 3.4 + bob);
      ctx.lineTo(6.4, 6 + i * 3.4 + bob);
    }
    ctx.stroke();
    ctx.strokeStyle = rgb(SKIN_LIGHT, 0.8);
    ctx.lineWidth = 0.9;
    ctx.beginPath();
    ctx.moveTo(-14, shoulderY + 6);
    ctx.quadraticCurveTo(-9, shoulderY + 11, -2, shoulderY + 9.4);
    ctx.moveTo(14, shoulderY + 6);
    ctx.quadraticCurveTo(9, shoulderY + 11, 2, shoulderY + 9.4);
    ctx.stroke();
  } else {
    // Espalda: columna, omóplatos y dorsales
    ctx.moveTo(0, shoulderY + 1);
    ctx.lineTo(0, 15 + bob);
    ctx.moveTo(-1.2, shoulderY + 6);
    ctx.quadraticCurveTo(-9, shoulderY + 10, -14.4, shoulderY + 3);
    ctx.moveTo(1.2, shoulderY + 6);
    ctx.quadraticCurveTo(9, shoulderY + 10, 14.4, shoulderY + 3);
    ctx.moveTo(-11, 2 + bob);
    ctx.quadraticCurveTo(-5, 7 + bob, -2, 13 + bob);
    ctx.moveTo(11, 2 + bob);
    ctx.quadraticCurveTo(5, 7 + bob, 2, 13 + bob);
    ctx.stroke();
  }
  // Correas cruzadas sobre el pecho (arnés), que se juntan en la hebilla en X
  for (const k of [-1, 1] as const) {
    path(ctx, [[k * 8, shoulderY + 0.4], [k * 12, shoulderY + 1.8], [k * 2.6, 14 + bob], [k * -1.6, 14 + bob]]);
    fillStroke(ctx, vGradient(ctx, shoulderY, 14, shade(LEATHER, 1.2), LEATHER_DARK), 1.2);
  }
  if (back) xBuckle(ctx, 0, shoulderY + 8.4, 2.8);

  // Taparrabos delantero y cinturón ancho con hebilla en X y bolsas
  if (!back) loincloth(ctx, 14 + bob, 10, cloth, false);
  path(ctx, [[-12.4, 13 + bob], [12.4, 13 + bob], [12.4, 18.4 + bob], [-12.4, 18.4 + bob]]);
  fillStroke(ctx, LEATHER, 1.8);
  if (!back) {
    xBuckle(ctx, 0, 15.8 + bob, 4.4);
    pouch(ctx, -10, 16.4 + bob, 4.6, 5.8);
    pouch(ctx, 10, 16.4 + bob, 4.6, 5.8);
  } else {
    pouch(ctx, -8.4, 15.8 + bob, 6.4, 8.2);
    pouch(ctx, 8.4, 15.8 + bob, 6.4, 8.2);
  }

  if (!back) arms.forEach(drawArm);

  // Hombros enormes (deltoides), por encima de los brazos
  for (const k of [-1, 1] as const) {
    ctx.beginPath();
    ctx.moveTo(k * 8.8, shoulderY - 2.4);
    ctx.quadraticCurveTo(k * 21, shoulderY - 9, k * 25.4, shoulderY + 5);
    ctx.quadraticCurveTo(k * 20, shoulderY + 2, k * 11.4, shoulderY + 4);
    ctx.closePath();
    fillStroke(ctx, hGradient(ctx, k * 9, k * 25, SKIN_LIGHT, SKIN_DARK), 1.9);
    line(ctx, SKIN_DARK, 0.9, [k * 12, shoulderY - 1], [k * 21, shoulderY + 1.4]);
  }

  // Manos y dagas, por delante de los hombros
  if (!back) {
    drawDaggers();
    arms.forEach(drawHand);
  } else {
    arms.forEach(drawHand);
  }

  // Cabeza enorme con melenón, hundida entre los hombros
  const hy = -20 + bob;
  if (back) headBack(ctx, 0, hy, sway);
  else headFront(ctx, headTurn * 3, hy, headTurn);
}

// --- De perfil (mirando a +x; para el oeste se refleja el lienzo): encorvado y ancho ---

function drawSide(ctx: Ctx, r: RigBase): void {
  const { walkAngle, moving, showWeapons, swordPower, now, bob, sway } = r;
  const hipY = 22 + bob;
  // Muy inclinado hacia delante: hombros bajos y adelantados, espalda en joroba
  const lean = moving ? 8.4 : 7;
  const shoulderY = -3 + bob;

  const leg = (near: boolean) => {
    const a = moving ? walkAngle + (near ? 0 : Math.PI) : 0;
    const hip: Pt = [-1.4, hipY];
    const fx = hip[0] + (moving ? Math.sin(a) * 8.4 : near ? 4.2 : -3.4);
    const lift = moving ? Math.max(0, Math.cos(a)) * 5.2 : 0;
    // Rodillas muy dobladas: pierna corta y gruesa, pies bien separados
    const { j, e } = ik(hip[0], hip[1], fx, GROUND - 5 - lift, THIGH, SHIN, -1);
    return { hip, knee: j, ankle: e };
  };
  const farLeg = leg(false);
  const nearLeg = leg(true);

  const arm = (near: boolean) => {
    const a = moving ? walkAngle + (near ? Math.PI : 0) : 0;
    const sh: Pt = [lean - 1 + (near ? 1.2 : -0.6), shoulderY + 4];
    let tx = sh[0] + (moving ? Math.sin(a) * 7 : 3.2);
    let ty = sh[1] + 17 - (moving ? Math.abs(Math.sin(a)) * 1.6 : 0);
    if (showWeapons) {
      tx = sh[0] + (near ? 13.6 : 9.4);
      ty = sh[1] + (near ? 9 : 11.6);
    }
    const { j, e } = ik(sh[0], sh[1], tx, ty, UPPER_ARM, FOREARM, 1);
    return { sh, elbow: j, hand: e };
  };
  const farArm = arm(false);
  const nearArm = arm(true);

  const drawLeg = (l: ReturnType<typeof leg>) => {
    capsule(ctx, l.hip, l.knee, 12.4, SKIN);
    capsule(ctx, l.knee, l.ankle, 9.6, SKIN);
    joint(ctx, l.knee, 4.4, SKIN);
    strap(ctx, l.hip, l.knee, 0.78, 11);
    strap(ctx, l.knee, l.ankle, 0.6, 9);
    foot(ctx, [l.ankle[0], l.ankle[1] + 3], 'side');
  };
  const drawArm = (a: ReturnType<typeof arm>) => {
    capsule(ctx, a.sh, a.elbow, 12, SKIN);
    capsule(ctx, a.elbow, a.hand, 10, SKIN);
    joint(ctx, a.elbow, 4.2, SKIN);
    strap(ctx, a.sh, a.elbow, 0.55, 11);
    strap(ctx, a.elbow, a.hand, 0.42, 9.6);
    strap(ctx, a.elbow, a.hand, 0.8, 9.2);
  };
  const drawHand = (a: ReturnType<typeof arm>) => {
    oval(ctx, a.hand[0], a.hand[1], 5, 4.8);
    fillStroke(ctx, vGradient(ctx, a.hand[1] - 5, a.hand[1] + 5, SKIN_LIGHT, SKIN_DARK), 1.6);
  };

  // Lado lejano, detrás del cuerpo
  drawLeg(farLeg);
  drawArm(farArm);
  if (showWeapons) dagger(ctx, farArm.hand[0], farArm.hand[1] + 1, 0.2, -1, swordPower, now);
  drawHand(farArm);

  // Taparrabos trasero y torso ancho y encorvado: espalda en joroba, pecho y barriga adelante
  const cloth = moving ? Math.sin(walkAngle) * 3 : 0;
  loincloth(ctx, 14 + bob, 9, cloth - 3, true);
  ctx.beginPath();
  ctx.moveTo(-9.6, 18 + bob);
  ctx.bezierCurveTo(-14.6, 10 + bob, -13.6, shoulderY + 5, -7 + lean * 0.5, shoulderY - 3);
  ctx.bezierCurveTo(-1 + lean * 0.7, shoulderY - 8, 9 + lean, shoulderY - 5, 12.4 + lean, shoulderY + 3);
  ctx.bezierCurveTo(15 + lean * 0.8, shoulderY + 9, 15.4 + lean * 0.3, 8 + bob, 12.8 + lean * 0.1, 14 + bob);
  ctx.lineTo(11.6, 18 + bob);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -14, 16, SKIN_DARK, SKIN_LIGHT), 2);
  // Músculos: dorsal y trapecio, pectoral y abdominales
  ctx.strokeStyle = rgb(SKIN_DARK, 0.9);
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.moveTo(-6 + lean * 0.5, shoulderY + 1);
  ctx.quadraticCurveTo(-11, 4 + bob, -8, 14 + bob);
  ctx.moveTo(4 + lean * 0.6, shoulderY + 7);
  ctx.quadraticCurveTo(11 + lean * 0.6, shoulderY + 10, 14 + lean * 0.5, shoulderY + 5);
  for (let i = 0; i < 3; i++) {
    ctx.moveTo(6 + lean * 0.3, 6 + i * 3.4 + bob);
    ctx.lineTo(12 + lean * 0.2, 6.6 + i * 3.4 + bob);
  }
  ctx.stroke();
  // Correa del arnés cruzando el torso en diagonal
  path(ctx, [[-4 + lean * 0.6, shoulderY - 2], [-0.4 + lean * 0.6, shoulderY - 3], [11.4, 14 + bob], [7.6, 15.6 + bob]]);
  fillStroke(ctx, vGradient(ctx, shoulderY, 16, shade(LEATHER, 1.2), LEATHER_DARK), 1.2);

  // Cinturón y taparrabos delantero
  loincloth(ctx, 14 + bob, 8.8, cloth + 3, false);
  path(ctx, [[-10.6, 13 + bob], [12.4, 13 + bob], [12.4, 18.4 + bob], [-10.6, 18.4 + bob]]);
  fillStroke(ctx, LEATHER, 1.6);
  xBuckle(ctx, 9.8, 15.8 + bob, 3.4);
  pouch(ctx, -6.4, 15.8 + bob, 6.2, 8);

  // Lado cercano, por delante
  drawLeg(nearLeg);
  drawArm(nearArm);
  // Hombro y deltoides
  ctx.beginPath();
  ctx.moveTo(-5 + lean, shoulderY - 4.4);
  ctx.quadraticCurveTo(9 + lean, shoulderY - 9, 13.6 + lean, shoulderY + 4);
  ctx.quadraticCurveTo(5 + lean, shoulderY + 2, -4 + lean, shoulderY + 5);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -5, 13, SKIN_DARK, SKIN_LIGHT), 1.8);
  if (showWeapons) dagger(ctx, nearArm.hand[0], nearArm.hand[1] + 1, 0.2 + (moving ? Math.sin(walkAngle) * 0.03 : 0), -1, swordPower, now);
  drawHand(nearArm);

  // La cabeza cuelga hacia delante, hundida entre los hombros
  headSide(ctx, 5.4 + lean, -15 + bob, sway);
}
