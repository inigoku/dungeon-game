/**
 * Nube de pelea de dibujo animado: una polvareda que se sacude con puños, botas, garras y
 * colmillos asomando, estrellas, rayas de impacto y onomatopeyas.
 */
import type { Ctx, RGB } from './gfx';
import { font, rgb } from './gfx';

const OUTLINE: RGB = [38, 22, 16];
const DUST: RGB = [232, 224, 204];
const DUST_SHADE: RGB = [186, 176, 152];

/** Número pseudoaleatorio estable en [0, 1) para (a, b). */
function rnd(a: number, b: number): number {
  const x = Math.sin(a * 127.1 + b * 311.7) * 43758.5453;
  return x - Math.floor(x);
}

function star(ctx: Ctx, x: number, y: number, r: number, rotation: number): void {
  ctx.beginPath();
  for (let i = 0; i < 10; i++) {
    const rr = i % 2 === 0 ? r : r * 0.45;
    const a = rotation + (i / 10) * Math.PI * 2 - Math.PI / 2;
    const px = x + Math.cos(a) * rr;
    const py = y + Math.sin(a) * rr;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.fillStyle = rgb([255, 214, 52]);
  ctx.fill();
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = Math.max(1, r * 0.16);
  ctx.lineJoin = 'round';
  ctx.stroke();
}

/** Algo que asoma de la nube: puño, bota, escudo, espada, garra, aleta o colmillo. */
function poke(ctx: Ctx, kind: number, r: number): void {
  const lw = Math.max(1, r * 0.16);
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = lw;
  switch (kind) {
    case 0: {
      // Puño con guantelete
      ctx.fillStyle = rgb([128, 128, 112]);
      ctx.beginPath();
      ctx.rect(-r * 0.5, r * 0.1, r, r * 0.55);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = rgb([234, 180, 136]);
      ctx.beginPath();
      ctx.ellipse(0, -r * 0.2, r * 0.55, r * 0.5, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      break;
    }
    case 1: {
      // Bota
      ctx.fillStyle = rgb([142, 90, 52]);
      ctx.beginPath();
      ctx.moveTo(-r * 0.35, r * 0.5);
      ctx.lineTo(-r * 0.35, -r * 0.1);
      ctx.quadraticCurveTo(r * 0.5, -r * 0.1, r * 0.7, -r * 0.55);
      ctx.lineTo(r * 0.9, -r * 0.2);
      ctx.quadraticCurveTo(r * 0.4, r * 0.5, -r * 0.35, r * 0.5);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      break;
    }
    case 2: {
      // Borde del escudo
      ctx.fillStyle = rgb([128, 128, 112]);
      ctx.beginPath();
      ctx.moveTo(-r * 0.6, r * 0.4);
      ctx.quadraticCurveTo(0, -r * 0.9, r * 0.6, r * 0.4);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      break;
    }
    case 3: {
      // Destello de espada
      ctx.fillStyle = rgb([214, 218, 208]);
      ctx.beginPath();
      ctx.moveTo(0, -r * 1.1);
      ctx.lineTo(r * 0.2, r * 0.5);
      ctx.lineTo(-r * 0.2, r * 0.5);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = rgb([236, 178, 56]);
      ctx.fillRect(-r * 0.45, r * 0.5, r * 0.9, r * 0.16);
      break;
    }
    case 4: {
      // Garra de Profundo
      ctx.fillStyle = rgb([96, 110, 58]);
      ctx.beginPath();
      ctx.ellipse(0, 0, r * 0.55, r * 0.45, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = rgb([250, 226, 176]);
      for (const dx of [-0.32, 0, 0.32]) {
        ctx.beginPath();
        ctx.moveTo(dx * r - r * 0.12, -r * 0.3);
        ctx.lineTo(dx * r, -r * 0.85);
        ctx.lineTo(dx * r + r * 0.12, -r * 0.3);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();
      }
      break;
    }
    case 5: {
      // Aleta de Profundo
      ctx.fillStyle = rgb([96, 110, 58]);
      ctx.beginPath();
      ctx.moveTo(-r * 0.4, r * 0.5);
      ctx.lineTo(0, -r * 0.9);
      ctx.quadraticCurveTo(r * 0.1, -r * 0.2, r * 0.5, -r * 0.3);
      ctx.quadraticCurveTo(r * 0.2, r * 0.1, r * 0.4, r * 0.5);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      break;
    }
    default: {
      // Colmillo
      ctx.fillStyle = rgb([250, 226, 176]);
      ctx.beginPath();
      ctx.moveTo(-r * 0.3, -r * 0.6);
      ctx.lineTo(r * 0.3, -r * 0.6);
      ctx.lineTo(0, r * 0.6);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }
  }
}

const WORDS = ['¡POW!', '¡ZAS!', '¡PAF!', '¡GRRR!', '¡CRASH!'];

/** Globo de onomatopeya con forma de explosión. */
function burst(ctx: Ctx, x: number, y: number, r: number, word: string, rotation: number): void {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(rotation);
  ctx.beginPath();
  for (let i = 0; i < 16; i++) {
    const rr = i % 2 === 0 ? r : r * 0.66;
    const a = (i / 16) * Math.PI * 2;
    const px = Math.cos(a) * rr;
    const py = Math.sin(a) * rr * 0.8;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.fillStyle = rgb([255, 214, 52]);
  ctx.fill();
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.lineWidth = Math.max(1.5, r * 0.09);
  ctx.lineJoin = 'round';
  ctx.stroke();
  const size = Math.max(8, r * 0.46);
  ctx.font = font(size / 0.72);
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.lineWidth = Math.max(1.5, size * 0.16);
  ctx.strokeStyle = rgb(OUTLINE);
  ctx.strokeText(word, 0, 0);
  ctx.fillStyle = rgb([216, 44, 36]);
  ctx.fillText(word, 0, 0);
  ctx.restore();
}

/**
 * Dibuja la nube de pelea centrada en (cx, cy). `size` es el lado de la celda,
 * `elapsed` el tiempo desde que empezó y `duration` su duración total (ms).
 */
export function drawFightCloud(ctx: Ctx, cx: number, cy: number, size: number, elapsed: number, duration: number): void {
  const t = Math.max(0, Math.min(1, elapsed / duration));
  // Aparece rápido, se mantiene y se disipa al final
  const grow = Math.min(1, t / 0.12);
  const fade = t > 0.86 ? 1 - (t - 0.86) / 0.14 : 1;
  const scale = (0.35 + 0.65 * (1 - Math.pow(1 - grow, 3))) * (0.75 + 0.25 * fade);
  const slice = Math.floor(elapsed / 90);
  const wobble = (i: number, k: number) => (rnd(slice * 7 + i, k) - 0.5);

  ctx.save();
  ctx.translate(cx + wobble(1, 1) * size * 0.05, cy + wobble(2, 2) * size * 0.05);
  ctx.globalAlpha = Math.max(0, Math.min(1, fade * 1.1));

  // Polvareda: anillo de bocanadas que gira y tiembla
  const puffs = 13;
  const spin = elapsed * 0.0042;
  const base = size * 0.3 * scale;
  const positions: Array<[number, number, number]> = [];
  for (let i = 0; i < puffs; i++) {
    const ring = i < 8 ? 1 : 0.5;
    const a = (i / (i < 8 ? 8 : 5)) * Math.PI * 2 + spin * (i < 8 ? 1 : -1.4) + rnd(i, 3) * 0.6;
    const rad = base * (0.62 + 0.4 * rnd(i, 4)) * ring + wobble(i, 5) * size * 0.04;
    positions.push([Math.cos(a) * rad * 1.1, Math.sin(a) * rad * 0.9, base * (0.52 + 0.3 * rnd(i, 6))]);
  }
  positions.push([0, 0, base * 0.95]);
  // Contorno común, luego relleno y sombras
  ctx.fillStyle = rgb(OUTLINE);
  for (const [x, y, r] of positions) {
    ctx.beginPath();
    ctx.arc(x, y, r + size * 0.022, 0, Math.PI * 2);
    ctx.fill();
  }
  for (const [x, y, r] of positions) {
    const grad = ctx.createRadialGradient(x - r * 0.3, y - r * 0.35, r * 0.1, x, y, r);
    grad.addColorStop(0, rgb(DUST));
    grad.addColorStop(1, rgb(DUST_SHADE));
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  // Cosas que asoman de la nube: cada una dura un instante y cambia de sitio
  const pokeSlice = Math.floor(elapsed / 210);
  for (let i = 0; i < 6; i++) {
    const id = pokeSlice * 11 + i;
    const phase = ((elapsed % 210) / 210 + rnd(id, 7)) % 1;
    const life = Math.sin(Math.min(1, phase) * Math.PI);
    if (life < 0.05 || rnd(id, 8) < 0.25) continue;
    const a = rnd(id, 9) * Math.PI * 2;
    const dist = base * (0.95 + 0.35 * rnd(id, 10)) * (0.55 + 0.45 * life);
    const kind = Math.floor(rnd(id, 11) * 7);
    ctx.save();
    ctx.translate(Math.cos(a) * dist, Math.sin(a) * dist * 0.85);
    ctx.rotate(a + Math.PI / 2 + (rnd(id, 12) - 0.5) * 1.2);
    poke(ctx, kind, size * 0.13 * (0.75 + 0.5 * life) * scale);
    ctx.restore();
  }

  // Rayas de impacto
  ctx.strokeStyle = rgb([255, 252, 232]);
  ctx.lineWidth = Math.max(1, size * 0.012);
  ctx.lineCap = 'round';
  for (let i = 0; i < 8; i++) {
    if (rnd(slice + i, 13) < 0.45) continue;
    const a = rnd(slice + i, 14) * Math.PI * 2;
    const r0 = base * 1.5;
    const r1 = r0 + size * (0.07 + 0.08 * rnd(slice + i, 15));
    ctx.beginPath();
    ctx.moveTo(Math.cos(a) * r0, Math.sin(a) * r0 * 0.9);
    ctx.lineTo(Math.cos(a) * r1, Math.sin(a) * r1 * 0.9);
    ctx.stroke();
  }

  // Estrellas que giran sobre la nube
  for (let i = 0; i < 3; i++) {
    const a = spin * 1.6 + (i / 3) * Math.PI * 2;
    const sx = Math.cos(a) * base * 1.05;
    const sy = -base * 1.15 + Math.sin(a) * base * 0.28;
    star(ctx, sx, sy, size * 0.06 * scale, a * 1.5);
  }

  // Onomatopeya, cambia cada 0,6 s
  const wordIndex = Math.floor(elapsed / 600);
  if (grow > 0.5 && fade > 0.4) {
    const side = wordIndex % 2 === 0 ? -1 : 1;
    const pop = 0.8 + 0.2 * Math.abs(Math.sin((elapsed % 600) / 600 * Math.PI));
    burst(ctx, side * base * 1.0, -base * 1.25, size * 0.26 * pop * scale, WORDS[wordIndex % WORDS.length], side * 0.12);
  }
  ctx.restore();
}
