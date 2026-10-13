import { describe, expect, it } from 'vitest';
import { PAD_DEADZONE, padDirection } from '../src/touchpad';

describe('padDirection', () => {
  it('no da dirección dentro de la zona muerta', () => {
    expect(padDirection(0, 0)).toBeNull();
    expect(padDirection(PAD_DEADZONE - 1, 0)).toBeNull();
  });

  it('elige el eje dominante', () => {
    expect(padDirection(40, 10)).toBe('E');
    expect(padDirection(-40, 10)).toBe('O');
    expect(padDirection(10, 40)).toBe('S');
    expect(padDirection(10, -40)).toBe('N');
  });
});
