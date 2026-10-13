/**
 * Guerrero articulado: esqueleto con cadera, rodillas, hombros y codos que se resuelve con
 * cinemática inversa, visto de frente, de espaldas o de perfil según hacia dónde camine.
 *
 * Se dibuja en un cuadro de 100×100 unidades centrado en (0, 0), como el resto de sprites.
 */
import type { Ctx, RGB } from './gfx';
import { rgb } from './gfx';
import { fillStroke, frame, glow, hGradient, line, OUTLINE, oval, path, rGradient, shade, vGradient, type Pt } from './sprites';

export type Facing = 'N' | 'E' | 'S' | 'O';

export interface WarriorLook {
  /** Ángulo del ciclo de marcha en radianes (avanza mientras camina). */
  walkAngle: number;
  moving: boolean;
  facing: Facing;
  /** Mirada a los lados durante la introducción: -1, 0 o 1 (solo de frente). */
  headTurn: number;
  showWeapons: boolean;
  swordPower: boolean;
  /** Reloj del juego en ms, para la respiración y el vaivén del penacho. */
  now: number;
}

// Paleta cálida y apagada, como las imágenes de los pensamientos
const ARMOR: RGB = [128, 128, 112];
const ARMOR_LIGHT: RGB = [168, 168, 148];
const ARMOR_DARK: RGB = [78, 78, 68];
const MAIL: RGB = [112, 110, 98];
const RED: RGB = [196, 52, 42];
const RED_DARK: RGB = [124, 26, 28];
const SKIN: RGB = [234, 180, 136];
const SKIN_LIGHT: RGB = [248, 202, 160];
const SKIN_DARK: RGB = [196, 138, 98];
const LEATHER: RGB = [142, 90, 52];
const LEATHER_DARK: RGB = [92, 56, 34];
const GOLD: RGB = [236, 178, 56];
const GOLD_DARK: RGB = [160, 104, 24];
const BLADE: RGB = [208, 212, 202];
const HAIR: RGB = [74, 44, 28];

// ---------------------------------------------------------------------------
// Esqueleto
// ---------------------------------------------------------------------------

/** Cinemática inversa de dos huesos: devuelve la articulación (rodilla/codo) y el extremo alcanzable. */
function ik(ax: number, ay: number, tx: number, ty: number, l1: number, l2: number, bend: 1 | -1): { j: Pt; e: Pt } {
  let dx = tx - ax;
  let dy = ty - ay;
  let d = Math.hypot(dx, dy) || 0.001;
  const maxD = l1 + l2 - 0.05;
  if (d > maxD) {
    dx *= maxD / d;
    dy *= maxD / d;
    d = maxD;
  }
  const a = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
  const h = Math.sqrt(Math.max(0, l1 * l1 - a * a));
  const mx = ax + (dx * a) / d;
  const my = ay + (dy * a) / d;
  return { j: [mx + (bend * h * -dy) / d, my + (bend * h * dx) / d], e: [ax + dx, ay + dy] };
}

/** Cápsula gruesa con contorno entre dos puntos. */
function capsule(ctx: Ctx, a: Pt, b: Pt, width: number, fill: RGB, outline = 1.1): void {
  ctx.lineCap = 'round';
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = width + outline * 2;
  ctx.beginPath();
  ctx.moveTo(a[0], a[1]);
  ctx.lineTo(b[0], b[1]);
  ctx.stroke();
  ctx.strokeStyle = rgb(fill);
  ctx.lineWidth = width;
  ctx.stroke();
  // Brillo suave a lo largo del hueso
  ctx.strokeStyle = rgb(shade(fill, 1.28), 0.5);
  ctx.lineWidth = Math.max(0.8, width * 0.28);
  const nx = -(b[1] - a[1]);
  const ny = b[0] - a[0];
  const n = Math.hypot(nx, ny) || 1;
  const off = width * 0.2;
  ctx.beginPath();
  ctx.moveTo(a[0] + (nx / n) * -off, a[1] + (ny / n) * -off);
  ctx.lineTo(b[0] + (nx / n) * -off, b[1] + (ny / n) * -off);
  ctx.stroke();
}

function joint(ctx: Ctx, p: Pt, r: number, fill: RGB): void {
  oval(ctx, p[0], p[1], r, r);
  fillStroke(ctx, rGradient(ctx, p[0], p[1], r * 1.4, shade(fill, 1.3), shade(fill, 0.8)), 1.3);
}

// ---------------------------------------------------------------------------
// Objetos
// ---------------------------------------------------------------------------

