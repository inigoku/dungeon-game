/** Reloj del juego (equivalente a pygame.time.get_ticks): milisegundos desde el arranque. */
const origin = performance.now();

export function ticks(): number {
  return performance.now() - origin;
}

export const sleep = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));
