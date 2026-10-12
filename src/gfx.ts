/**
 * Primitivas de dibujo sobre Canvas 2D con la misma semántica que pygame.draw
 * (rellenos, bordes interiores, grosor de línea, arcos en sentido antihorario...).
 */

export type RGB = readonly [number, number, number];
export type Ctx = CanvasRenderingContext2D;
export type Canvas = HTMLCanvasElement;

export function rgb(c: RGB, alpha = 1): string {
  const r = Math.round(c[0]);
  const g = Math.round(c[1]);
  const b = Math.round(c[2]);
  return alpha >= 1 ? `rgb(${r},${g},${b})` : `rgba(${r},${g},${b},${Math.max(0, alpha)})`;
}

export function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

export function gray(v: number): RGB {
  const b = clamp(Math.trunc(v), 0, 255);
  return [b, b, b];
}

export function createCanvas(w: number, h: number): Canvas {
  const canvas = document.createElement('canvas');
  canvas.width = Math.max(1, Math.round(w));
  canvas.height = Math.max(1, Math.round(h));
  return canvas;
}

export function context2d(canvas: Canvas): Ctx {
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Canvas 2D no disponible');
  return ctx;
}

export function fillRect(ctx: Ctx, color: RGB, x: number, y: number, w: number, h: number, alpha = 1): void {
  if (w <= 0 || h <= 0) return;
  ctx.fillStyle = rgb(color, alpha);
  ctx.fillRect(x, y, w, h);
}

/** Borde de rectángulo de `width` píxeles dibujado hacia el interior (como pygame). */
export function strokeRect(ctx: Ctx, color: RGB, x: number, y: number, w: number, h: number, width: number, alpha = 1): void {
  if (w <= 0 || h <= 0) return;
  ctx.strokeStyle = rgb(color, alpha);
  ctx.lineWidth = width;
  ctx.strokeRect(x + width / 2, y + width / 2, w - width, h - width);
}

export function line(
  ctx: Ctx,
  color: RGB,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  width = 1,
  alpha = 1,
): void {
  ctx.strokeStyle = rgb(color, alpha);
  ctx.lineWidth = width;
  ctx.lineCap = 'butt';
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

/** Círculo relleno (width = 0) o anillo interior de `width` píxeles. */
export function circle(ctx: Ctx, color: RGB, cx: number, cy: number, r: number, width = 0, alpha = 1): void {
  if (r <= 0) return;
  if (width <= 0 || width >= r) {
    ctx.fillStyle = rgb(color, alpha);
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.strokeStyle = rgb(color, alpha);
    ctx.lineWidth = width;
    ctx.beginPath();
    ctx.arc(cx, cy, r - width / 2, 0, Math.PI * 2);
    ctx.stroke();
  }
}

/** Elipse inscrita en el rectángulo (x, y, w, h); relleno o borde interior. */
export function ellipse(
  ctx: Ctx,
  color: RGB,
  x: number,
  y: number,
  w: number,
  h: number,
  width = 0,
  alpha = 1,
): void {
  if (w <= 0 || h <= 0) return;
  ctx.beginPath();
  if (width <= 0) {
    ctx.fillStyle = rgb(color, alpha);
    ctx.ellipse(x + w / 2, y + h / 2, w / 2, h / 2, 0, 0, Math.PI * 2);
    ctx.fill();
  } else {
    ctx.strokeStyle = rgb(color, alpha);
    ctx.lineWidth = width;
    ctx.ellipse(x + w / 2, y + h / 2, Math.max(0.1, (w - width) / 2), Math.max(0.1, (h - width) / 2), 0, 0, Math.PI * 2);
    ctx.stroke();
  }
}

export function polygon(ctx: Ctx, color: RGB, points: ReadonlyArray<readonly [number, number]>, alpha = 1): void {
  ctx.fillStyle = rgb(color, alpha);
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);
  for (let i = 1; i < points.length; i++) ctx.lineTo(points[i][0], points[i][1]);
  ctx.closePath();
  ctx.fill();
}

/**
 * Arco de elipse inscrita en (x, y, w, h). Los ángulos siguen la convención de
 * pygame: radianes, en sentido antihorario visto en pantalla, 0 = derecha.
 */
export function arc(
  ctx: Ctx,
  color: RGB,
  x: number,
  y: number,
  w: number,
  h: number,
  start: number,
  stop: number,
  width = 1,
): void {
  if (w <= 0 || h <= 0) return;
  ctx.strokeStyle = rgb(color);
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.ellipse(x + w / 2, y + h / 2, w / 2, h / 2, 0, -start, -stop, true);
  ctx.stroke();
}

/** Texto centrado (o alineado) con la fuente por defecto del juego. */
export function font(size: number): string {
  // pygame.font.Font(None, n) produce glifos de unos 0.7·n píxeles de alto
  return `bold ${Math.round(size * 0.72)}px "Helvetica Neue", Arial, sans-serif`;
}
