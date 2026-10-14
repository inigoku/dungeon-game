/** Cruceta táctil adaptativa: aparece bajo el dedo mientras se mantiene pulsado y desaparece al soltar. */
import type { Direction } from './models';

/** Distancia (px CSS) que hay que alejar el dedo del centro para que cuente como dirección. */
export const PAD_DEADZONE = 18;

/** Cuánto debe pesar el eje menor, respecto al mayor, para que cuente como diagonal. */
export const PAD_DIAGONAL_RATIO = 0.45;

/**
 * Direcciones según el desplazamiento del dedo respecto al centro: una (eje dominante), dos si
 * el dedo apunta en diagonal (como pulsar dos botones a la vez) o ninguna dentro de la zona muerta.
 */
export function padDirections(dx: number, dy: number, deadzone = PAD_DEADZONE): Direction[] {
  if (Math.hypot(dx, dy) < deadzone) return [];
  const ax = Math.abs(dx);
  const ay = Math.abs(dy);
  const horizontal: Direction = dx > 0 ? 'E' : 'O';
  const vertical: Direction = dy > 0 ? 'S' : 'N';
  if (ay < ax * PAD_DIAGONAL_RATIO) return [horizontal];
  if (ax < ay * PAD_DIAGONAL_RATIO) return [vertical];
  return ax >= ay ? [horizontal, vertical] : [vertical, horizontal];
}

const ARROWS: Record<Direction, string> = { N: '▲', E: '▶', S: '▼', O: '◀' };

export class AdaptivePad {
  private readonly root: HTMLElement;
  private readonly arrows = new Map<Direction, HTMLElement>();

  constructor(stage: HTMLElement) {
    this.root = document.createElement('div');
    this.root.className = 'apad';
    this.root.hidden = true;
    for (const direction of ['N', 'E', 'S', 'O'] as const) {
      const arrow = document.createElement('span');
      arrow.className = `apad-arrow apad-${direction}`;
      arrow.textContent = ARROWS[direction];
      this.root.append(arrow);
      this.arrows.set(direction, arrow);
    }
    stage.append(this.root);
  }

  /** Muestra la cruceta centrada en (x, y), coordenadas CSS relativas al escenario. */
  show(x: number, y: number): void {
    this.root.style.left = `${x}px`;
    this.root.style.top = `${y}px`;
    this.setActive([]);
    this.root.hidden = false;
  }

  setActive(directions: readonly Direction[]): void {
    for (const [d, arrow] of this.arrows) arrow.classList.toggle('on', directions.includes(d));
  }

  hide(): void {
    this.root.hidden = true;
  }

  dispose(): void {
    this.root.remove();
  }
}
