import { describe, expect, it } from 'vitest';
import { pickFrame, POSE } from '../src/atlas';

const base = { facing: 'S' as const, moving: false, walkAngle: 0, hurt: false, alerted: false };

describe('pickFrame', () => {
  it('reposo y alerta de frente', () => {
    expect(pickFrame(base).index).toBe(POSE.REST);
    expect(pickFrame({ ...base, alerted: true }).index).toBe(POSE.ALERT);
    expect(pickFrame({ ...base, hurt: true }).index).toBe(POSE.HURT_REST);
  });
  it('el oeste es el este reflejado', () => {
    const west = pickFrame({ ...base, facing: 'O' });
    expect(west).toEqual({ index: 16, mirror: true });
  });
  it('el ciclo de marcha recorre cuatro fases', () => {
    const idx = [0, 1.6, 3.2, 4.8].map((a) => pickFrame({ ...base, facing: 'N', moving: true, walkAngle: a }).index);
    expect(idx).toEqual([13, 14, 15, 14]);
  });
  it('una pose explícita manda', () => {
    expect(pickFrame({ ...base, pose: POSE.DEAD }).index).toBe(51);
  });
});
