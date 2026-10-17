/**
 * Escenas de los pensamientos y de la pantalla de título, dibujadas con código al estilo de dibujo animado
 * oscuro del juego. El personaje (su cara y su pose) sale de la tira de expresiones de su clase, así que las
 * escenas valen para cualquier personaje, incluidos los que se puedan personalizar más adelante.
 */
import { createCanvas, context2d, type Canvas, type Ctx } from './gfx';
import { seeded, type Rng } from './rng';
import { drawDeepOne } from './sprites';

export type SceneName = 'antorcha' | 'sangre' | 'espada' | 'profundo' | 'losa' | 'titulo';
/** Arma que sale en la escena del poder: la de la clase. */
export type WeaponKind = 'espada' | 'daga' | 'arco';

/** Expresiones de la tira `caras_<clase>.png`: una celda de 256×256 por cada una. */
export const FACE = { guardia: 0, grito: 1, susto: 2, asombro: 3, poder: 4, mirar: 5, ladoE: 6, ladoO: 7 } as const;
const FACE_CELL = 256;
const INK = '#140c07';

type Pt = [number, number];

const mix = (a: readonly number[], b: readonly number[], t: number): string =>
  `rgb(${Math.round(a[0] + (b[0] - a[0]) * t)},${Math.round(a[1] + (b[1] - a[1]) * t)},${Math.round(a[2] + (b[2] - a[2]) * t)})`;

function roundRect(ctx: Ctx, x: number, y: number, w: number, h: number, r: number): void {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function inked(ctx: Ctx, fill: string | CanvasGradient, width = 6): void {
  ctx.fillStyle = fill;
  ctx.fill();
  ctx.lineWidth = width;
  ctx.strokeStyle = INK;
  ctx.lineJoin = 'round';
  ctx.stroke();
}

/** Muro de bloques de piedra iluminado por una antorcha que está en `light`. */
function wall(ctx: Ctx, S: number, light: Pt, rnd: Rng): void {
  ctx.fillStyle = INK;
  ctx.fillRect(0, 0, S, S);
  const dark = [30, 21, 15];
  const lit = [132, 98, 62];
  let row = 0;
  for (let y = -20; y < S * 0.82; y += 128, row++) {
    let x = -rnd.randint(0, 120) - (row % 2) * 90;
    while (x < S) {
      const w = rnd.randint(150, 250);
      const cx = x + w / 2;
      const cy = y + 64;
      const t = Math.max(0, 1 - Math.hypot(cx - light[0], cy - light[1]) / (S * 0.95)) ** 1.5;
      roundRect(ctx, x + 3, y + 3, w - 6, 122, 16);
      inked(ctx, mix(dark, lit, t * (0.8 + rnd.random() * 0.4)), 5);
      // Reflejo en el canto superior y alguna grieta
      ctx.strokeStyle = `rgba(255,214,150,${0.05 + t * 0.2})`;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(x + 20, y + 14);
      ctx.lineTo(x + w - 24, y + 14);
      ctx.stroke();
      if (rnd.random() < 0.3) {
        ctx.strokeStyle = 'rgba(0,0,0,0.5)';
        ctx.lineWidth = 3;
        ctx.beginPath();
        const sx = x + rnd.randint(30, w - 30);
        ctx.moveTo(sx, y + 20);
        ctx.lineTo(sx + rnd.randint(-20, 20), y + 60);
        ctx.lineTo(sx + rnd.randint(-20, 20), y + 100);
        ctx.stroke();
      }
      x += w;
    }
  }
}

function floor(ctx: Ctx, S: number, light: Pt, rnd: Rng): void {
  const top = S * 0.8;
  ctx.fillStyle = INK;
  ctx.fillRect(0, top - 6, S, S - top + 6);
  let y = top;
  let h = 46;
  let row = 0;
  while (y < S) {
    let x = -(row % 2) * 90 - rnd.randint(0, 80);
    while (x < S) {
      const w = rnd.randint(150, 240);
      const t = Math.max(0, 1 - Math.hypot(x + w / 2 - light[0], y - light[1]) / (S * 1.1)) ** 1.4;
      roundRect(ctx, x + 3, y + 3, w - 6, h - 6, 12);
      inked(ctx, mix([42, 30, 20], [118, 84, 52], t * (0.7 + rnd.random() * 0.5)), 5);
      x += w;
    }
    y += h;
    h = Math.round(h * 1.28);
    row++;
  }
}

function flame(ctx: Ctx, x: number, y: number, s: number): void {
  const layers: Array<[string, number]> = [['#ff7a14', 1], ['#ffb62a', 0.74], ['#fff0a0', 0.42]];
  for (const [color, k] of layers) {
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.bezierCurveTo(x - 62 * s * k, y - 30 * s * k, x - 70 * s * k, y - 120 * s * k, x - 8 * s * k, y - 190 * s * k);
    ctx.bezierCurveTo(x + 4 * s * k, y - 120 * s * k, x + 40 * s * k, y - 130 * s * k, x + 46 * s * k, y - 90 * s * k);
    ctx.bezierCurveTo(x + 76 * s * k, y - 50 * s * k, x + 58 * s * k, y - 8 * s * k, x, y);
    ctx.closePath();
    inked(ctx, color, k === 1 ? 6 : 0.01);
  }
}

function torch(ctx: Ctx, x: number, y: number): void {
  // Soporte y copa
  roundRect(ctx, x - 16, y + 40, 32, 120, 10);
  inked(ctx, '#6a5646', 6);
  ctx.beginPath();
  ctx.moveTo(x - 46, y + 2);
  ctx.lineTo(x + 46, y + 2);
  ctx.lineTo(x + 26, y + 58);
  ctx.lineTo(x - 26, y + 58);
  ctx.closePath();
  inked(ctx, '#85705a', 6);
  flame(ctx, x, y + 6, 1);
}

function glow(ctx: Ctx, x: number, y: number, r: number, color: string): void {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, color);
  g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g;
  ctx.fillRect(x - r, y - r, r * 2, r * 2);
}

