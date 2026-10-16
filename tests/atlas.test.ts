import { describe, expect, it } from 'vitest';
import { pickFrame, POSE } from '../src/atlas';

const base = { facing: 'S' as const, moving: false, walkAngle: 0, hurt: false, alerted: false };

describe('pickFrame', () => {
  it('en guardia o en reposo cuando está parado', () => {
    expect(pickFrame({ ...base, alerted: true }).index).toBe(POSE.ALERT);
    expect(pickFrame(base).index).toBe(POSE.REST);
    expect(pickFrame({ ...base, hurt: true }).index).toBe(POSE.HURT_REST);
    expect(pickFrame({ ...base, hurt: true, alerted: true }).index).toBe(POSE.HURT_ALERT);
  });
  it('parado siempre de frente, aunque mirase a un lado', () => {
    expect(pickFrame({ ...base, facing: 'E', alerted: true }).index).toBe(POSE.ALERT);
  });
  it('un icono de movimiento por dirección, sin reflejar', () => {
    const icons = (['N', 'E', 'O', 'S'] as const).map((facing) => pickFrame({ ...base, facing, moving: true }));
    expect(icons.map((i) => i.index)).toEqual([12, 17, 20, POSE.ALERT_TO_REST]);
    expect(icons.every((i) => !i.mirror)).toBe(true);
  });
  it('el salto del paso es pequeño y no negativo', () => {
    for (const a of [0, 1, 2, 3, 4, 5, 6]) {
      const hop = pickFrame({ ...base, moving: true, walkAngle: a }).hop;
      expect(hop).toBeGreaterThanOrEqual(0);
      expect(hop).toBeLessThan(0.04);
    }
  });
  it('una pose explícita manda', () => {
    expect(pickFrame({ ...base, pose: POSE.DEAD }).index).toBe(51);
  });
});