/** Espada con la mano en (0, 0) y la hoja hacia arriba; `tilt` la inclina hacia +x. */
function sword(ctx: Ctx, x: number, y: number, tilt: number, power: boolean, now: number): void {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(tilt);
  const tipY = -50;
  if (power) {
    glow(ctx, 0, tipY / 2, 32, [190, 235, 255], 0.5 + Math.sin(now * 0.01) * 0.08);
    ctx.strokeStyle = 'rgba(190,230,255,0.85)';
    ctx.lineWidth = 1.2;
    for (let i = 0; i < 6; i++) {
      const yy = tipY + 8 + i * 8;
      ctx.beginPath();
      ctx.moveTo(6, yy);
      ctx.lineTo(10 + (i % 2) * 3, yy - 2);
      ctx.moveTo(-6, yy);
      ctx.lineTo(-10 - (i % 2) * 3, yy - 2);
      ctx.stroke();
    }
  }
  // Hoja facetada
  path(ctx, [[-3.4, -3], [3.4, -3], [3, tipY + 6], [0, tipY], [-3, tipY + 6]]);
  fillStroke(ctx, power ? [224, 247, 255] : BLADE, 1.9);
  path(ctx, [[0.3, -3], [3.4, -3], [3, tipY + 6], [0.3, tipY + 1]]);
  ctx.fillStyle = rgb([120, 146, 160], 0.5);
  ctx.fill();
  line(ctx, [96, 104, 100], 0.8, [0, -5], [0, tipY + 7]);
  // Guarda dorada curvada hacia arriba
  ctx.beginPath();
  ctx.moveTo(-10, -6);
  ctx.quadraticCurveTo(-8, -1, -3, -1.4);
  ctx.lineTo(3, -1.4);
  ctx.quadraticCurveTo(8, -1, 10, -6);
  ctx.quadraticCurveTo(5, -4, 0, -4);
  ctx.quadraticCurveTo(-5, -4, -10, -6);
  ctx.closePath();
  fillStroke(ctx, vGradient(ctx, -7, -1, GOLD, GOLD_DARK), 1.7);
  // Empuñadura y pomo
  path(ctx, [[-1.9, -1.4], [1.9, -1.4], [1.9, 7], [-1.9, 7]]);
  fillStroke(ctx, LEATHER, 1.5);
  oval(ctx, 0, 9.2, 2.9, 2.9);
  fillStroke(ctx, rGradient(ctx, 0, 9.2, 4, [255, 214, 110], GOLD_DARK), 1.5);
  ctx.restore();
}

/** Escudo en forma de cometa centrado en (x, y); `squash` lo estrecha (1 de frente, ~0.3 de canto). */
function shield(ctx: Ctx, x: number, y: number, squash: number): void {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(squash, 1);
  const outline = 2.2 / Math.max(0.5, squash);
  ctx.beginPath();
  ctx.moveTo(-14, -15);
  ctx.quadraticCurveTo(0, -20, 14, -15);
  ctx.bezierCurveTo(16, 4, 9, 17, 0, 24);
  ctx.bezierCurveTo(-9, 17, -16, 4, -14, -15);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -14, 15, ARMOR_LIGHT, ARMOR_DARK), outline);
  ctx.beginPath();
  ctx.moveTo(-9.8, -11.4);
  ctx.quadraticCurveTo(0, -15, 9.8, -11.4);
  ctx.bezierCurveTo(11, 3, 5.6, 13, 0, 18.6);
  ctx.bezierCurveTo(-5.6, 13, -11, 3, -9.8, -11.4);
  ctx.closePath();
  ctx.fillStyle = rgb(ARMOR);
  ctx.fill();
  ctx.strokeStyle = rgb(ARMOR_DARK);
  ctx.lineWidth = 1.3 / Math.max(0.5, squash);
  ctx.stroke();
  line(ctx, ARMOR_DARK, 1 / Math.max(0.5, squash), [-1, -12], [-1, 16]);
  ctx.restore();
}

// ---------------------------------------------------------------------------
// Cabezas
// ---------------------------------------------------------------------------

/** Penacho: arco rojo que cae hacia `dir` (-1 izquierda, 1 derecha) y ondea con el movimiento. */
function plume(ctx: Ctx, x: number, y: number, dir: number, sway: number, drop: number): void {
  const d = dir;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.bezierCurveTo(x + d * 3, y - 18, x + d * (17 + sway), y - 16 + drop * 0.2, x + d * (22 + sway * 1.5), y - 2 + drop);
  ctx.bezierCurveTo(x + d * (17 + sway), y - 6, x + d * 10, y - 6, x + d * 5, y + 1);
  ctx.closePath();
  fillStroke(ctx, vGradient(ctx, y - 18, y + 4, [216, 70, 54], RED_DARK), 1.8);
  line(ctx, [240, 120, 96], 0.8, [x + d * 2, y - 2], [x + d * (11 + sway * 0.6), y - 12], [x + d * (19 + sway), y - 3 + drop * 0.8]);
  line(ctx, RED_DARK, 0.8, [x + d * 4, y + 0.5], [x + d * (14 + sway * 0.8), y - 6], [x + d * (21 + sway * 1.2), y - 1 + drop * 0.9]);
}

/** Yelmo de ranuras visto de frente (la cara queda debajo de la ceja de metal). */
function helmetFront(ctx: Ctx, hx: number, hy: number): void {
  ctx.beginPath();
  ctx.moveTo(hx - 11, hy + 1.5);
  ctx.bezierCurveTo(hx - 11.5, hy - 17, hx + 11.5, hy - 17, hx + 11, hy + 1.5);
  ctx.quadraticCurveTo(hx + 7, hy - 3.2, hx, hy - 3.6);
  ctx.quadraticCurveTo(hx - 7, hy - 3.2, hx - 11, hy + 1.5);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, hx - 11, hx + 11, ARMOR_LIGHT, ARMOR_DARK), 2);
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = 1.3;
  for (let i = -2; i <= 2; i++) {
    ctx.beginPath();
    ctx.moveTo(hx + i * 3.6, hy - 10.8 + Math.abs(i) * 0.9);
    ctx.lineTo(hx + i * 3.6 + i * 0.5, hy - 6.4 + Math.abs(i) * 0.5);
    ctx.stroke();
  }
  oval(ctx, hx, hy - 12.8, 2.6, 2.3);
  fillStroke(ctx, vGradient(ctx, hy - 15, hy - 10.5, ARMOR_LIGHT, ARMOR_DARK), 1.4);
  for (const side of [-1, 1] as const) {
    oval(ctx, hx + side * 10.6, hy + 2, 2.1, 2.6);
    fillStroke(ctx, rGradient(ctx, hx + side * 10.6, hy + 2, 3, ARMOR_LIGHT, ARMOR_DARK), 1.2);
  }
}

