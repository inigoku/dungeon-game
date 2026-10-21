import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import fs from 'node:fs';
const OUT = '/tmp/claude-0/stl/out/';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 300, height: 300 } });
p.on('pageerror', e => console.log('E', e.message));
await p.goto('http://localhost:8765/view.html');
await p.waitForFunction(() => window.ready, null, { timeout: 90000 });
const cell = { size: 512, half: 29.09, zc: 26.36 };
const big = { size: 1024, half: 27.83, zc: 26.85 };
const C = (n) => `col_${n}.bin`;
const jobs = {
  // atlas 128 (cada fotograma)
  'a0': { ...cell, view: 'frente', col: C('guardia') }, 'a1': { ...cell, view: 'frente', col: C('guardia') },
  'a2': { ...cell, view: 'frente', col: C('guardia') }, 'a12': { ...cell, view: 'atras', col: C('guardia') },
  'a17': { ...cell, view: 'izq', col: C('guardia') }, 'a20': { ...cell, view: 'der', col: C('guardia') },
  'a24': { ...cell, view: 'frente', col: C('dolor'), rot: [-0.22, 0.1, 0] }, 'a25': { ...cell, view: 'frente', col: C('dolor'), rot: [-0.22, -0.1, 0] },
  'a48': { ...cell, view: 'izq', col: C('dolor'), rot: [-0.4, 0, 0], center: true },
  'a49': { ...cell, view: 'izq', col: C('dolor'), rot: [-0.95, 0, 0], ground: true, center: true },
  'a50': { ...cell, view: 'izq', col: C('muerta'), rot: [-1.35, 0, 0], ground: true, center: true },
  'a51': { ...cell, view: 'izq', col: C('muerta'), rot: [-1.5708, 0, 0], ground: true, center: true },
  'a56': { ...cell, view: 'izq', col: C('susto'), rot: [0.4, 0, 0] },
  'a57': { ...cell, view: 'izq', col: C('susto'), rot: [1.05, 0, 0], center: true },
  // tira de caras 256
  'c0': { ...big, view: 'frente', col: C('guardia') },
  'c1': { ...big, view: 'frente', col: C('dolor'), rot: [-0.28, 0.12, 0] },
  'c2': { ...big, view: 'frente', col: C('susto'), rot: [-0.14, 0, 0] },
  'c3': { ...big, view: 'frente', col: C('asombro') },
  'c4': { ...big, view: 'frente', col: C('poder'), rot: [0, 0, -0.1] },
  'c5': { ...big, view: 'frente', col: C('mirar'), rot: [0, 0, 0.55] },
  'c6': { ...big, view: 'izq', col: C('guardia') }, 'c7': { ...big, view: 'der', col: C('guardia') },
  // retrato de busto
  'cara': { size: 800, half: 8, zc: 39, view: 'frente', col: C('guardia') }, 'cara2': { size: 800, half: 8, zc: 39, view: 'frente', col: C('asombro') },
  'retrato': { size: 640, half: 13.5, zc: 38.5, view: 'frente', col: C('guardia') },
};
const only = process.argv.slice(2);
for (const [n, o] of Object.entries(jobs)) {
  if (only.length && !only.includes(n)) continue;
  const d = await p.evaluate(o => window.render(o), o);
  fs.writeFileSync(`${OUT}${n}.png`, Buffer.from(d.split(',')[1], 'base64'));
}
await b.close();
