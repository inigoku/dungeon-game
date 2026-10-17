import { describe, expect, it } from 'vitest';
import { CLASSES, CLASS_IDS, initialClass } from '../src/classes';

describe('clases', () => {
  it('cada clase tiene su dibujo y una hoja completa', () => {
    expect(CLASS_IDS).toEqual(['guerrero', 'barbaro', 'exploradora']);
    for (const id of CLASS_IDS) {
      const info = CLASSES[id];
      expect(info.id).toBe(id);
      expect(typeof info.draw).toBe('function');
      expect(info.sheet.abilities).toHaveLength(6);
      expect(info.sheet.attacks.length).toBeGreaterThan(0);
      expect(info.sheet.equipment.length).toBeGreaterThan(0);
    }
  });

  it('corazones: caballero 4, bárbaro 3 y exploradora 2', () => {
    expect([CLASSES.guerrero.hearts, CLASSES.barbaro.hearts, CLASSES.exploradora.hearts]).toEqual([4, 3, 2]);
  });

  it('sin navegador la clase inicial es el guerrero', () => {
    expect(initialClass()).toBe('guerrero');
  });
});