/** Cara de frente con proporciones humanas: ojos pequeños con párpado, cejas, nariz y labios. */
function faceFront(ctx: Ctx, hx: number, hy: number, turn: number): void {
  // Mandíbula y cuello
  ctx.beginPath();
  ctx.moveTo(hx - 8.6, hy - 1);
  ctx.bezierCurveTo(hx - 9, hy + 7, hx - 6.5, hy + 12.4, hx, hy + 12.8);
  ctx.bezierCurveTo(hx + 6.5, hy + 12.4, hx + 9, hy + 7, hx + 8.6, hy - 1);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, hx - 9, hx + 9, SKIN_LIGHT, SKIN_DARK), 1.8);
  // Sombras bajo el pómulo y la barbilla
  ctx.fillStyle = rgb(SKIN_DARK, 0.28);
  oval(ctx, hx - 6, hy + 6.2, 2.6, 1.7);
  ctx.fill();
  oval(ctx, hx + 6, hy + 6.2, 2.6, 1.7);
  ctx.fill();
  // Ojos
  for (const side of [-1, 1] as const) {
    const ex = hx + side * 3.9 + turn * 1.1;
    const ey = hy + 1.6;
    path(ctx, [[ex - 2.6 * side, ey + 0.2], [ex, ey - 1.3], [ex + 2.6 * side, ey + 0.4], [ex, ey + 1.3]]);
    ctx.fillStyle = rgb([250, 246, 236]);
    ctx.fill();
    oval(ctx, ex + turn * 0.9, ey + 0.1, 1.15, 1.2);
    ctx.fillStyle = rgb([78, 54, 36]);
    ctx.fill();
    oval(ctx, ex + turn * 0.9, ey + 0.1, 0.55, 0.6);
    ctx.fillStyle = rgb([14, 10, 10]);
    ctx.fill();
    // Párpado superior y ceja
    ctx.strokeStyle = rgb(OUTLINE);
    ctx.lineWidth = 0.9;
    ctx.beginPath();
    ctx.moveTo(ex - 2.7 * side, ey + 0.3);
    ctx.quadraticCurveTo(ex, ey - 2, ex + 2.7 * side, ey + 0.4);
    ctx.stroke();
    ctx.strokeStyle = rgb(HAIR);
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(ex - 3.2 * side, ey - 2.3);
    ctx.quadraticCurveTo(ex, ey - 4.2, ex + 3.4 * side, ey - 2.7 + side * 0.4);
    ctx.stroke();
  }
  // Nariz: puente sombreado, punta y orificios
  ctx.strokeStyle = rgb(SKIN_DARK, 0.9);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(hx - 1, hy + 1.5);
  ctx.quadraticCurveTo(hx - 1.6, hy + 5, hx - 2.2, hy + 6.4);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(hx - 2.4, hy + 6.8);
  ctx.quadraticCurveTo(hx, hy + 8.2, hx + 2.4, hy + 6.8);
  ctx.stroke();
  ctx.fillStyle = rgb(SKIN_LIGHT, 0.7);
  oval(ctx, hx + 0.4, hy + 5.8, 0.9, 1.4);
  ctx.fill();
  ctx.fillStyle = rgb(OUTLINE, 0.8);
  oval(ctx, hx - 1.2, hy + 7, 0.55, 0.4);
  ctx.fill();
  oval(ctx, hx + 1.2, hy + 7, 0.55, 0.4);
  ctx.fill();
  // Boca: labios con una media sonrisa
  ctx.strokeStyle = rgb([128, 62, 52]);
  ctx.lineWidth = 1.1;
  ctx.beginPath();
  ctx.moveTo(hx - 3.4, hy + 9.6);
  ctx.quadraticCurveTo(hx, hy + 10.6, hx + 3.4, hy + 9.4);
  ctx.stroke();
  ctx.fillStyle = rgb([200, 100, 88], 0.85);
  ctx.beginPath();
  ctx.moveTo(hx - 2.4, hy + 10);
  ctx.quadraticCurveTo(hx, hy + 12, hx + 2.6, hy + 9.9);
  ctx.quadraticCurveTo(hx, hy + 10.7, hx - 2.4, hy + 10);
  ctx.fill();
  // Sombra de barba
  ctx.fillStyle = rgb(HAIR, 0.16);
  oval(ctx, hx, hy + 10.6, 6.4, 3.2);
  ctx.fill();
}

