/** Efectos visuales del dungeon: líneas quebradas, suelo rugoso, piedras en paredes y acantilado. */
import { Cell, type Direction } from './models';
import { seeded } from './rng';
import { clamp, ellipse, fillRect, line, rgb, type Ctx, type RGB } from './gfx';


export const CLIFF_BASE_COLOR: RGB = [34, 24, 38];

type Rect = [number, number, number, number];

/** Estilo de pared: losas de piedra labrada o roca natural de cueva. */
export type WallStyle = 'losas' | 'cueva';

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

/** Rectángulos de pared de una celda; dejan hueco donde hay salida (y no llegan al barranco). */
function wallRects(cellSize: number, x: number, y: number, cell: Cell, barranco: ReadonlySet<Direction>): Rect[] {
  const size = cellSize;
  const wallThickness = Math.max(6, Math.trunc(size * 0.28));
  const gapW = Math.max(8, Math.trunc(size * 0.36));
  const gapH = Math.max(8, Math.trunc(size * 0.36));
  const exits = cell.exits;
  const rects: Rect[] = [];

  if (exits.has('N')) {
    const leftW = Math.floor((size - gapW) / 2);
    if (!barranco.has('O')) rects.push([x, y, leftW, wallThickness]);
    if (!barranco.has('E')) rects.push([x + leftW + gapW, y, leftW, wallThickness]);
  } else {
    rects.push([x, y, size, wallThickness]);
  }

  if (exits.has('S')) {
    const leftW = Math.floor((size - gapW) / 2);
    if (!barranco.has('O')) rects.push([x, y + size - wallThickness, leftW, wallThickness]);
    if (!barranco.has('E')) rects.push([x + leftW + gapW, y + size - wallThickness, leftW, wallThickness]);
  } else {
    rects.push([x, y + size - wallThickness, size, wallThickness]);
  }

  if (exits.has('O')) {
    const topH = Math.floor((size - gapH) / 2);
    if (!barranco.has('N')) rects.push([x, y, wallThickness, topH]);
    if (!barranco.has('S')) rects.push([x, y + topH + gapH, wallThickness, topH]);
  } else {
    rects.push([x, y, wallThickness, size]);
  }

  if (exits.has('E')) {
    const topH = Math.floor((size - gapH) / 2);
    if (!barranco.has('N')) rects.push([x + size - wallThickness, y, wallThickness, topH]);
    if (!barranco.has('S')) rects.push([x + size - wallThickness, y + topH + gapH, wallThickness, topH]);
  } else {
    rects.push([x + size - wallThickness, y, wallThickness, size]);
  }
  return rects;
}

/** Color de piedra con un ligero tinte cálido a partir de un nivel de gris. */
function stoneColor(level: number): RGB {
  return [clamp(level + 5, 0, 255), clamp(level + 3, 0, 255), clamp(level - 3, 0, 255)];
}

