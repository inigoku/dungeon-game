import { describe, expect, it } from 'vitest';
import { PAD_DEADZONE, padDirections } from '../src/touchpad';

describe('padDirections', () => {
  it('no da dirección dentro de la zona muerta', () => {
    expect(padDirections(0, 0)).toEqual([]);
    expect(padDirections(PAD_DEADZONE - 1, 0)).toEqual([]);
  });

  it('elige una sola dirección cuando un eje domina', () => {
    expect(padDirections(40, 10)).toEqual(['E']);
    expect(padDirections(-40, 10)).toEqual(['O']);
    expect(padDirections(10, 40)).toEqual(['S']);
    expect(padDirections(10, -40)).toEqual(['N']);
  });

  it('da dos direcciones en diagonal, la dominante primero', () => {
    expect(padDirections(30, -30)).toEqual(['E', 'N']);
    expect(padDirections(-30, 30)).toEqual(['O', 'S']);
    expect(padDirections(20, 35)).toEqual(['S', 'E']);
    expect(padDirections(-35, -20)).toEqual(['O', 'N']);
  });
});
