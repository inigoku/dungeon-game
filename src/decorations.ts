/** Decoraciones del dungeon: antorchas, sangre, huellas, fuente, polvo, telarañas y escalera. */
import { Cell, type Direction } from './models';
import { seeded } from './rng';
import { circle, clamp, ellipse, line, rgb, type Ctx, type RGB } from './gfx';
import { ticks } from './time';

export interface Footprint {
  relX: number;
  relY: number;
  time: number;
}

/** Huellas húmedas de los monstruos: se desvanecen en 15 segundos. */
export function drawWetFootprints(ctx: Ctx, x: number, y: number, footprints: Footprint[]): void {
  const now = ticks();
  for (const fp of footprints) {
    const age = now - fp.time;
    if (age > 15000) continue;
    const alpha = Math.trunc(120 * (1 - age / 15000)) / 255;
    ellipse(ctx, [20, 40, 40], x + fp.relX - 7, y + fp.relY - 5, 14, 10, 0, alpha);
  }
}

/** Manchas de sangre cerca de la salida (distancia 1-10), deterministas por celda. */
export function drawBloodStains(
  ctx: Ctx,
  cellSize: number,
  boardRow: number,
  boardCol: number,
  x: number,
  y: number,
  brightnessFactor: number,
  exitPosition: readonly [number, number],
): void {
  const bloodFactor = 1 - 0.5 * (1 - brightnessFactor);
  const distance = Math.abs(exitPosition[0] - boardRow) + Math.abs(exitPosition[1] - boardCol);
  if (distance < 1 || distance > 10) return;

  const rnd = seeded(boardRow * 100000 + boardCol);
  const probability = 1 - ((distance - 1) / 9) * 0.7;
  if (rnd.random() > probability) return;

  const scale = (c: readonly [number, number, number]): RGB => [Math.trunc(c[0] * bloodFactor), Math.trunc(c[1] * bloodFactor), Math.trunc(c[2] * bloodFactor)];
  const bloodColors = [scale([80, 0, 0]), scale([100, 10, 10]), scale([70, 5, 5])];

  const numStains = rnd.randint(2, 5);
  for (let i = 0; i < numStains; i++) {
    const stainX = x + Math.trunc(rnd.uniform(0.2, 0.8) * cellSize);
    const stainY = y + Math.trunc(rnd.uniform(0.2, 0.8) * cellSize);
    const size = rnd.randint(4, 12);
    const color = rnd.choice(bloodColors);
    const numCircles = rnd.randint(2, 4);
    for (let j = 0; j < numCircles; j++) {
      const half = Math.floor(size / 2);
      const offsetX = rnd.randint(-half, half);
      const offsetY = rnd.randint(-half, half);
      const circleSize = rnd.randint(half, size);
      circle(ctx, color, stainX + offsetX, stainY + offsetY, circleSize);
    }
  }
}

function drawSingleTorch(ctx: Ctx, x: number, y: number, size: number, flicker: number): void {
  const handleWidth = Math.max(3, Math.floor(size / 4));
  ctx.fillStyle = rgb([101, 67, 33]);
  ctx.fillRect(x - Math.floor(handleWidth / 2), y, handleWidth, size);

  const flameRadius = Math.trunc(size * flicker * 0.6);
  circle(ctx, [255, 140, 0], x, y, flameRadius);
  circle(ctx, [255, 220, 100], x, y, Math.trunc(flameRadius * 0.5));
}

