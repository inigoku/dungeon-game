import { describe, expect, it } from 'vitest';
import { dyingFrame, fallFrame, LAYOUTS, pickFrame } from '../src/atlas';

const base = { facing: 'S' as const, moving: false, walkAngle: 0, hurt: false, alerted: false };
const barbaro = LAYOUTS.barbaro;
const guerrero = LAYOUTS.guerrero;
const exploradora = LAYOUTS.exploradora;
const duelista = LAYOUTS.duelista;

describe('pickFrame', () => {
  it('en guardia o en reposo cuando está parado', () => {
    expect(pickFrame(barbaro, { ...base, alerted: true }).index).toBe(0);
    expect(pickFrame(barbaro, base).index).toBe(1);
    expect(pickFrame(barbaro, { ...base, hurt: true }).index).toBe(25);
    expect(pickFrame(barbaro, { ...base, hurt: true, alerted: true }).index).toBe(24);
  });
  it('el caballero herido usa sus fotogramas de herido', () => {
    expect(pickFrame(guerrero, { ...base, hurt: true, alerted: true }).index).toBe(24);
    expect(pickFrame(guerrero, { ...base, hurt: true }).index).toBe(25);
    expect(pickFrame(guerrero, base).index).toBe(guerrero.rest);
  });
  it('parado siempre de frente, aunque mirase a un lado', () => {
    expect(pickFrame(barbaro, { ...base, facing: 'E', alerted: true }).index).toBe(0);
  });
  it('un icono de movimiento por dirección', () => {
    const icons = (['N', 'E', 'O', 'S'] as const).map((facing) => pickFrame(barbaro, { ...base, facing, moving: true }));
    expect(icons.map((i) => i.index)).toEqual([12, 17, 20, 2]);
    expect(icons.every((i) => !i.mirror)).toBe(true);
  });
  it('el caballero, la exploradora y la duelista tienen oeste propio, sin reflejar', () => {
    for (const layout of [guerrero, exploradora, duelista]) {
      const east = pickFrame(layout, { ...base, facing: 'E', moving: true });
      const west = pickFrame(layout, { ...base, facing: 'O', moving: true });
      expect(west.index).not.toBe(east.index);
      expect([east.mirror, west.mirror]).toEqual([false, false]);
    }
  });
  it('el salto del paso es pequeño y no negativo', () => {
    for (const a of [0, 1, 2, 3, 4, 5, 6]) {
      const hop = pickFrame(barbaro, { ...base, moving: true, walkAngle: a }).hop;
      expect(hop).toBeGreaterThanOrEqual(0);
      expect(hop).toBeLessThan(0.04);
    }
  });
  it('una pose explícita manda', () => {
    expect(pickFrame(barbaro, { ...base, pose: 51 }).index).toBe(51);
  });
});

describe('muerte y caída', () => {
  it('recorre los cuatro fotogramas de la muerte y se queda en el último', () => {
    expect([0, 400, 800, 1200, 99999].map((ms) => dyingFrame(barbaro, ms))).toEqual([48, 49, 50, 51, 51]);
  });
  it('tropieza y cae', () => {
    expect(fallFrame(barbaro, 0.1)).toBe(56);
    expect(fallFrame(barbaro, 0.8)).toBe(57);
  });
});