/** Cabeza de perfil mirando a +x. */
function headSide(ctx: Ctx, hx: number, hy: number, sway: number): void {
  // Penacho cae hacia atrás (-x)
  plume(ctx, hx - 1, hy - 14, -1, sway, 8);
  // Cráneo y cara en perfil
  ctx.beginPath();
  ctx.moveTo(hx - 8.4, hy - 6);
  ctx.bezierCurveTo(hx - 10.5, hy + 4, hx - 8, hy + 11.5, hx - 2, hy + 13);
  ctx.quadraticCurveTo(hx + 3.4, hy + 13.4, hx + 6.2, hy + 11.6); // mandíbula y barbilla
  ctx.quadraticCurveTo(hx + 8.2, hy + 10.6, hx + 7.6, hy + 9.2); // labio inferior
  ctx.quadraticCurveTo(hx + 8.8, hy + 8.3, hx + 7.6, hy + 7.4); // labio superior
  ctx.quadraticCurveTo(hx + 8.2, hy + 6.6, hx + 7.4, hy + 6.1);
  ctx.quadraticCurveTo(hx + 11.8, hy + 4.8, hx + 8.8, hy + 2.8); // punta de la nariz
  ctx.quadraticCurveTo(hx + 8.4, hy + 0.6, hx + 7.4, hy - 1.4); // puente y entrecejo
  ctx.quadraticCurveTo(hx + 7.8, hy - 4, hx + 7, hy - 6);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, hx - 10, hx + 11, SKIN_DARK, SKIN_LIGHT), 1.8);
  // Ojo, ceja, boca y oreja
  path(ctx, [[hx + 3.2, hy + 1.6], [hx + 5.2, hy + 0.5], [hx + 6.8, hy + 1.5], [hx + 5.2, hy + 2.7]]);
  ctx.fillStyle = rgb([250, 246, 236]);
  ctx.fill();
  oval(ctx, hx + 5.6, hy + 1.6, 0.95, 1.1);
  ctx.fillStyle = rgb([40, 26, 20]);
  ctx.fill();
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = 0.8;
  ctx.beginPath();
  ctx.moveTo(hx + 2.8, hy + 1.8);
  ctx.quadraticCurveTo(hx + 5, hy - 0.4, hx + 7, hy + 1.3);
  ctx.stroke();
  ctx.strokeStyle = rgb(HAIR);
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(hx + 2.6, hy - 1.4);
  ctx.quadraticCurveTo(hx + 5.4, hy - 3, hx + 7.4, hy - 1.4);
  ctx.stroke();
  ctx.strokeStyle = rgb([128, 62, 52]);
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(hx + 7.6, hy + 8.2);
  ctx.lineTo(hx + 4.6, hy + 8.4);
  ctx.stroke();
  oval(ctx, hx - 2.8, hy + 4.2, 1.9, 3);
  fillStroke(ctx, SKIN_DARK, 1.2);
  // Sombra de barba en la mandíbula
  ctx.fillStyle = rgb(HAIR, 0.16);
  oval(ctx, hx + 2.4, hy + 10.6, 5.2, 2.6);
  ctx.fill();
  // Yelmo de perfil: cúpula, ala sobre la frente y carrillera
  ctx.beginPath();
  ctx.moveTo(hx - 11, hy + 3.4);
  ctx.bezierCurveTo(hx - 12.5, hy - 17, hx + 9, hy - 18, hx + 11.4, hy - 4);
  ctx.quadraticCurveTo(hx + 12, hy - 2.2, hx + 9.4, hy - 2.8);
  ctx.lineTo(hx - 3, hy - 2.8);
  ctx.quadraticCurveTo(hx - 4, hy + 3, hx - 3, hy + 8);
  ctx.lineTo(hx - 8, hy + 8.4);
  ctx.quadraticCurveTo(hx - 11, hy + 7, hx - 11, hy + 3.4);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, hx - 12, hx + 12, ARMOR_DARK, ARMOR_LIGHT), 2);
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = 1.2;
  for (let i = 0; i < 4; i++) {
    ctx.beginPath();
    ctx.moveTo(hx - 5 + i * 3.4, hy - 11.4 + i * 0.9);
    ctx.lineTo(hx - 4 + i * 3.4, hy - 6.8 + i * 0.7);
    ctx.stroke();
  }
  oval(ctx, hx + 0.2, hy - 15.2, 2.5, 2.2);
  fillStroke(ctx, vGradient(ctx, hy - 17.4, hy - 13, ARMOR_LIGHT, ARMOR_DARK), 1.3);
  oval(ctx, hx - 2.6, hy + 2.4, 2.3, 2.7);
  fillStroke(ctx, rGradient(ctx, hx - 2.6, hy + 2.4, 3, ARMOR_LIGHT, ARMOR_DARK), 1.2);
}

