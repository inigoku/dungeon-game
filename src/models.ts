/** Modelos básicos: tipos de celda, direcciones y la celda del tablero. */

export enum CellType {
  EMPTY = 0,
  INICIO = 1,
  PASILLO = 2,
  HABITACION = 3,
  SALIDA = 4,
}

/** Direcciones cardinales (O = Oeste). */
export type Direction = 'N' | 'E' | 'S' | 'O';

export const DIRECTIONS: readonly Direction[] = ['N', 'E', 'S', 'O'];

export const DELTA: Record<Direction, readonly [number, number]> = {
  N: [-1, 0],
  S: [1, 0],
  E: [0, 1],
  O: [0, -1],
};

const OPPOSITE: Record<Direction, Direction> = { N: 'S', S: 'N', E: 'O', O: 'E' };

export function oppositeDirection(direction: Direction): Direction {
  return OPPOSITE[direction];
}

export type Pos = readonly [number, number];

/** Clave numérica única de una posición (el tablero mide como mucho 101). */
export function posKey(row: number, col: number): number {
  return row * 1000 + col;
}

export class Cell {
  constructor(
    public cellType: CellType,
    public exits: Set<Direction> = new Set(),
  ) {}
}
