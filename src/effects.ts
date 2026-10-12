/** Efectos visuales del dungeon: líneas quebradas, suelo rugoso, piedras en paredes y acantilado. */
import { Cell, type Direction } from './models';
import { seeded } from './rng';
import { clamp, ellipse, fillRect, line, rgb, type Ctx, type RGB } from './gfx';


export const CLIFF_BASE_COLOR: RGB = [34, 24, 38];

type Rect = [number, number, number, number];

export function drawBrokenLine(
  ctx: Ctx,
  color: RGB,
  start: readonly [number, number],
  end: readonly [number, number],
  width: number,
  boardRow: number,
  boardCol: number,
  lineId: number,
): void {
  const c: RGB = [clamp(Math.trunc(color[0]), 0, 255), clamp(Math.trunc(color[1]), 0, 255), clamp(Math.trunc(color[2]), 0, 255)];
  const rnd = seeded(boardRow * 100000 + boardCol * 100 + lineId);
  const [x1, y1] = start;
  const [x2, y2] = end;
  const length = Math.hypot(x2 - x1, y2 - y1);

  if (length < 5) {
    line(ctx, c, x1, y1, x2, y2, width);
    return;
  }

  const numSegments = Math.max(3, Math.trunc(length / 10));
  const dx = x2 - x1;
  const dy = y2 - y1;
  let perpX = -dy;
  let perpY = dx;
  const perpLen = Math.hypot(perpX, perpY);
  if (perpLen > 0) {
    perpX /= perpLen;
    perpY /= perpLen;
  }

  ctx.strokeStyle = rgb(c);
  ctx.lineWidth = width;
  ctx.lineCap = 'butt';
  ctx.lineJoin = 'round';
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  for (let i = 1; i < numSegments; i++) {
    const t = i / numSegments;
    const offset = rnd.uniform(-3, 3);
    const px = x1 + t * dx + perpX * offset;
    const py = y1 + t * dy + perpY * offset;
    ctx.lineTo(Math.trunc(px), Math.trunc(py));
  }
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

/** Suelo con textura rugosa (ruido determinista por celda). */
export function drawRoughFloor(
  ctx: Ctx,
  x: number,
  y: number,
  width: number,
  height: number,
  color: RGB,
  boardRow: number,
  boardCol: number,
): void {
  fillRect(ctx, color, x, y, width, height);
  // Si el color es muy oscuro no se dibujan detalles
  if (color[0] < 20 || width < 2 || height < 2) return;

  const rnd = seeded(boardRow * 100000 + boardCol);
  const numSpots = Math.trunc(width * height * 0.08);
  for (let i = 0; i < numSpots; i++) {
    const sx = x + rnd.randint(0, width - 2);
    const sy = y + rnd.randint(0, height - 2);
    const variation = rnd.randint(-15, 15);
    ctx.fillStyle = rgb([clamp(color[0] + variation, 0, 255), clamp(color[1] + variation, 0, 255), clamp(color[2] + variation, 0, 255)]);
    ctx.fillRect(sx, sy, 2, 2);
  }
}

/**
 * Textura de piedra en las zonas de pared de una celda; deja hueco donde hay
 * salida. Si un lado da al barranco, la esquina de marco de puerta que toca
 * esa esquina se omite (la rellena drawBarrancoDoorCorners).
 */
export function drawStoneInWalls(
  ctx: Ctx,
  cellSize: number,
  boardRow: number,
  boardCol: number,
  x: number,
  y: number,
  cell: Cell,
  wallBrightness: number,
  barrancoDirs: Iterable<Direction> | null = null,
): void {
  const rnd = seeded(boardRow * 100000 + boardCol + 7);
  const size = cellSize;
  const wallThickness = Math.max(6, Math.trunc(size * 0.28));
  const gapW = Math.max(8, Math.trunc(size * 0.36));
  const gapH = Math.max(8, Math.trunc(size * 0.36));
  const barranco = new Set<Direction>(barrancoDirs ?? []);
  const exits = cell.exits;

  const allRects: Rect[] = [];

  if (exits.has('N')) {
    const leftW = Math.floor((size - gapW) / 2);
    if (!barranco.has('O')) allRects.push([x, y, leftW, wallThickness]);
    if (!barranco.has('E')) allRects.push([x + leftW + gapW, y, leftW, wallThickness]);
  } else {
    allRects.push([x, y, size, wallThickness]);
  }

  if (exits.has('S')) {
    const leftW = Math.floor((size - gapW) / 2);
    if (!barranco.has('O')) allRects.push([x, y + size - wallThickness, leftW, wallThickness]);
    if (!barranco.has('E')) allRects.push([x + leftW + gapW, y + size - wallThickness, leftW, wallThickness]);
  } else {
    allRects.push([x, y + size - wallThickness, size, wallThickness]);
  }

  if (exits.has('O')) {
    const topH = Math.floor((size - gapH) / 2);
    if (!barranco.has('N')) allRects.push([x, y, wallThickness, topH]);
    if (!barranco.has('S')) allRects.push([x, y + topH + gapH, wallThickness, topH]);
  } else {
    allRects.push([x, y, wallThickness, size]);
  }

  if (exits.has('E')) {
    const topH = Math.floor((size - gapH) / 2);
    if (!barranco.has('N')) allRects.push([x + size - wallThickness, y, wallThickness, topH]);
    if (!barranco.has('S')) allRects.push([x + size - wallThickness, y + topH + gapH, wallThickness, topH]);
  } else {
    allRects.push([x + size - wallThickness, y, wallThickness, size]);
  }

  const wb = Math.trunc(wallBrightness);
  const shadeOf = (shade: number): RGB => [clamp(wb + shade, 0, 255), clamp(wb + shade, 0, 255), clamp(wb + shade, 0, 255)];

  for (const [rx, ry, rw, rh] of allRects) {
    const area = Math.max(1, rw * rh);
    const num = rnd.randint(Math.max(12, Math.floor(area / 80)), Math.max(24, Math.floor(area / 40)));
    for (let i = 0; i < num; i++) {
      const w = rnd.randint(Math.max(2, Math.trunc(rw * 0.08)), Math.max(4, Math.trunc(rw * 0.5)));
      const h = rnd.randint(Math.max(2, Math.trunc(rh * 0.06)), Math.max(4, Math.trunc(rh * 0.45)));
      const sx = rx + rnd.randint(0, Math.max(0, rw - w));
      const sy = ry + rnd.randint(0, Math.max(0, rh - h));
      const stone = shadeOf(rnd.randint(-40, 60));
      ellipse(ctx, stone, sx, sy, w, h);
      if (rnd.random() < 0.9) {
        const border: RGB = [Math.max(0, stone[0] - 55), Math.max(0, stone[1] - 55), Math.max(0, stone[2] - 55)];
        ellipse(ctx, border, sx, sy, w, h, 1);
      }
    }
  }

  // Grietas
  const mortar: RGB = [25, 25, 25];
  for (let i = rnd.randint(6, 14); i > 0; i--) {
    const [rx, ry, rw, rh] = rnd.choice(allRects);
    const x1 = rx + rnd.randint(0, Math.max(0, rw - 1));
    const y1 = ry + rnd.randint(0, Math.max(0, rh - 1));
    const x2 = rx + rnd.randint(0, Math.max(0, rw - 1));
    const y2 = ry + rnd.randint(0, Math.max(0, rh - 1));
    line(ctx, mortar, x1, y1, x2, y2, 2);
  }
}

/** Rellena un rectángulo con la textura de roca del acantilado. */
function drawCliffTexture(ctx: Ctx, rx: number, ry: number, rw: number, rh: number, seed: number): void {
  if (rw <= 0 || rh <= 0) return;
  const rnd = seeded(seed);
  fillRect(ctx, CLIFF_BASE_COLOR, rx, ry, rw, rh);
  for (let i = rnd.randint(6, 12); i > 0; i--) {
    const w = rnd.randint(Math.max(2, Math.trunc(rw * 0.1)), Math.max(4, Math.trunc(rw * 0.4)));
    const h = rnd.randint(Math.max(2, Math.trunc(rh * 0.1)), Math.max(4, Math.trunc(rh * 0.4)));
    const sx = rx + rnd.randint(0, Math.max(0, rw - w));
    const sy = ry + rnd.randint(0, Math.max(0, rh - h));
    const shade = rnd.randint(-20, 25);
    ellipse(ctx, [clamp(CLIFF_BASE_COLOR[0] + shade, 0, 255), clamp(CLIFF_BASE_COLOR[1] + shade, 0, 255), clamp(CLIFF_BASE_COLOR[2] + shade, 0, 255)], sx, sy, w, h);
  }
}

/** Esquinas de puerta que dan al barranco, rellenas con roca del acantilado. */
export function drawBarrancoDoorCorners(
  ctx: Ctx,
  cellSize: number,
  boardRow: number,
  boardCol: number,
  x: number,
  y: number,
  cell: Cell,
  barrancoDirs: Iterable<Direction>,
): void {
  const barranco = new Set<Direction>(barrancoDirs);
  if (barranco.size === 0) return;

  const size = cellSize;
  const wallThickness = Math.max(6, Math.trunc(size * 0.28));
  const gapW = Math.max(8, Math.trunc(size * 0.36));
  const gapH = Math.max(8, Math.trunc(size * 0.36));
  const corners: Rect[] = [];

  if (cell.exits.has('N')) {
    const leftW = Math.floor((size - gapW) / 2);
    if (barranco.has('O')) corners.push([x, y, leftW, wallThickness]);
    if (barranco.has('E')) corners.push([x + leftW + gapW, y, leftW, wallThickness]);
  }
  if (cell.exits.has('S')) {
    const leftW = Math.floor((size - gapW) / 2);
    if (barranco.has('O')) corners.push([x, y + size - wallThickness, leftW, wallThickness]);
    if (barranco.has('E')) corners.push([x + leftW + gapW, y + size - wallThickness, leftW, wallThickness]);
  }
  if (cell.exits.has('O')) {
    const topH = Math.floor((size - gapH) / 2);
    if (barranco.has('N')) corners.push([x, y, wallThickness, topH]);
    if (barranco.has('S')) corners.push([x, y + topH + gapH, wallThickness, topH]);
  }
  if (cell.exits.has('E')) {
    const topH = Math.floor((size - gapH) / 2);
    if (barranco.has('N')) corners.push([x + size - wallThickness, y, wallThickness, topH]);
    if (barranco.has('S')) corners.push([x + size - wallThickness, y + topH + gapH, wallThickness, topH]);
  }

  const seed = boardRow * 100000 + boardCol;
  corners.forEach(([fx, fy, fw, fh], i) => drawCliffTexture(ctx, fx, fy, fw, fh, seed + 500 + i));
}

/** Borde de acantilado infranqueable en el lado de la celda que da al barranco. */
export function drawCliffSide(
  ctx: Ctx,
  cellSize: number,
  x: number,
  y: number,
  direction: Direction,
  boardRow: number,
  boardCol: number,
): void {
  const size = cellSize;
  const thickness = Math.max(10, Math.trunc(size * 0.34));
  let rect: Rect;
  if (direction === 'N') rect = [0, 0, size, thickness];
  else if (direction === 'S') rect = [0, size - thickness, size, thickness];
  else if (direction === 'O') rect = [0, 0, thickness, size];
  else rect = [size - thickness, 0, thickness, size];

  const dirOffset = { N: 1, S: 2, E: 3, O: 4 }[direction];
  const seed = boardRow * 100000 + boardCol + dirOffset;
  drawCliffTexture(ctx, x + rect[0], y + rect[1], rect[2], rect[3], seed);
}