/** Cabeza vista por detrás: nuca, cubrenuca y penacho cayendo por la espalda. */
function headBack(ctx: Ctx, hx: number, hy: number, sway: number): void {
  // Cuello y nuca
  ctx.beginPath();
  ctx.moveTo(hx - 8, hy + 2);
  ctx.bezierCurveTo(hx - 8.4, hy + 10, hx - 5, hy + 13, hx, hy + 13);
  ctx.bezierCurveTo(hx + 5, hy + 13, hx + 8.4, hy + 10, hx + 8, hy + 2);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, hx - 8, hx + 8, SKIN_DARK, SKIN), 1.7);
  // Penacho cayendo por detrás
  ctx.beginPath();
  ctx.moveTo(hx, hy - 15);
  ctx.bezierCurveTo(hx - 7, hy - 4, hx - 8 + sway * 0.5, hy + 7, hx - 3 + sway, hy + 17);
  ctx.bezierCurveTo(hx + 1, hy + 8, hx + 5, hy - 2, hx, hy - 15);
  ctx.closePath();
  fillStroke(ctx, vGradient(ctx, hy - 15, hy + 17, [216, 70, 54], RED_DARK), 1.8);
  line(ctx, [240, 120, 96], 0.8, [hx, hy - 12], [hx - 3 + sway * 0.4, hy + 2], [hx - 2 + sway * 0.8, hy + 12]);
  // Yelmo por detrás: cúpula y cubrenuca con láminas
  ctx.beginPath();
  ctx.moveTo(hx - 11, hy + 5);
  ctx.bezierCurveTo(hx - 11.5, hy - 17, hx + 11.5, hy - 17, hx + 11, hy + 5);
  ctx.quadraticCurveTo(hx, hy + 9, hx - 11, hy + 5);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, hx - 11, hx + 11, ARMOR_LIGHT, ARMOR_DARK), 2);
  for (let i = 0; i < 3; i++) {
    ctx.strokeStyle = rgb(ARMOR_DARK);
    ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.moveTo(hx - 10.2 + i * 0.7, hy - 1 + i * 2.4);
    ctx.quadraticCurveTo(hx, hy + 2.6 + i * 2.4, hx + 10.2 - i * 0.7, hy - 1 + i * 2.4);
    ctx.stroke();
  }
  oval(ctx, hx, hy - 12.8, 2.6, 2.3);
  fillStroke(ctx, vGradient(ctx, hy - 15, hy - 10.5, ARMOR_LIGHT, ARMOR_DARK), 1.4);
  for (const side of [-1, 1] as const) {
    oval(ctx, hx + side * 10.6, hy + 1, 2.1, 2.6);
    fillStroke(ctx, rGradient(ctx, hx + side * 10.6, hy + 1, 3, ARMOR_LIGHT, ARMOR_DARK), 1.2);
  }
}

// ---------------------------------------------------------------------------
// Guerrero
// ---------------------------------------------------------------------------

const GROUND = 44;
const THIGH = 11.5;
const SHIN = 11.5;
const UPPER_ARM = 10.5;
const FOREARM = 10;

function boot(ctx: Ctx, ankle: Pt, view: 'front' | 'back' | 'side'): void {
  const [x, y] = ankle;
  if (view === 'side') {
    ctx.beginPath();
    ctx.moveTo(x - 4.2, y - 6);
    ctx.lineTo(x + 3.6, y - 6);
    ctx.lineTo(x + 4, y - 1.5);
    ctx.quadraticCurveTo(x + 11.5, y - 0.5, x + 11, y + 3.6);
    ctx.lineTo(x - 5, y + 3.6);
    ctx.quadraticCurveTo(x - 5.6, y - 1, x - 4.2, y - 6);
    ctx.closePath();
  } else {
    ctx.beginPath();
    ctx.moveTo(x - 4.2, y - 6);
    ctx.lineTo(x + 4.2, y - 6);
    ctx.lineTo(x + 4.4, y - 1);
    ctx.quadraticCurveTo(x + 8, y, x + 7.6, y + 3.8);
    ctx.lineTo(x - 7.6, y + 3.8);
    ctx.quadraticCurveTo(x - 8, y, x - 4.4, y - 1);
    ctx.closePath();
  }
  fillStroke(ctx, vGradient(ctx, y - 6, y + 4, shade(LEATHER, 1.2), LEATHER_DARK), 1.7);
  // Vuelta de la bota
  const w = view === 'side' ? 4.8 : 5.4;
  path(ctx, [[x - w, y - 9.4], [x + w, y - 9.4], [x + w - 0.8, y - 4.4], [x - w + 0.8, y - 4.4]]);
  fillStroke(ctx, vGradient(ctx, y - 9.4, y - 4.4, shade(LEATHER, 1.35), LEATHER), 1.4);
}