/** Bloque de sillar: relleno con ligero degradado, esquinas romas, relieve de luz arriba-izquierda y ruido. */
function drawStoneBlock(ctx: Ctx, rnd: ReturnType<typeof seeded>, bx: number, by: number, bw: number, bh: number, level: number): void {
  if (bw < 2 || bh < 2) return;
  const r = Math.min(2.2, bw / 3, bh / 3);
  ctx.beginPath();
  ctx.moveTo(bx + r, by);
  ctx.arcTo(bx + bw, by, bx + bw, by + bh, r);
  ctx.arcTo(bx + bw, by + bh, bx, by + bh, r);
  ctx.arcTo(bx, by + bh, bx, by, r);
  ctx.arcTo(bx, by, bx + bw, by, r);
  ctx.closePath();
  const lit = stoneColor(level + 9);
  const dark = stoneColor(level - 9);
  const grad = ctx.createLinearGradient(bx, by, bx + bw * 0.6, by + bh);
  grad.addColorStop(0, rgb(lit));
  grad.addColorStop(1, rgb(dark));
  ctx.fillStyle = grad;
  ctx.fill();

  // Relieve: filo claro arriba y a la izquierda, sombra abajo y a la derecha
  ctx.lineWidth = 1;
  ctx.strokeStyle = rgb(stoneColor(level + 30), 0.55);
  ctx.beginPath();
  ctx.moveTo(bx + 0.5, by + bh - 1);
  ctx.lineTo(bx + 0.5, by + 0.5);
  ctx.lineTo(bx + bw - 1, by + 0.5);
  ctx.stroke();
  ctx.strokeStyle = rgb(stoneColor(level - 32), 0.6);
  ctx.beginPath();
  ctx.moveTo(bx + bw - 0.5, by + 1);
  ctx.lineTo(bx + bw - 0.5, by + bh - 0.5);
  ctx.lineTo(bx + 1, by + bh - 0.5);
  ctx.stroke();

  // Grano de la piedra
  const specks = Math.trunc((bw * bh) / 38);
  for (let i = 0; i < specks; i++) {
    const v = rnd.randint(-16, 16);
    ctx.fillStyle = rgb(stoneColor(level + v), 0.7);
    ctx.fillRect(bx + 1 + rnd.random() * Math.max(0, bw - 3), by + 1 + rnd.random() * Math.max(0, bh - 3), 1, 1);
  }
  // Alguna picadura
  if (rnd.random() < 0.3) {
    ctx.fillStyle = rgb(stoneColor(level - 22), 0.65);
    ctx.beginPath();
    ctx.ellipse(bx + bw * rnd.uniform(0.25, 0.75), by + bh * rnd.uniform(0.3, 0.7), rnd.uniform(0.8, 2), rnd.uniform(0.6, 1.4), 0, 0, Math.PI * 2);
    ctx.fill();
  }
}

/** Roca natural: masa oscura con peñascos irregulares, de formas angulosas y sin hiladas. */
function drawCaveRock(ctx: Ctx, rnd: ReturnType<typeof seeded>, rect: Rect, level: number): void {
  const [rx, ry, rw, rh] = rect;
  fillRect(ctx, rockColor(level * 0.42 - 4), rx, ry, rw, rh);
  ctx.save();
  ctx.beginPath();
  ctx.rect(rx, ry, rw, rh);
  ctx.clip();
  const count = Math.max(6, Math.trunc((rw * rh) / 110));
  for (let i = 0; i < count; i++) {
    const cx = rx + rnd.random() * rw;
    const cy = ry + rnd.random() * rh;
    drawBoulder(ctx, rnd, cx, cy, rnd.uniform(5, 12), level + rnd.randint(-18, 24));
  }
  // Grietas oscuras entre los peñascos
  for (let i = Math.trunc(count / 5); i > 0; i--) {
    let cx = rx + rnd.random() * rw;
    let cy = ry + rnd.random() * rh;
    ctx.strokeStyle = rgb(rockColor(level * 0.15 - 4), 0.8);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    for (let k = rnd.randint(2, 4); k > 0; k--) {
      cx += rnd.randint(-5, 5);
      cy += rnd.randint(-5, 5);
      ctx.lineTo(cx, cy);
    }
    ctx.stroke();
  }
  ctx.restore();
}

/** Color de roca con un tinte pardo, algo más cálido y apagado que la piedra labrada. */
function rockColor(level: number): RGB {
  return [clamp(level + 7, 0, 255), clamp(level + 1, 0, 255), clamp(level - 7, 0, 255)];
}

