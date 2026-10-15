/** Utilidades de esqueleto compartidas por los personajes articulados. */
import type { Ctx, RGB } from './gfx';
import { rgb } from './gfx';
import { fillStroke, OUTLINE, oval, rGradient, shade, type Pt } from './sprites';

/** Cinemática inversa de dos huesos: devuelve la articulación (rodilla/codo) y el extremo alcanzable. */
export function ik(ax: number, ay: number, tx: number, ty: number, l1: number, l2: number, bend: 1 | -1): { j: Pt; e: Pt } {
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

/** Cápsula gruesa con contorno y un brillo suave entre dos puntos. */
export function capsule(ctx: Ctx, a: Pt, b: Pt, width: number, fill: RGB, outline = 1.2): void {
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
  ctx.strokeStyle = rgb(shade(fill, 1.28), 0.5);
  ctx.lineWidth = Math.max(0.8, width * 0.26);
  const nx = -(b[1] - a[1]);
  const ny = b[0] - a[0];
  const n = Math.hypot(nx, ny) || 1;
  const off = width * 0.2;
  ctx.beginPath();
  ctx.moveTo(a[0] + (nx / n) * -off, a[1] + (ny / n) * -off);
  ctx.lineTo(b[0] + (nx / n) * -off, b[1] + (ny / n) * -off);
  ctx.stroke();
}

/** Articulación redondeada (rodilla, codo). */
export function joint(ctx: Ctx, p: Pt, r: number, fill: RGB): void {
  oval(ctx, p[0], p[1], r, r);
  fillStroke(ctx, rGradient(ctx, p[0], p[1], r * 1.4, shade(fill, 1.3), shade(fill, 0.8)), 1.3);
}