export function drawWarrior(ctx: Ctx, cx: number, cy: number, size: number, look: WarriorLook): void {
  const { walkAngle, moving, facing, headTurn, showWeapons, swordPower, now } = look;
  frame(ctx, cx, cy, size, () => {
    const side = facing === 'E' || facing === 'O';
    if (facing === 'O') ctx.scale(-1, 1);

    const breath = moving ? 0 : Math.sin(now * 0.003) * 0.5;
    const bob = moving ? -Math.abs(Math.sin(walkAngle)) * 1.8 : breath;
    const sway = (moving ? Math.sin(walkAngle * 2 - 0.6) * 2.4 : Math.sin(now * 0.004) * 1.2) * 1;

    // Sombra en el suelo
    ctx.fillStyle = 'rgba(0,0,0,0.38)';
    oval(ctx, side ? 1 : 0, 47, side ? 16 : 24, 5.6);
    ctx.fill();

    if (side) drawSide(ctx, { walkAngle, moving, showWeapons, swordPower, now, bob, sway, swordNear: facing === 'E' });
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
  // Al ir de espaldas la pierna que avanza se ve más arriba (se aleja)
  const depth = back ? -1 : 1;
  const hipY = 17 + bob;
  const shoulderY = -10 + bob;

  const legs: Array<{ k: -1 | 1; knee: Pt; ankle: Pt }> = [];
  for (const k of [-1, 1] as const) {
    const a = moving ? walkAngle + (k === 1 ? Math.PI : 0) : 0;
    const swing = Math.sin(a);
    const swingLift = Math.max(0, Math.cos(a)) * 3.4;
    const fx = k * (6.2 + (moving ? 0 : 0.6));
    const fy = GROUND - 4 + depth * swing * 2.4 - (moving ? swingLift : 0);
    const { j, e } = ik(k * 6, hipY, fx, fy, THIGH, SHIN, k === 1 ? -1 : 1);
    legs.push({ k, knee: j, ankle: e });
  }

  // Piernas: muslo de malla, greba de acero, rodillera y bota
  for (const { k, knee, ankle } of legs) {
    capsule(ctx, [k * 6, hipY], knee, 8.2, MAIL);
    capsule(ctx, knee, ankle, 7.2, ARMOR);
    joint(ctx, knee, 4, ARMOR_LIGHT);
    boot(ctx, [ankle[0], ankle[1] + 3], back ? 'back' : 'front');
  }

  // Faldón rojo que se mueve con las piernas
  const skirtSwing = moving ? Math.sin(walkAngle) * 2.2 : 0;
  path(ctx, [[-10.5, 12 + bob], [10.5, 12 + bob], [13 + skirtSwing, 28 + bob], [3, 30 + bob], [0, 26 + bob], [-3, 30 + bob], [-13 + skirtSwing, 28 + bob]]);
  fillStroke(ctx, vGradient(ctx, 12, 30, RED, RED_DARK), 1.8);
  line(ctx, RED_DARK, 0.9, [0, 26 + bob], [0, 14 + bob]);

  // Brazos (detrás del torso si van de espaldas)
  const swordSide: -1 | 1 = back ? 1 : -1; // la mano derecha del guerrero
  const arms = ([-1, 1] as const).map((k) => {
    const a = moving ? walkAngle + (k === -1 ? Math.PI : 0) : 0;
    const sx = k * 13.2;
    const holdingSword = showWeapons && k === swordSide;
    const holdingShield = showWeapons && k !== swordSide;
    let tx = k * 15.4;
    let ty = shoulderY + 20 + (moving ? -Math.sin(a) * 2.2 : 0);
    if (holdingSword) {
      tx = k * 21;
      ty = shoulderY + 11 + (moving ? Math.sin(a) * 1.2 : 0);
    } else if (holdingShield) {
      tx = k * 17.5;
      ty = shoulderY + 14 + (moving ? Math.sin(a) * 1 : 0);
    }
    const { j, e } = ik(sx, shoulderY + 2, tx, ty, UPPER_ARM, FOREARM, k === 1 ? -1 : 1);
    return { k, sx, elbow: j, hand: e, holdingSword, holdingShield };
  });

  const drawArm = (arm: (typeof arms)[number]) => {
    capsule(ctx, [arm.sx, shoulderY + 2], arm.elbow, 7.4, MAIL);
    capsule(ctx, arm.elbow, arm.hand, 6.6, ARMOR);
    joint(ctx, arm.elbow, 3.6, ARMOR_LIGHT);
  };
  const drawHand = (arm: (typeof arms)[number]) => {
    oval(ctx, arm.hand[0], arm.hand[1], 3.8, 3.8);
    fillStroke(ctx, vGradient(ctx, arm.hand[1] - 4, arm.hand[1] + 4, SKIN_LIGHT, SKIN_DARK), 1.5);
  };

  if (back) {
    // De espaldas las armas se sujetan por delante del cuerpo: quedan detrás de brazos y torso
    if (showWeapons) {
      for (const arm of arms) {
        if (arm.holdingShield) shield(ctx, arm.hand[0] + arm.k * 6, arm.hand[1] + 4, 1);
        else if (arm.holdingSword) sword(ctx, arm.hand[0], arm.hand[1] + 1, arm.k * -0.12 + (moving ? Math.sin(walkAngle) * 0.03 : 0), swordPower, now);
      }
    }
    arms.forEach(drawArm);
  }

  // Torso: coraza (peto o espaldar) con bisel y cinturón
  ctx.beginPath();
  ctx.moveTo(-13, shoulderY + 0.5);
  ctx.quadraticCurveTo(0, shoulderY - 3.4, 13, shoulderY + 0.5);
  ctx.bezierCurveTo(13.8, shoulderY + 10, 11, 10 + bob, 10, 14 + bob);
  ctx.lineTo(-10, 14 + bob);
  ctx.bezierCurveTo(-11, 10 + bob, -13.8, shoulderY + 10, -13, shoulderY + 0.5);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -13, 13, ARMOR_LIGHT, ARMOR), 1.9);
  if (!back) {
    ctx.beginPath();
    ctx.moveTo(-9.6, shoulderY + 3);
    ctx.quadraticCurveTo(-10.2, 4, -8, 9 + bob);
    ctx.lineTo(-1, 9 + bob);
    ctx.lineTo(-1, shoulderY + 2);
    ctx.closePath();
    ctx.fillStyle = rgb(ARMOR_LIGHT, 0.32);
    ctx.fill();
    line(ctx, ARMOR_DARK, 1.1, [0, shoulderY + 2], [0, 12 + bob]);
  } else {
    line(ctx, ARMOR_DARK, 1.2, [0, shoulderY + 1], [0, 13 + bob]);
    ctx.strokeStyle = rgb(ARMOR_DARK, 0.8);
    ctx.lineWidth = 1;
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.moveTo(-9, shoulderY + 7 + i * 4.4);
      ctx.quadraticCurveTo(0, shoulderY + 9 + i * 4.4, 9, shoulderY + 7 + i * 4.4);
      ctx.stroke();
    }
  }
  // Cinturón con hebilla
  path(ctx, [[-10.4, 11 + bob], [10.4, 11 + bob], [10.4, 15.4 + bob], [-10.4, 15.4 + bob]]);
  fillStroke(ctx, LEATHER, 1.6);
  if (!back) {
    path(ctx, [[-3.4, 10.4 + bob], [3.4, 10.4 + bob], [3.4, 16 + bob], [-3.4, 16 + bob]]);
    fillStroke(ctx, GOLD, 1.4);
    path(ctx, [[-1.6, 12.2 + bob], [1.6, 12.2 + bob], [1.6, 14.4 + bob], [-1.6, 14.4 + bob]]);
    fillStroke(ctx, LEATHER_DARK, 0.7);
  }

  if (!back) arms.forEach(drawArm);

  // Hombreras: por encima del brazo
  for (const k of [-1, 1] as const) {
    ctx.beginPath();
    ctx.moveTo(k * 9.4, shoulderY - 1.4);
    ctx.quadraticCurveTo(k * 18.4, shoulderY - 6, k * 19.2, shoulderY + 4.4);
    ctx.quadraticCurveTo(k * 15.4, shoulderY + 1.6, k * 10.6, shoulderY + 3.2);
    ctx.closePath();
    fillStroke(ctx, hGradient(ctx, k * 9, k * 19, ARMOR_LIGHT, ARMOR_DARK), 1.7);
  }

  // Cuello y bufanda / cuello de la espalda
  capsule(ctx, [0, shoulderY - 1], [0, shoulderY - 6], 6.4, SKIN);
  ctx.beginPath();
  ctx.moveTo(-8, shoulderY - 1.4);
  ctx.quadraticCurveTo(0, shoulderY + (back ? 3 : 5), 8, shoulderY - 1.4);
  ctx.lineTo(7, shoulderY - 5);
  ctx.quadraticCurveTo(0, shoulderY - (back ? 0.4 : 2), -7, shoulderY - 5);
  ctx.closePath();
  fillStroke(ctx, vGradient(ctx, shoulderY - 5, shoulderY + 4, RED, RED_DARK), 1.5);

  // Manos; de frente las armas van por delante de los hombros (de espaldas ya se dibujaron detrás)
  if (showWeapons) {
    for (const arm of arms) {
      if (back) {
        if (arm.holdingSword) drawHand(arm);
      } else if (arm.holdingShield) {
        drawHand(arm); // la mano queda detrás del escudo
        shield(ctx, arm.hand[0] + arm.k * 6, arm.hand[1] + 4, 1);
      } else if (arm.holdingSword) {
        sword(ctx, arm.hand[0], arm.hand[1] + 1, arm.k * -0.12 + (moving ? Math.sin(walkAngle) * 0.03 : 0), swordPower, now);
        drawHand(arm);
      }
    }
  } else {
    arms.forEach(drawHand);
  }

  // Cabeza
  const hx = back ? 0 : headTurn * 3;
  const hy = -24 + bob;
  if (back) {
    headBack(ctx, hx, hy, sway);
  } else {
    plume(ctx, hx + 1, hy - 14, 1, sway, 8 + sway * 0.3);
    faceFront(ctx, hx, hy, headTurn);
    helmetFront(ctx, hx, hy);
  }
}