function vignette(ctx: Ctx, S: number): void {
  const g = ctx.createRadialGradient(S / 2, S * 0.5, S * 0.3, S / 2, S * 0.5, S * 0.78);
  g.addColorStop(0, 'rgba(0,0,0,0)');
  g.addColorStop(1, 'rgba(0,0,0,0.7)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, S, S);
}

function bloodSplat(ctx: Ctx, x: number, y: number, r: number, rnd: Rng): void {
  ctx.fillStyle = 'rgb(150,18,20)';
  ctx.strokeStyle = 'rgb(70,6,8)';
  ctx.lineWidth = 3;
  // Mancha irregular y redondeada
  const n = 14;
  const pts: Pt[] = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const rr = r * (i % 3 === 0 ? rnd.uniform(1.0, 1.25) : rnd.uniform(0.7, 0.95));
    pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr * 0.85]);
  }
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const [px, py] = pts[i];
    const [qx, qy] = pts[(i + 1) % n];
    const mx = (px + qx) / 2;
    const my = (py + qy) / 2;
    if (i === 0) ctx.moveTo(mx, my);
    else ctx.quadraticCurveTo(px, py, mx, my);
  }
  const [fx, fy] = pts[0];
  ctx.quadraticCurveTo(fx, fy, (fx + pts[1][0]) / 2, (fy + pts[1][1]) / 2);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  // Gotas alrededor y chorreones
  for (let i = 0; i < 6; i++) {
    const a = rnd.uniform(0, Math.PI * 2);
    ctx.beginPath();
    ctx.arc(x + Math.cos(a) * r * rnd.uniform(1.3, 1.9), y + Math.sin(a) * r * rnd.uniform(1.1, 1.6), rnd.uniform(4, 9), 0, Math.PI * 2);
    ctx.fill();
  }
  for (let i = rnd.randint(1, 3); i > 0; i--) {
    const dx = x + rnd.uniform(-r * 0.5, r * 0.5);
    const len = rnd.uniform(r * 0.9, r * 2.4);
    roundRect(ctx, dx - 7, y + r * 0.3, 14, len, 7);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(dx, y + r * 0.3 + len, 9, 0, Math.PI * 2);
    ctx.fill();
  }
}

