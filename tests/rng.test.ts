import { describe, expect, it } from 'vitest';
import { random, seeded } from '../src/rng';

describe('seeded rng', () => {
  it('es determinista para una misma semilla', () => {
    const a = seeded(12345);
    const b = seeded(12345);
    for (let i = 0; i < 50; i++) expect(a.random()).toBe(b.random());
  });

  it('semillas distintas dan secuencias distintas', () => {
    expect(seeded(1).random()).not.toBe(seeded(2).random());
  });

  it('randint respeta los límites (inclusivos)', () => {
    const rnd = seeded(7);
    const seen = new Set<number>();
    for (let i = 0; i < 500; i++) {
      const v = rnd.randint(-3, 3);
      expect(v).toBeGreaterThanOrEqual(-3);
      expect(v).toBeLessThanOrEqual(3);
      seen.add(v);
    }
    expect(seen.size).toBe(7);
  });

  it('uniform queda en [a, b)', () => {
    const rnd = seeded(9);
    for (let i = 0; i < 200; i++) {
      const v = rnd.uniform(0.2, 0.8);
      expect(v).toBeGreaterThanOrEqual(0.2);
      expect(v).toBeLessThan(0.8);
    }
  });

  it('sample devuelve k elementos distintos del origen', () => {
    const items = [1, 2, 3, 4, 5, 6];
    const picked = seeded(3).sample(items, 4);
    expect(picked).toHaveLength(4);
    expect(new Set(picked).size).toBe(4);
    for (const p of picked) expect(items).toContain(p);
    expect(items).toEqual([1, 2, 3, 4, 5, 6]); // no muta la entrada
  });

  it('el generador global funciona', () => {
    const v = random.randint(1, 6);
    expect(v).toBeGreaterThanOrEqual(1);
    expect(v).toBeLessThanOrEqual(6);
  });
});