/** Antorchas animadas en las paredes sin salida (y que no den al barranco). */
export function drawTorches(
  ctx: Ctx,
  cellSize: number,
  boardRow: number,
  boardCol: number,
  x: number,
  y: number,
  cell: Cell,
  numTorches: number,
  barrancoDirs: Iterable<Direction> = [],
): void {
  const seed = boardRow * 100000 + boardCol;
  const rnd = seeded(seed);
  const flicker = Math.abs(Math.sin(ticks() * 0.003 + seed)) * 0.3 + 0.7;
  const torchSize = Math.max(8, Math.trunc(cellSize * 0.15));
  const wallThickness = Math.trunc(cellSize * 0.28);
  const half = Math.floor(wallThickness / 2);
  const barranco = new Set<Direction>(barrancoDirs);

  const positions: Array<[number, number]> = [];
  if (!cell.exits.has('N') && !barranco.has('N')) positions.push([x + Math.floor(cellSize / 2) + rnd.randint(-20, 20), y + half]);
  if (!cell.exits.has('S') && !barranco.has('S')) positions.push([x + Math.floor(cellSize / 2) + rnd.randint(-20, 20), y + cellSize - half]);
  if (!cell.exits.has('E') && !barranco.has('E')) positions.push([x + cellSize - half, y + Math.floor(cellSize / 2) + rnd.randint(-20, 20)]);
  if (!cell.exits.has('O') && !barranco.has('O')) positions.push([x + half, y + Math.floor(cellSize / 2) + rnd.randint(-20, 20)]);

  for (let i = 0; i < Math.min(numTorches, positions.length); i++) {
    drawSingleTorch(ctx, positions[i][0], positions[i][1], torchSize, flicker);
  }
}

/** Fuente decorativa en la esquina superior izquierda de la celda de inicio. */
export function drawFountain(ctx: Ctx, cellSize: number, x: number, y: number, bf = 1): void {
  const fountainSize = Math.max(20, Math.trunc(cellSize * 0.3));
  const fx = x + Math.floor(fountainSize / 2) + 5;
  const fy = y + Math.floor(fountainSize / 2) + 5;
  const left = fx - Math.floor(fountainSize / 2);
  const top = fy - Math.floor(fountainSize / 2);

  const baseVal = Math.trunc(100 * bf);
  ctx.fillStyle = rgb([baseVal, baseVal, baseVal]);
  ctx.fillRect(left, top, fountainSize, fountainSize);

  const borderVal = Math.trunc(150 * bf);
  ctx.strokeStyle = rgb([borderVal, borderVal, borderVal]);
  ctx.lineWidth = 2;
  ctx.strokeRect(left + 1, top + 1, fountainSize - 2, fountainSize - 2);

  const waterRadius = Math.floor(fountainSize / 3);
  circle(ctx, [Math.trunc(100 * bf), Math.trunc(180 * bf), Math.trunc(255 * bf)], fx, fy, waterRadius);

  const t = ticks();
  for (let i = 0; i < 3; i++) {
    const progress = ((t + i * 800) % 2400) / 2400;
    const radius = Math.trunc(waterRadius * progress);
    if (radius > 0) circle(ctx, [Math.trunc(150 * bf), Math.trunc(220 * bf), Math.trunc(255 * bf)], fx, fy, radius, 1);
  }

  const shineX = fx - Math.floor(waterRadius / 3);
  const shineY = fy - Math.floor(waterRadius / 3);
  const shineRadius = Math.max(2, Math.trunc(waterRadius * 0.2));
  const pulse = (Math.sin(t * 0.005) + 1) * 0.5;
  const shineAlpha = Math.trunc((100 + 100 * pulse) * bf);
  circle(ctx, [255, 255, 255], shineX, shineY, shineRadius, 0, shineAlpha / 255);

  circle(ctx, [Math.trunc(150 * bf), Math.trunc(200 * bf), Math.trunc(255 * bf)], fx, fy, waterRadius, 2);
}

/** Partículas de polvo flotando en el aire de la celda de inicio. */
export function drawDustParticles(ctx: Ctx, cellSize: number, x: number, y: number, boardRow: number, boardCol: number, bf = 1): void {
  const t = ticks();
  const rnd = seeded(boardRow * 100000 + boardCol);
  for (let i = 0; i < 40; i++) {
    const startX = rnd.randint(0, cellSize);
    const startY = rnd.randint(0, cellSize);
    const offsetX = Math.sin(t * 0.0005 + i) * 15;
    const speedY = rnd.uniform(0.01, 0.03);
    const offsetY = (t * speedY) % cellSize;
    const mod = (v: number) => ((v % cellSize) + cellSize) % cellSize;
    const px = x + Math.trunc(mod(startX + offsetX));
    const py = y + Math.trunc(mod(startY - offsetY));
    const size = rnd.randint(1, 2);
    const pulse = (Math.sin(t * 0.003 + i) + 1) * 0.5;
    const alpha = Math.trunc((50 + 100 * pulse) * bf);
    // Con size = 1 el radio es 0 y no se ve nada (igual que en pygame)
    if (alpha > 0 && size >= 2) circle(ctx, [255, 255, 200], px + 1, py + 1, 1, 0, alpha / 255);
  }
}