/** Peñasco poligonal: cara en sombra, cara iluminada arriba-izquierda, filo claro y contorno oscuro. */
function drawBoulder(ctx: Ctx, rnd: ReturnType<typeof seeded>, cx: number, cy: number, radius: number, level: number): void {
  const n = rnd.randint(5, 7);
  const pts: [number, number][] = [];
  const phase = rnd.random() * Math.PI * 2;
  const squash = rnd.uniform(0.7, 1.15);
  for (let i = 0; i < n; i++) {
    const ang = phase + (i / n) * Math.PI * 2;
    const r = radius * rnd.uniform(0.62, 1.12);
    pts.push([cx + Math.cos(ang) * r, cy + Math.sin(ang) * r * squash]);
  }
  const trace = (dx = 0, dy = 0, k = 1) => {
    ctx.beginPath();
    pts.forEach(([px, py], i) => {
      const x = cx + (px - cx) * k + dx;
      const y = cy + (py - cy) * k + dy;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
  };
  trace();
  ctx.fillStyle = rgb(rockColor(level - 10));
  ctx.fill();
  // Cara iluminada: el mismo polígono más pequeño y desplazado hacia la luz
  trace(-radius * 0.12, -radius * 0.14, 0.72);
  ctx.fillStyle = rgb(rockColor(level + 8));
  ctx.fill();
  trace(-radius * 0.2, -radius * 0.24, 0.4);
  ctx.fillStyle = rgb(rockColor(level + 20), 0.7);
  ctx.fill();
  trace();
  ctx.strokeStyle = rgb(rockColor(level - 38), 0.9);
  ctx.lineWidth = 1;
  ctx.stroke();
}

/** Sillería en aparejo a soga: hiladas a lo largo del muro, con las juntas desfasadas y bloques de largo irregular. */
function drawMasonry(ctx: Ctx, rnd: ReturnType<typeof seeded>, rect: Rect, courseH: number, level: number, long: [number, number], spread: [number, number]): void {
  const [rx, ry, rw, rh] = rect;
  const horizontal = rw >= rh;
  const along = horizontal ? rw : rh;
  const across = horizontal ? rh : rw;
  const courses = Math.max(1, Math.round(across / courseH));
  const ch = across / courses;

  // Mortero: fondo oscuro al que las piedras dejan una junta
  fillRect(ctx, stoneColor(level * 0.35 - 6), rx, ry, rw, rh);
  const joint = 1.2;
  for (let c = 0; c < courses; c++) {
    let p = -rnd.randint(0, Math.round(ch * 2));
    while (p < along) {
      const len = rnd.randint(Math.round(ch * long[0]), Math.round(ch * long[1]));
      const a = Math.max(0, p);
      const b = Math.min(along, p + len);
      p += len;
      if (b - a < 3) continue;
      const tone = level + rnd.randint(spread[0], spread[1]);
      const u0 = a + (a === 0 ? 0 : joint / 2);
      const u1 = b - (b === along ? 0 : joint / 2);
      const v0 = c * ch + joint / 2;
      const v1 = (c + 1) * ch - joint / 2;
      if (horizontal) drawStoneBlock(ctx, rnd, rx + u0, ry + v0, u1 - u0, v1 - v0, tone);
      else drawStoneBlock(ctx, rnd, rx + v0, ry + u0, v1 - v0, u1 - u0, tone);
    }
  }
}

/**
 * Paredes de sillería en las zonas de pared de una celda; deja hueco donde hay
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
  style: WallStyle = 'losas',
): void {
  const rnd = seeded(boardRow * 100000 + boardCol + 7);
  const allRects = wallRects(cellSize, x, y, cell, new Set<Direction>(barrancoDirs ?? []));
  const level = Math.trunc(wallBrightness);
  // Losas grandes y casi regulares (dos hiladas por muro) o roca natural sin hiladas
  const courseH = Math.max(8, cellSize * 0.135);

  // Primero los muros verticales y encima los horizontales, para que las esquinas encajen
  const ordered = [...allRects.filter(([, , w, h]) => w < h), ...allRects.filter(([, , w, h]) => w >= h)];
  for (const rect of ordered) {
    if (style === 'cueva') drawCaveRock(ctx, rnd, rect, level);
    else drawMasonry(ctx, rnd, rect, courseH, level, [1.5, 2.5], [-8, 14]);
  }
  if (style === 'cueva') return;

  // Grietas finas que cruzan alguna junta
  const crack = stoneColor(level * 0.25 - 4);
  for (let i = rnd.randint(3, 7); i > 0; i--) {
    const [rx, ry, rw, rh] = rnd.choice(allRects);
    const x1 = rx + rnd.randint(0, Math.max(0, rw - 1));
    const y1 = ry + rnd.randint(0, Math.max(0, rh - 1));
    ctx.strokeStyle = rgb(crack, 0.85);
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    let cx = x1;
    let cy = y1;
    for (let k = rnd.randint(2, 4); k > 0; k--) {
      cx = clamp(cx + rnd.randint(-5, 5), rx, rx + rw);
      cy = clamp(cy + rnd.randint(-5, 5), ry, ry + rh);
      ctx.lineTo(cx, cy);
    }
    ctx.stroke();
  }
}

/** Borde irregular de la roca sobre el suelo: peñascos pequeños que asoman a lo largo de la línea del muro. */
function caveEdge(ctx: Ctx, rnd: ReturnType<typeof seeded>, from: number, to: number, edge: number, axis: 0 | 1, level: number): void {
  for (let p = from; p < to; p += rnd.uniform(3.5, 7)) {
    const off = rnd.uniform(-2.5, 1.5);
    const r = rnd.uniform(2.5, 5);
    if (axis === 0) drawBoulder(ctx, rnd, p, edge + off, r, level + rnd.randint(-8, 16));
    else drawBoulder(ctx, rnd, edge + off, p, r, level + rnd.randint(-8, 16));
  }
}

/**
 * Remate y sombra de las paredes sobre el suelo: un filo claro donde la piedra termina y una penumbra que se
 * funde con el suelo. Va después de pintar el suelo (que tapa la parte interior del muro).
 */
export function drawWallShadows(
  ctx: Ctx,
  cellSize: number,
  x: number,
  y: number,
  cell: Cell,
  wallBrightness: number,
  barrancoDirs: Iterable<Direction> | null = null,
  style: WallStyle = 'losas',
  boardRow = 0,
  boardCol = 0,
): void {
  const size = cellSize;
  const inset = Math.trunc(size * 0.15);
  const reach = Math.max(6, Math.trunc(size * 0.13));
  const level = Math.trunc(wallBrightness);
  const lipW = Math.max(2, Math.round(size * 0.02));
  const floorMin = x + inset;
  const floorMax = x + size - inset;
  const floorTop = y + inset;
  const floorBottom = y + size - inset;

  const rnd = seeded(boardRow * 100000 + boardCol + 13);
  for (const [rx, ry, rw, rh] of wallRects(size, x, y, cell, new Set<Direction>(barrancoDirs ?? []))) {
    const horizontal = rw >= rh;
    ctx.save();
    if (horizontal) {
      const north = ry < y + size / 2;
      const x0 = Math.max(rx, floorMin);
      const x1 = Math.min(rx + rw, floorMax);
      if (x1 <= x0) {
        ctx.restore();
        continue;
      }
      const edge = north ? floorTop : floorBottom;
      const dir = north ? 1 : -1;
      const grad = ctx.createLinearGradient(0, edge, 0, edge + dir * reach);
      grad.addColorStop(0, 'rgba(0,0,0,0.5)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(x0, north ? edge : edge - reach, x1 - x0, reach);
      if (style === 'cueva') caveEdge(ctx, rnd, x0, x1, edge, 0, level);
      else fillRect(ctx, stoneColor(level + (north ? 26 : -4)), x0, north ? edge - lipW : edge, x1 - x0, lipW, 0.8);
    } else {
      const west = rx < x + size / 2;
      const y0 = Math.max(ry, floorTop);
      const y1 = Math.min(ry + rh, floorBottom);
      if (y1 <= y0) {
        ctx.restore();
        continue;
      }
      const edge = west ? floorMin : floorMax;
      const dir = west ? 1 : -1;
      const grad = ctx.createLinearGradient(edge, 0, edge + dir * reach, 0);
      grad.addColorStop(0, 'rgba(0,0,0,0.45)');
      grad.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(west ? edge : edge - reach, y0, reach, y1 - y0);
      if (style === 'cueva') caveEdge(ctx, rnd, y0, y1, edge, 1, level);
      else fillRect(ctx, stoneColor(level + (west ? 18 : -4)), west ? edge - lipW : edge, y0, lipW, y1 - y0, 0.8);
    }
    ctx.restore();
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
