/** Generadores de números aleatorios: global (Math.random) y con semilla (determinista). */

export interface Rng {
  random(): number;
  randint(a: number, b: number): number;
  uniform(a: number, b: number): number;
  choice<T>(items: readonly T[]): T;
  sample<T>(items: readonly T[], k: number): T[];
  shuffle<T>(items: T[]): void;
}

class BaseRng implements Rng {
  constructor(private readonly next: () => number) {}

  random(): number {
    return this.next();
  }

  /** Entero uniforme en [a, b] (ambos incluidos). */
  randint(a: number, b: number): number {
    return a + Math.floor(this.next() * (b - a + 1));
  }

  uniform(a: number, b: number): number {
    return a + (b - a) * this.next();
  }

  choice<T>(items: readonly T[]): T {
    return items[Math.floor(this.next() * items.length)];
  }

  sample<T>(items: readonly T[], k: number): T[] {
    const copy = items.slice();
    this.shuffle(copy);
    return copy.slice(0, k);
  }

  shuffle<T>(items: T[]): void {
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(this.next() * (i + 1));
      [items[i], items[j]] = [items[j], items[i]];
    }
  }
}

/** mulberry32: PRNG de 32 bits pequeño y rápido. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Generador con semilla: la misma semilla produce siempre la misma secuencia. */
export function seeded(seed: number): Rng {
  return new BaseRng(mulberry32(seed));
}

/** Generador global no determinista. */
export const random: Rng = new BaseRng(Math.random);