/** Telarañas en las esquinas de las habitaciones (30 % de probabilidad). */
export function drawCobwebs(ctx: Ctx, cellSize: number, x: number, y: number, boardRow: number, boardCol: number, bf = 1): void {
  const rnd = seeded(boardRow * 100000 + boardCol);
  if (rnd.random() > 0.3) return;

  const corners: Array<[number, number, number, number]> = [
    [0, 0, 1, 1],
    [cellSize, 0, -1, 1],
    [0, cellSize, 1, -1],
    [cellSize, cellSize, -1, -1],
  ];
  const numWebs = rnd.randint(1, 3);
  const selected = rnd.sample(corners, numWebs);

  const alpha = Math.trunc(80 * bf);
  if (alpha < 5) return;
  const color: RGB = [220, 220, 220];
  const a = alpha / 255;

  for (const [cxOff, cyOff, dx, dy] of selected) {
    const cx = x + cxOff;
    const cy = y + cyOff;
    const size = rnd.randint(Math.trunc(cellSize * 0.15), Math.trunc(cellSize * 0.25));
    const numRadials = rnd.randint(3, 5);
    const points: Array<[number, number]> = [];
    for (let i = 0; i < numRadials; i++) {
      const angle = (i / (numRadials - 1)) * (Math.PI / 2);
      const px = cx + Math.cos(angle) * size * dx;
      const py = cy + Math.sin(angle) * size * dy;
      points.push([px, py]);
      line(ctx, color, cx, cy, px, py, 1, a);
    }
    const numCross = rnd.randint(2, 4);
    for (let j = 1; j <= numCross; j++) {
      const factor = j / (numCross + 1);
      for (let k = 0; k < points.length - 1; k++) {
        const [p1x, p1y] = points[k];
        const [p2x, p2y] = points[k + 1];
        line(ctx, color, cx + (p1x - cx) * factor, cy + (p1y - cy) * factor, cx + (p2x - cx) * factor, cy + (p2y - cy) * factor, 1, a);
      }
    }
  }
}

/** Escalera de caracol de la celda de salida. */
export function drawSpiralStairs(ctx: Ctx, cellSize: number, x: number, y: number): void {
  const stairsSize = Math.max(20, Math.trunc(cellSize * 0.35));
  const sx = x + cellSize - Math.floor(stairsSize / 2) - 5;
  const sy = y + cellSize - Math.floor(stairsSize / 2) - 5;
  const postRadius = Math.max(3, Math.floor(stairsSize / 8));
  circle(ctx, [100, 80, 60], sx, sy, postRadius);

  const numSteps = 8;
  for (let i = 0; i < numSteps; i++) {
    const angle = (i / numSteps) * 2 * Math.PI;
    const radius = Math.floor(stairsSize / 2);
    const stepX = sx + Math.trunc(radius * Math.cos(angle));
    const stepY = sy + Math.trunc(radius * Math.sin(angle));
    const b = 120 + Math.trunc(30 * (i / numSteps));
    const innerX = sx + Math.trunc(radius * 0.3 * Math.cos(angle));
    const innerY = sy + Math.trunc(radius * 0.3 * Math.sin(angle));
    line(ctx, [clamp(b, 0, 255), b - 20, b - 40], innerX, innerY, stepX, stepY, 3);
  }
  circle(ctx, [80, 60, 40], sx, sy, postRadius, 1);
}
