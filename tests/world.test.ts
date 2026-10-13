import { describe, expect, it } from 'vitest';
import { CellType, DELTA, DIRECTIONS, oppositeDirection, posKey } from '../src/models';
import { World } from '../src/world';

const SIZE = 101;

describe('World (generación del mapa)', () => {
  // Varios mapas aleatorios: las propiedades deben cumplirse siempre
  const worlds = Array.from({ length: 12 }, () => new World(SIZE));

  it('el inicio está en el centro y tiene las cuatro salidas posibles', () => {
    for (const w of worlds) {
      const [r, c] = w.startPosition;
      expect([r, c]).toEqual([50, 50]);
      expect(w.board[r][c].cellType).toBe(CellType.INICIO);
    }
  });

  it('hay conectividad garantizada entre el inicio y la salida', () => {
    for (const w of worlds) expect(w.checkConnectivity(w.startPosition, w.exitPosition)).toBe(true);
  });

  it('la salida está al otro lado del barranco que el inicio', () => {
    for (const w of worlds) {
      const [er, ec] = w.exitPosition;
      expect(w.isValidExitSide(er, ec, true)).toBe(true);
      expect(w.board[er][ec].cellType).toBe(CellType.SALIDA);
    }
  });

  it('el camino principal cruza el barranco solo por el puente principal', () => {
    for (const w of worlds) {
      const onLine = w.mainPathOrdered.filter(([r, c]) => w.isBarrancoLine(r, c));
      expect(onLine).toHaveLength(1);
      expect(onLine[0]).toEqual([...w.mainBridgePoint]);
    }
  });

  it('el camino principal es continuo (cada paso es a una celda contigua)', () => {
    for (const w of worlds) {
      const p = w.mainPathOrdered;
      for (let i = 1; i < p.length; i++) {
        expect(Math.abs(p[i][0] - p[i - 1][0]) + Math.abs(p[i][1] - p[i - 1][1])).toBe(1);
      }
      expect(p[0]).toEqual([...w.startPosition]);
      expect(p[p.length - 1]).toEqual([...w.exitPosition]);
    }
  });

  it('las conexiones del camino principal son bidireccionales', () => {
    for (const w of worlds) {
      for (const [r, c] of w.mainPathOrdered) {
        const cell = w.board[r][c];
        for (const d of cell.exits) {
          const [dr, dc] = DELTA[d];
          if (!w.isInMainPath(r + dr, c + dc)) continue;
          expect(w.board[r + dr][c + dc].exits.has(oppositeDirection(d))).toBe(true);
        }
      }
    }
  });

  it('ninguna celda tiene salida hacia el barranco', () => {
    for (const w of worlds) {
      for (const [r, c] of w.mainPathOrdered) {
        for (const d of w.board[r][c].exits) {
          const [dr, dc] = DELTA[d];
          expect(w.isBarrancoCell(r + dr, c + dc)).toBe(false);
        }
      }
    }
  });

  it('los puentes solo tienen las salidas que cruzan el vacío', () => {
    for (const w of worlds) {
      const crossing = new Set(w.getBridgeCrossingDirections());
      for (const [r, c] of w.bridgePointList) {
        expect(w.isBridgeCell(r, c)).toBe(true);
        expect(w.isBarrancoCell(r, c)).toBe(false);
        const exits = w.generateRandomExits('N', CellType.PASILLO, [r, c]);
        expect(exits).toEqual(crossing);
      }
    }
  });

  it('el barranco divide el tablero lejos del centro', () => {
    for (const w of worlds) {
      expect(Math.abs(w.barrancoIndex - w.center)).toBeGreaterThanOrEqual(15);
      expect(w.bridgePointList).toHaveLength(2);
    }
  });
});

describe('World (consultas)', () => {
  const w = new World(SIZE);

  it('barrancoFacingDirections detecta el lado que linda con el barranco', () => {
    const [near] = w.getBridgeAnchorPoints(w.mainBridgePoint);
    // Una celda contigua a la línea del barranco (pero no a un puente) mira hacia él
    const offset = w.barrancoAxis === 'row' ? [0, 1] : [1, 0];
    const cell: [number, number] = [near[0] + offset[0] * 2, near[1] + offset[1] * 2];
    const dirs = w.barrancoFacingDirections(cell[0], cell[1]);
    expect(dirs.length).toBeGreaterThanOrEqual(1);
    for (const d of dirs) {
      const [dr, dc] = DELTA[d];
      expect(w.isBarrancoCell(cell[0] + dr, cell[1] + dc)).toBe(true);
    }
  });

  it('hasBloodStains solo ocurre a distancia 1-10 de la salida y es determinista', () => {
    const [er, ec] = w.exitPosition;
    expect(w.hasBloodStains(er, ec)).toBe(false);
    expect(w.hasBloodStains(er, ec + 15)).toBe(false);
    expect(w.hasBloodStains(er, ec + 1)).toBe(w.hasBloodStains(er, ec + 1));
  });

  it('hasLineOfSight exige celdas no vacías entre los dos puntos', () => {
    const [r, c] = w.startPosition;
    expect(w.hasLineOfSight([r, c], [r, c])).toBe(true);
    // Las celdas vecinas del inicio que no están en el camino siguen vacías
    const empty = DIRECTIONS.map((d) => [r + DELTA[d][0], c + DELTA[d][1]] as const).find(([nr, nc]) => w.board[nr][nc].cellType === CellType.EMPTY);
    if (empty) expect(w.hasLineOfSight([r, c], empty)).toBe(false);
    expect(w.hasLineOfSight([r, c], [-1, c])).toBe(false);
  });

  it('posKey es inyectiva en el tablero', () => {
    const keys = new Set<number>();
    for (let r = 0; r < 20; r++) for (let c = 0; c < 20; c++) keys.add(posKey(r, c));
    expect(keys.size).toBe(400);
  });
});

describe('World.findPath', () => {
  const w = new World(SIZE);
  const everything = () => true;

  it('encuentra el camino más corto por conexiones mutuas', () => {
    const [sr, sc] = w.startPosition;
    const path = w.findPath(w.startPosition, w.exitPosition, everything);
    expect(path).not.toBeNull();
    expect(path![path!.length - 1]).toEqual([...w.exitPosition]);
    let prev: readonly [number, number] = [sr, sc];
    for (const step of path!) {
      expect(Math.abs(step[0] - prev[0]) + Math.abs(step[1] - prev[1])).toBe(1);
      prev = step;
    }
  });

  it('respeta las celdas permitidas', () => {
    expect(w.findPath(w.startPosition, w.exitPosition, () => false)).toBeNull();
    const only = new Set([posKey(50, 50)]);
    expect(w.findPath(w.startPosition, w.exitPosition, (r, c) => only.has(posKey(r, c)))).toBeNull();
  });

  it('a la propia celda de origen devuelve un camino vacío', () => {
    expect(w.findPath(w.startPosition, w.startPosition, everything)).toEqual([]);
  });
});