// --- De perfil (mirando a +x; para el oeste se refleja el lienzo) --------------

function drawSide(ctx: Ctx, r: RigBase & { swordNear: boolean }): void {
  const { walkAngle, moving, showWeapons, swordPower, now, bob, sway, swordNear } = r;
  const hipY = 17 + bob;
  const shoulderY = -10 + bob;
  const lean = moving ? 1.6 : 0;

  // Piernas: la "cercana" y la "lejana" van en oposición de fase
  const leg = (near: boolean) => {
    const a = moving ? walkAngle + (near ? 0 : Math.PI) : 0;
    const hip: Pt = [lean * 0.3 - 0.5, hipY];
    const fx = hip[0] + (moving ? Math.sin(a) * 8 : near ? 1 : -1);
    const lift = moving ? Math.max(0, Math.cos(a)) * 5.2 : 0;
    const fy = GROUND - 4 - lift;
    const { j, e } = ik(hip[0], hip[1], fx, fy, THIGH, SHIN, -1);
    return { hip, knee: j, ankle: e };
  };
  const farLeg = leg(false);
  const nearLeg = leg(true);

  const arm = (near: boolean) => {
    const a = moving ? walkAngle + (near ? Math.PI : 0) : 0;
    const sh: Pt = [lean + (near ? 0.6 : -0.4), shoulderY + 2.4];
    const holdingSword = showWeapons && (near === swordNear);
    const holdingShield = showWeapons && !holdingSword;
    let tx = sh[0] + (moving ? Math.sin(a) * 7 : 1.2);
    let ty = sh[1] + 19 - (moving ? Math.abs(Math.sin(a)) * 1.6 : 0);
    if (holdingSword) {
      tx = sh[0] + 14.5 + (moving ? Math.sin(a) * 1.4 : 0);
      ty = sh[1] + 9;
    } else if (holdingShield) {
      tx = sh[0] + 7.4;
      ty = sh[1] + 10.4;
    }
    const { j, e } = ik(sh[0], sh[1], tx, ty, UPPER_ARM, FOREARM, 1);
    return { sh, elbow: j, hand: e, holdingSword, holdingShield };
  };
  const farArm = arm(false);
  const nearArm = arm(true);

  const drawLeg = (l: ReturnType<typeof leg>) => {
    capsule(ctx, l.hip, l.knee, 8.2, MAIL);
    capsule(ctx, l.knee, l.ankle, 7, ARMOR);
    joint(ctx, l.knee, 4, ARMOR_LIGHT);
    boot(ctx, [l.ankle[0], l.ankle[1] + 3], 'side');
  };
  const drawArm = (a: ReturnType<typeof arm>) => {
    capsule(ctx, a.sh, a.elbow, 7.2, MAIL);
    capsule(ctx, a.elbow, a.hand, 6.4, ARMOR);
    joint(ctx, a.elbow, 3.5, ARMOR_LIGHT);
  };
  const drawHand = (a: ReturnType<typeof arm>) => {
    oval(ctx, a.hand[0], a.hand[1], 3.6, 3.6);
    fillStroke(ctx, vGradient(ctx, a.hand[1] - 4, a.hand[1] + 4, SKIN_LIGHT, SKIN_DARK), 1.5);
  };

  // Cosas del lado lejano, detrás del cuerpo
  drawLeg(farLeg);
  drawArm(farArm);
  if (farArm.holdingSword) sword(ctx, farArm.hand[0], farArm.hand[1] + 1, 0.16, swordPower, now);
  drawHand(farArm);
  if (farArm.holdingShield) shield(ctx, farArm.hand[0] + 5, farArm.hand[1] + 4, 0.34);

  // Faldón y torso de perfil
  const skirtSwing = moving ? Math.sin(walkAngle) * 3 : 0;
  path(ctx, [[-6.4 + lean * 0.3, 12 + bob], [6.4 + lean * 0.3, 12 + bob], [9 + skirtSwing, 28 + bob], [-0.5, 30 + bob], [-9 + skirtSwing * 0.4, 28 + bob]]);
  fillStroke(ctx, vGradient(ctx, 12, 30, RED, RED_DARK), 1.7);

  ctx.beginPath();
  ctx.moveTo(-6.4 + lean * 0.5, shoulderY + 0.5);
  ctx.bezierCurveTo(-3, shoulderY - 2.4, 5.6 + lean, shoulderY - 2, 7.2 + lean, shoulderY + 2);
  ctx.bezierCurveTo(8.2 + lean * 0.5, 4, 7.2, 10 + bob, 6.4, 14 + bob);
  ctx.lineTo(-6.4, 14 + bob);
  ctx.bezierCurveTo(-7.4, 8 + bob, -7.4, shoulderY + 6, -6.4 + lean * 0.5, shoulderY + 0.5);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -7, 8, ARMOR_DARK, ARMOR_LIGHT), 1.8);
  path(ctx, [[-6.6, 11 + bob], [6.6, 11 + bob], [6.6, 15.4 + bob], [-6.6, 15.4 + bob]]);
  fillStroke(ctx, LEATHER, 1.5);

  // Pierna y brazo cercanos, por delante
  drawLeg(nearLeg);
  drawArm(nearArm);

  // Hombrera
  ctx.beginPath();
  ctx.moveTo(-4.6 + lean, shoulderY - 1.6);
  ctx.quadraticCurveTo(5.4 + lean, shoulderY - 5.4, 8.2 + lean, shoulderY + 3);
  ctx.quadraticCurveTo(3 + lean, shoulderY + 1.4, -3.2 + lean, shoulderY + 3.6);
  ctx.closePath();
  fillStroke(ctx, hGradient(ctx, -4, 9, ARMOR_DARK, ARMOR_LIGHT), 1.6);

  // Cuello y bufanda
  capsule(ctx, [lean, shoulderY - 1], [lean + 0.6, shoulderY - 6], 5.8, SKIN);
  ctx.beginPath();
  ctx.moveTo(-4.4 + lean, shoulderY - 1.4);
  ctx.quadraticCurveTo(lean + 1, shoulderY + 4.6, 6 + lean, shoulderY - 1.4);
  ctx.lineTo(5 + lean, shoulderY - 5);
  ctx.quadraticCurveTo(lean, shoulderY - 2.4, -3.6 + lean, shoulderY - 5);
  ctx.closePath();
  fillStroke(ctx, vGradient(ctx, shoulderY - 5, shoulderY + 4, RED, RED_DARK), 1.4);

  // Armas del lado cercano, por delante del hombro
  if (nearArm.holdingSword) sword(ctx, nearArm.hand[0], nearArm.hand[1] + 1, 0.16 + (moving ? Math.sin(walkAngle) * 0.03 : 0), swordPower, now);
  drawHand(nearArm);
  if (nearArm.holdingShield) shield(ctx, nearArm.hand[0] + 5, nearArm.hand[1] + 3, 0.5);

  headSide(ctx, 1.4 + lean, -24 + bob, sway);
}