function bloodPool(ctx: Ctx, x: number, y: number, rx: number, ry: number): void {
  ctx.beginPath();
  ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
  inked(ctx, 'rgb(128,14,18)', 5);
  ctx.beginPath();
  ctx.ellipse(x - rx * 0.25, y - ry * 0.3, rx * 0.35, ry * 0.2, 0, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(255,120,120,0.4)';
  ctx.fill();
}

/** Estela de piedra con el relieve de un ser con tentáculos y alas, y runas. */
function stele(ctx: Ctx, x: number, y: number, w: number, h: number, rnd: Rng): void {
  const g = ctx.createLinearGradient(x, y, x + w, y);
  g.addColorStop(0, 'rgb(92,96,80)');
  g.addColorStop(1, 'rgb(58,60,50)');
  ctx.beginPath();
  ctx.moveTo(x, y + h);
  ctx.lineTo(x, y + 90);
  ctx.quadraticCurveTo(x, y, x + 90, y);
  ctx.lineTo(x + w - 90, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + 90);
  ctx.lineTo(x + w, y + h);
  ctx.closePath();
  inked(ctx, g, 8);
  // Basa
  roundRect(ctx, x - 40, y + h - 30, w + 80, 60, 10);
  inked(ctx, 'rgb(74,76,64)', 7);

  const cx = x + w / 2;
  const hy = y + h * 0.3;
  // Alas
  for (const side of [-1, 1] as const) {
    ctx.beginPath();
    ctx.moveTo(cx + side * 70, hy + 10);
    ctx.quadraticCurveTo(cx + side * 190, hy - 130, cx + side * 215, hy - 40);
    ctx.quadraticCurveTo(cx + side * 190, hy - 20, cx + side * 185, hy + 40);
    ctx.quadraticCurveTo(cx + side * 150, hy + 20, cx + side * 140, hy + 70);
    ctx.quadraticCurveTo(cx + side * 110, hy + 40, cx + side * 80, hy + 90);
    ctx.closePath();
    inked(ctx, 'rgb(58,66,42)', 6);
  }
  // Brazos y garras
  for (const side of [-1, 1] as const) {
    ctx.beginPath();
    ctx.moveTo(cx + side * 80, hy + 120);
    ctx.quadraticCurveTo(cx + side * 190, hy + 190, cx + side * 150, hy + 320);
    ctx.lineTo(cx + side * 90, hy + 320);
    ctx.quadraticCurveTo(cx + side * 130, hy + 220, cx + side * 60, hy + 180);
    ctx.closePath();
    inked(ctx, 'rgb(78,86,48)', 6);
    for (let k = 0; k < 3; k++) {
      ctx.beginPath();
      ctx.moveTo(cx + side * (150 - k * 22), hy + 316);
      ctx.lineTo(cx + side * (158 - k * 22), hy + 360);
      ctx.lineTo(cx + side * (138 - k * 22), hy + 320);
      ctx.closePath();
      inked(ctx, 'rgb(70,78,44)', 4);
    }
  }
  // Tentáculos
  for (let i = 0; i < 6; i++) {
    const tx = cx - 75 + i * 30;
    ctx.strokeStyle = INK;
    ctx.lineCap = 'round';
    ctx.lineWidth = 34;
    ctx.beginPath();
    ctx.moveTo(tx, hy + 80);
    ctx.bezierCurveTo(tx + (i % 2 ? 24 : -24), hy + 150, tx + (i % 2 ? -26 : 26), hy + 220, tx + (i - 2.5) * 6, hy + 300);
    ctx.stroke();
    ctx.strokeStyle = 'rgb(88,98,50)';
    ctx.lineWidth = 24;
    ctx.stroke();
  }
  // Cabeza
  ctx.beginPath();
  ctx.ellipse(cx, hy, 110, 100, 0, 0, Math.PI * 2);
  inked(ctx, 'rgb(90,100,52)', 7);
  ctx.beginPath();
  ctx.ellipse(cx - 28, hy - 40, 50, 28, -0.4, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(150,164,90,0.45)';
  ctx.fill();
  // Ojos naranjas con ceño
  for (const side of [-1, 1] as const) {
    ctx.beginPath();
    ctx.moveTo(cx + side * 18, hy + 6);
    ctx.quadraticCurveTo(cx + side * 56, hy - 22, cx + side * 88, hy - 8);
    ctx.quadraticCurveTo(cx + side * 60, hy + 30, cx + side * 18, hy + 6);
    ctx.closePath();
    inked(ctx, '#ff9a14', 5);
    ctx.beginPath();
    ctx.ellipse(cx + side * 56, hy + 4, 9, 14, 0, 0, Math.PI * 2);
    ctx.fillStyle = INK;
    ctx.fill();
    ctx.strokeStyle = INK;
    ctx.lineWidth = 9;
    ctx.beginPath();
    ctx.moveTo(cx + side * 14, hy - 20);
    ctx.lineTo(cx + side * 96, hy - 36 + (side < 0 ? 0 : 0));
    ctx.stroke();
  }
  // Runas
  ctx.strokeStyle = 'rgb(40,42,34)';
  ctx.lineWidth = 7;
  ctx.lineCap = 'round';
  for (let row = 0; row < 2; row++) {
    let gx = x + 50;
    while (gx < x + w - 60) {
      const gy = y + h * 0.8 + row * 56;
      ctx.beginPath();
      const k = rnd.randint(0, 3);
      if (k === 0) { ctx.moveTo(gx, gy); ctx.lineTo(gx + 26, gy + 34); ctx.moveTo(gx + 26, gy); ctx.lineTo(gx, gy + 34); }
      else if (k === 1) { ctx.moveTo(gx, gy); ctx.lineTo(gx, gy + 34); ctx.lineTo(gx + 24, gy + 34); ctx.moveTo(gx, gy + 14); ctx.lineTo(gx + 22, gy); }
      else if (k === 2) { ctx.moveTo(gx, gy + 34); ctx.lineTo(gx + 14, gy); ctx.lineTo(gx + 28, gy + 34); }
      else { ctx.moveTo(gx, gy + 17); ctx.lineTo(gx + 28, gy + 17); ctx.moveTo(gx + 14, gy); ctx.lineTo(gx + 14, gy + 34); }
      ctx.stroke();
      gx += rnd.randint(46, 62);
    }
  }
}

/** Pozo de piedra del que sale una mano con el arma de la clase. */
function well(ctx: Ctx, cx: number, cy: number): void {
  // Cuerpo del pozo
  ctx.beginPath();
  ctx.moveTo(cx - 190, cy);
  ctx.lineTo(cx - 190, cy + 190);
  ctx.quadraticCurveTo(cx, cy + 270, cx + 190, cy + 190);
  ctx.lineTo(cx + 190, cy);
  ctx.closePath();
  inked(ctx, 'rgb(120,106,88)', 7);
  ctx.strokeStyle = 'rgba(20,12,7,0.7)';
  ctx.lineWidth = 5;
  for (let r = 1; r < 3; r++) {
    ctx.beginPath();
    ctx.moveTo(cx - 190, cy + r * 62);
    ctx.quadraticCurveTo(cx, cy + r * 62 + 42, cx + 190, cy + r * 62);
    ctx.stroke();
  }
  for (let i = -3; i <= 3; i++) {
    ctx.beginPath();
    ctx.moveTo(cx + i * 52, cy + 40);
    ctx.lineTo(cx + i * 52, cy + 100);
    ctx.stroke();
  }
  // Brocal y agua
  ctx.beginPath();
  ctx.ellipse(cx, cy, 200, 66, 0, 0, Math.PI * 2);
  inked(ctx, 'rgb(150,134,112)', 7);
  ctx.beginPath();
  ctx.ellipse(cx, cy + 4, 160, 46, 0, 0, Math.PI * 2);
  inked(ctx, 'rgb(44,128,176)', 5);
  ctx.beginPath();
  ctx.ellipse(cx - 40, cy - 6, 70, 12, 0, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(190,235,255,0.5)';
  ctx.fill();
}

/** Brazo que sale del agua sosteniendo el arma, con resplandor. `hand` es el puño. */
function risingHand(ctx: Ctx, wx: number, wy: number, kind: WeaponKind): void {
  const hx = wx + 14;
  const hy = wy - 250;
  // Antebrazo y manga
  ctx.beginPath();
  ctx.moveTo(wx - 34, wy + 6);
  ctx.quadraticCurveTo(wx - 30, wy - 120, hx - 30, hy + 30);
  ctx.lineTo(hx + 30, hy + 30);
  ctx.quadraticCurveTo(wx + 34, wy - 120, wx + 40, wy + 6);
  ctx.closePath();
  inked(ctx, 'rgb(244,190,136)', 6);
  roundRect(ctx, hx - 40, hy + 40, 80, 52, 14);
  inked(ctx, 'rgb(236,232,214)', 6);
  // Arma, con halo
  glow(ctx, hx, hy - 70, 330, 'rgba(160,230,255,0.75)');
  ctx.strokeStyle = 'rgba(220,250,255,0.9)';
  ctx.lineWidth = 6;
  ctx.lineCap = 'round';
  for (let i = 0; i < 14; i++) {
    const a = (i / 14) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(hx + Math.cos(a) * 190, hy - 70 + Math.sin(a) * 190);
    ctx.lineTo(hx + Math.cos(a) * 230, hy - 70 + Math.sin(a) * 230);
    ctx.stroke();
  }
  weapon(ctx, hx, hy, kind);
  // Puño por delante
  roundRect(ctx, hx - 46, hy - 10, 92, 62, 26);
  inked(ctx, 'rgb(244,190,136)', 6);
  for (let k = 0; k < 3; k++) {
    ctx.beginPath();
    ctx.moveTo(hx - 30 + k * 30, hy + 4);
    ctx.lineTo(hx - 30 + k * 30, hy + 36);
    ctx.strokeStyle = 'rgba(80,30,10,0.55)';
    ctx.lineWidth = 4;
    ctx.stroke();
  }
}

function weapon(ctx: Ctx, hx: number, hy: number, kind: WeaponKind): void {
  if (kind === 'espada') {
    ctx.beginPath();
    ctx.moveTo(hx - 22, hy);
    ctx.lineTo(hx - 22, hy - 250);
    ctx.lineTo(hx, hy - 330);
    ctx.lineTo(hx + 22, hy - 250);
    ctx.lineTo(hx + 22, hy);
    ctx.closePath();
    inked(ctx, 'rgb(214,236,248)', 6);
    ctx.fillStyle = 'rgba(120,170,200,0.7)';
    ctx.fillRect(hx - 5, hy - 250, 10, 240);
    roundRect(ctx, hx - 76, hy - 12, 152, 26, 12);
    inked(ctx, 'rgb(216,160,60)', 6);
    roundRect(ctx, hx - 16, hy + 40, 32, 70, 10);
    inked(ctx, 'rgb(150,90,40)', 6);
  } else if (kind === 'daga') {
    ctx.beginPath();
    ctx.moveTo(hx - 18, hy);
    ctx.bezierCurveTo(hx - 70, hy - 90, hx - 60, hy - 220, hx + 40, hy - 290);
    ctx.bezierCurveTo(hx + 30, hy - 200, hx + 36, hy - 90, hx + 20, hy);
    ctx.closePath();
    inked(ctx, 'rgb(206,222,232)', 6);
    ctx.strokeStyle = INK;
    ctx.lineWidth = 5;
    for (let k = 0; k < 5; k++) {
      ctx.beginPath();
      ctx.moveTo(hx - 56 + k * 4, hy - 70 - k * 36);
      ctx.lineTo(hx - 74 + k * 4, hy - 56 - k * 36);
      ctx.lineTo(hx - 52 + k * 4, hy - 100 - k * 36);
      ctx.stroke();
    }
    roundRect(ctx, hx - 40, hy - 10, 80, 22, 10);
    inked(ctx, 'rgb(90,70,56)', 6);
  } else {
    // Arco con la cuerda y una flecha de luz
    ctx.beginPath();
    ctx.moveTo(hx - 10, hy - 330);
    ctx.bezierCurveTo(hx - 140, hy - 240, hx - 140, hy - 70, hx - 10, hy + 20);
    ctx.lineWidth = 22;
    ctx.strokeStyle = INK;
    ctx.stroke();
    ctx.lineWidth = 12;
    ctx.strokeStyle = 'rgb(214,160,70)';
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(hx - 10, hy - 330);
    ctx.lineTo(hx - 10, hy + 20);
    ctx.lineWidth = 4;
    ctx.strokeStyle = 'rgb(255,250,220)';
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(hx - 10, hy - 200);
    ctx.lineTo(hx + 10, hy - 340);
    ctx.lineTo(hx + 30, hy - 200);
    ctx.closePath();
    inked(ctx, 'rgb(255,240,160)', 5);
  }
}

/** Dibuja la expresión `slot` del personaje con su pie en `bottom`; `lightX` es de dónde llega la luz. */
function character(ctx: Ctx, faces: HTMLImageElement, slot: number, cx: number, bottom: number, height: number, lightX: number, flip = false): { headX: number; top: number } {
  const k = height / FACE_CELL;
  const tmp = createCanvas(FACE_CELL, FACE_CELL);
  const t = context2d(tmp);
  t.drawImage(faces, slot * FACE_CELL, 0, FACE_CELL, FACE_CELL, 0, 0, FACE_CELL, FACE_CELL);
  // Luz cálida del lado de la antorcha y sombra en el otro, solo sobre el personaje
  t.globalCompositeOperation = 'source-atop';
  const toLeft = lightX < cx;
  const g = t.createLinearGradient(toLeft ? 0 : FACE_CELL, 0, toLeft ? FACE_CELL : 0, 0);
  g.addColorStop(0, 'rgba(255,170,70,0.32)');
  g.addColorStop(1, 'rgba(10,0,0,0.38)');
  t.fillStyle = g;
  t.fillRect(0, 0, FACE_CELL, FACE_CELL);

  const w = FACE_CELL * k;
  ctx.fillStyle = 'rgba(0,0,0,0.4)';
  ctx.beginPath();
  ctx.ellipse(cx, bottom - 6, w * 0.34, 22, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.save();
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.translate(cx, bottom);
  if (flip) ctx.scale(-1, 1);
  ctx.drawImage(tmp, -w / 2, -height, w, height);
  ctx.restore();

  // Dónde está la cabeza: la primera fila opaca y el centro de las filas de arriba
  const data = t.getImageData(0, 0, FACE_CELL, FACE_CELL).data;
  let topRow = FACE_CELL;
  let sumX = 0;
  let count = 0;
  for (let y = 0; y < FACE_CELL && count < 400; y++) {
    for (let x = 0; x < FACE_CELL; x++) {
      if (data[(y * FACE_CELL + x) * 4 + 3] > 40) {
        if (topRow === FACE_CELL) topRow = y;
        if (y < topRow + 30) {
          sumX += x;
          count++;
        }
      }
    }
  }
  const px = count ? sumX / count : FACE_CELL / 2;
  const headX = cx + (flip ? -1 : 1) * (px - FACE_CELL / 2) * k;
  return { headX, top: bottom - height + topRow * k };
}

/** Exclamación roja con gotas de sudor sobre la cabeza: el personaje se sobresalta. */
function startle(ctx: Ctx, x: number, y: number): void {
  roundRect(ctx, x - 16, y - 120, 32, 78, 14);
  inked(ctx, '#e0281c', 6);
  ctx.beginPath();
  ctx.arc(x, y - 18, 18, 0, Math.PI * 2);
  inked(ctx, '#e0281c', 6);
  for (const [dx, dy] of [[-70, -30], [-90, 6], [70, -26]] as const) {
    ctx.beginPath();
    ctx.moveTo(x + dx, y + dy - 22);
    ctx.quadraticCurveTo(x + dx + 20, y + dy + 6, x + dx, y + dy + 14);
    ctx.quadraticCurveTo(x + dx - 20, y + dy + 6, x + dx, y + dy - 22);
    inked(ctx, '#8fd8ff', 4);
  }
}

/** Pantalla de título: atardecer, la boca de la cueva con ojos rojos y el personaje con el arma lista. */
function title(ctx: Ctx, S: number, faces: HTMLImageElement | null, rnd: Rng): void {
  const sky = ctx.createLinearGradient(0, 0, 0, S);
  sky.addColorStop(0, '#f0a020');
  sky.addColorStop(0.55, '#ffc94a');
  sky.addColorStop(1, '#f6a834');
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, S, S);
  // Nubes
  ctx.fillStyle = 'rgba(255,224,150,0.7)';
  for (const [x, y, r] of [[110, 330, 70], [200, 320, 90], [300, 340, 64], [760, 280, 60], [850, 270, 84], [940, 300, 56]]) {
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }
  // Suelo
  ctx.beginPath();
  ctx.moveTo(0, 800);
  ctx.quadraticCurveTo(300, 760, 620, 810);
  ctx.quadraticCurveTo(860, 840, S, 800);
  ctx.lineTo(S, S);
  ctx.lineTo(0, S);
  ctx.closePath();
  inked(ctx, '#b86a2a', 7);
  // Cueva
  ctx.beginPath();
  ctx.moveTo(430, 840);
  ctx.bezierCurveTo(400, 400, 640, 330, 800, 360);
  ctx.bezierCurveTo(960, 390, 1040, 600, 1010, 840);
  ctx.closePath();
  inked(ctx, 'rgb(104,108,92)', 9);
  ctx.beginPath();
  ctx.moveTo(500, 840);
  ctx.bezierCurveTo(490, 480, 650, 430, 780, 450);
  ctx.bezierCurveTo(910, 470, 950, 620, 940, 840);
  ctx.closePath();
  ctx.fillStyle = 'rgb(26,14,16)';
  ctx.fill();
  ctx.stroke();
  // Bloques de la boca
  for (let i = 0; i < 9; i++) {
    const a = Math.PI + (i / 8) * Math.PI * 0.95;
    ctx.beginPath();
    ctx.ellipse(720 + Math.cos(a) * 270, 640 + Math.sin(a) * 250, 52, 38, a, 0, Math.PI * 2);
    inked(ctx, `rgb(${96 + rnd.randint(0, 24)},${100 + rnd.randint(0, 20)},${88 + rnd.randint(0, 16)})`, 6);
  }
  // Ojos rojos con colmillos
  for (const [x, y, s] of [[640, 640, 1], [770, 560, 0.9], [840, 700, 1.1], [700, 760, 0.8], [890, 600, 0.7]] as const) {
    for (const side of [-1, 1] as const) {
      ctx.beginPath();
      ctx.moveTo(x + side * 8 * s, y);
      ctx.quadraticCurveTo(x + side * 36 * s, y - 22 * s, x + side * 62 * s, y - 6 * s);
      ctx.quadraticCurveTo(x + side * 40 * s, y + 20 * s, x + side * 8 * s, y);
      ctx.closePath();
      ctx.fillStyle = '#e8281c';
      ctx.fill();
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#6a0a0a';
      ctx.stroke();
    }
    ctx.fillStyle = '#f0e6d0';
    for (let k = -2; k <= 2; k++) {
      ctx.beginPath();
      ctx.moveTo(x + k * 14 * s - 6 * s, y + 34 * s);
      ctx.lineTo(x + k * 14 * s, y + 62 * s);
      ctx.lineTo(x + k * 14 * s + 6 * s, y + 34 * s);
      ctx.closePath();
      ctx.fill();
    }
  }
  // Hierba
  ctx.fillStyle = '#3c6a28';
  for (const [x, y] of [[60, 880], [330, 930], [980, 890], [560, 960]]) {
    for (let k = -1; k <= 1; k++) {
      ctx.beginPath();
      ctx.moveTo(x + k * 18 - 10, y);
      ctx.lineTo(x + k * 26, y - 70 + Math.abs(k) * 20);
      ctx.lineTo(x + k * 18 + 10, y);
      ctx.closePath();
      inked(ctx, '#4a7c30', 4);
    }
  }
  if (faces) character(ctx, faces, FACE.guardia, 300, S - 40, 700, 900);
  // Textos
  ctx.textAlign = 'center';
  ctx.lineJoin = 'round';
  const text = (s: string, y: number, px: number, lw: number): void => {
    const font = (size: number): string => `900 ${size}px "Arial Black", Impact, "Helvetica Neue", Arial, sans-serif`;
    ctx.font = font(px);
    // Si no cabe a lo ancho, se reduce el tamaño (la fuente cambia según el dispositivo)
    const fit = Math.min(1, (S * 0.9) / ctx.measureText(s).width);
    px = Math.floor(px * fit);
    lw = Math.round(lw * fit);
    ctx.font = font(px);
    ctx.lineWidth = lw;
    ctx.strokeStyle = '#3a1a06';
    ctx.strokeText(s, S / 2, y);
    const g = ctx.createLinearGradient(0, y - px, 0, y);
    g.addColorStop(0, '#fff07a');
    g.addColorStop(1, '#ffb814');
    ctx.fillStyle = g;
    ctx.fillText(s, S / 2, y);
  };
  text('¿TE ATREVES A ENTRAR EN LA...', 120, 58, 14);
  text('MAZMORRA?', 250, 170, 26);
  text('Pulsa una tecla para entrar', S - 36, 54, 12);
}

/** Dibuja una escena cuadrada de `S` píxeles. Sin la tira de expresiones del personaje se queda el decorado. */
export function renderScene(name: SceneName, faces: HTMLImageElement | null, weaponKind: WeaponKind, S = 1024): Canvas {
  const canvas = createCanvas(S, S);
  const ctx = context2d(canvas);
  const rnd = seeded(name.length * 7919 + 13);
  if (name === 'titulo') {
    title(ctx, S, faces, rnd);
    return canvas;
  }
  const torchAt: Pt = name === 'espada' ? [860, 190] : name === 'losa' ? [190, 220] : [150, 200];
  wall(ctx, S, torchAt, rnd);
  floor(ctx, S, torchAt, rnd);
  glow(ctx, torchAt[0], torchAt[1], 640, 'rgba(255,160,50,0.42)');
  const slot = { antorcha: FACE.ladoO, sangre: FACE.ladoO, espada: FACE.poder, profundo: FACE.grito, losa: FACE.asombro }[name];

  if (name === 'antorcha') {
    torch(ctx, torchAt[0], torchAt[1]);
    if (faces) character(ctx, faces, slot, 560, S + 260, 980, torchAt[0]);
  } else if (name === 'sangre') {
    for (const [x, y, r] of [[120, 300, 70], [330, 180, 54], [210, 470, 60], [470, 360, 40]] as const) bloodSplat(ctx, x, y, r, rnd);
    for (const [x, y, rx, ry] of [[260, 900, 190, 44], [620, 960, 150, 34], [90, 980, 120, 30]] as const) bloodPool(ctx, x, y, rx, ry);
    torch(ctx, torchAt[0] + 380, torchAt[1] - 30);
    if (faces) {
      const head = character(ctx, faces, slot, 640, S + 260, 980, torchAt[0] + 380);
      startle(ctx, head.headX, head.top - 10);
    }
  } else if (name === 'espada') {
    torch(ctx, torchAt[0], torchAt[1]);
    well(ctx, 300, 740);
    risingHand(ctx, 300, 740, weaponKind);
    if (faces) character(ctx, faces, slot, 680, S + 240, 960, 300);
  } else if (name === 'profundo') {
    torch(ctx, torchAt[0], torchAt[1]);
    bloodSplat(ctx, 560, 150, 60, rnd);
    drawDeepOne(ctx, 360, 600, 760, { walkPhase: 0, roaring: true, roarT: 400, alerted: true, dead: false, now: 1200 });
    if (faces) character(ctx, faces, slot, 700, S + 280, 1000, torchAt[0]);
  } else {
    torch(ctx, torchAt[0], torchAt[1]);
    stele(ctx, 560, 110, 380, 830, rnd);
    if (faces) character(ctx, faces, slot, 330, S + 260, 980, torchAt[0]);
  }
  vignette(ctx, S);
  return canvas;
}
