/**
 * Tablero del dungeon: barranco con puentes, generación del camino principal,
 * salidas de las celdas y consultas de geometría.
 */
import { MAX_GENERATION_ATTEMPTS } from './config';
import { Cell, CellType, DELTA, DIRECTIONS, oppositeDirection, posKey, type Direction, type Pos } from './models';
import { random, seeded } from './rng';

const NEIGHBOR_DELTAS: ReadonlyArray<readonly [number, number]> = [
  [-1, 0],
  [1, 0],
  [0, -1],
  [0, 1],
];

const DIRECTIONS_WITH_DELTA: ReadonlyArray<readonly [number, number, Direction]> = [
  [-1, 0, 'N'],
  [1, 0, 'S'],
  [0, 1, 'E'],
  [0, -1, 'O'],
];

export type BarrancoAxis = 'row' | 'col';

export class World {
  readonly size: number;
  readonly center: number;
  board: Cell[][];
  readonly startPosition: Pos;

  readonly barrancoAxis: BarrancoAxis;
  readonly barrancoIndex: number;
  readonly bridgePointList: Pos[];
  private readonly bridgeKeys: Set<number>;
  private readonly barrancoDirsCache = new Map<number, Direction[]>();
  readonly mainBridgePoint: Pos;

  exitPosition: Pos = [0, 0];
  mainPathOrdered: Pos[] = [];
  mainPath = new Set<number>();

  constructor(size: number) {
    this.size = size;
    this.center = Math.floor(size / 2);
    const center = this.center;
    this.startPosition = [center, center];

    this.board = Array.from({ length: size }, () => Array.from({ length: size }, () => new Cell(CellType.EMPTY)));
    this.board[center][center] = new Cell(CellType.INICIO, new Set<Direction>(['N', 'E', 'S', 'O']));

    // Barranco: una fila o columna completa infranqueable que divide el tablero,
    // lejos del centro para dejar espacio de juego en el lado accesible.
    this.barrancoAxis = random.choice<BarrancoAxis>(['row', 'col']);
    const margin = 15;
    const minOffset = 20;
    const maxOffset = Math.max(minOffset, size - center - margin - 1);
    const offset = random.randint(minOffset, maxOffset);
    const side = random.choice([1, -1]);
    this.barrancoIndex = Math.max(margin, Math.min(size - margin - 1, center + side * offset));

    // Dos puntos cruzables (puente volante). El camino principal cruza siempre
    // por uno de ellos; el otro queda como cruce opcional.
    this.bridgePointList = this.chooseBridgePoints();
    this.bridgeKeys = new Set(this.bridgePointList.map(([r, c]) => posKey(r, c)));
    this.mainBridgePoint = random.choice(this.bridgePointList);

    this.generate();
  }

  private generate(): void {
    const center = this.center;
    let attempt = 0;
    let verified = false;

    while (!verified && attempt < MAX_GENERATION_ATTEMPTS) {
      attempt++;
      if (attempt > 1) console.log(`Intento ${attempt}: regenerando mapa...`);

      for (let row = 0; row < this.size; row++) {
        for (let col = 0; col < this.size; col++) {
          if (row !== center || col !== center) this.board[row][col] = new Cell(CellType.EMPTY);
        }
      }

      // La salida va al lado OPUESTO del barranco: solo se llega cruzando el puente
      this.exitPosition = this.generateExitPosition(true);

      const [nearCell, farCell] = this.getBridgeAnchorPoints(this.mainBridgePoint);
      const pathToBridge = this.calculateMainPath(this.startPosition, nearCell);
      const pathFromBridge = this.calculateMainPath(farCell, this.exitPosition);
      this.mainPathOrdered = [...pathToBridge, this.mainBridgePoint, ...pathFromBridge];
      this.mainPath = new Set(this.mainPathOrdered.map(([r, c]) => posKey(r, c)));

      this.generateMainPathCells();
      verified = this.checkConnectivity(this.startPosition, this.exitPosition);
    }

    if (!verified) console.warn('No se pudo generar un mapa con conectividad garantizada tras varios intentos');
    else console.log('Mapa generado correctamente');
  }

  // --- Consultas de geometría -------------------------------------------------

  inBounds(row: number, col: number): boolean {
    return row >= 0 && row < this.size && col >= 0 && col < this.size;
  }

  cellAt(row: number, col: number): Cell {
    return this.board[row][col];
  }

  isInMainPath(row: number, col: number): boolean {
    return this.mainPath.has(posKey(row, col));
  }

  /** Celda del barranco (infranqueable). Los puentes son la excepción. */
  isBarrancoCell(row: number, col: number): boolean {
    if (this.isBridgeCell(row, col)) return false;
    return this.barrancoAxis === 'row' ? row === this.barrancoIndex : col === this.barrancoIndex;
  }

  isBridgeCell(row: number, col: number): boolean {
    return this.bridgeKeys.has(posKey(row, col));
  }

  /** Celda en la línea del barranco, sea o no puente (el camino principal la evita). */
  isBarrancoLine(row: number, col: number): boolean {
    return this.barrancoAxis === 'row' ? row === this.barrancoIndex : col === this.barrancoIndex;
  }

  /** Las dos direcciones (una a cada lado) que un puente cruza. */
  getBridgeCrossingDirections(): [Direction, Direction] {
    return this.barrancoAxis === 'row' ? ['N', 'S'] : ['O', 'E'];
  }

  /** Lado del barranco en el que está una posición (por defecto, el del inicio). */
  isValidExitSide(row: number, col: number, farSide = false): boolean {
    const value = this.barrancoAxis === 'row' ? row : col;
    if (value === this.barrancoIndex) return false;
    const sameSideAsCenter = value < this.barrancoIndex === this.center < this.barrancoIndex;
    return farSide ? !sameSideAsCenter : sameSideAsCenter;
  }

  /** Direcciones en las que una celda linda directamente con el barranco. */
  barrancoFacingDirections(boardRow: number, boardCol: number): Direction[] {
    const key = posKey(boardRow, boardCol);
    const cached = this.barrancoDirsCache.get(key);
    if (cached) return cached;
    const dirs: Direction[] = [];
    for (const direction of ['N', 'S', 'E', 'O'] as const) {
      const [dr, dc] = DELTA[direction];
      const nr = boardRow + dr;
      const nc = boardCol + dc;
      if (this.inBounds(nr, nc) && this.isBarrancoCell(nr, nc)) dirs.push(direction);
    }
    this.barrancoDirsCache.set(key, dirs);
    return dirs;
  }

  /** Visto desde una celda de barranco, la dirección hacia el lado accesible. */
  getBarrancoAccessibleEdgeDirection(): Direction {
    if (this.barrancoAxis === 'row') return this.center < this.barrancoIndex ? 'N' : 'S';
    return this.center < this.barrancoIndex ? 'O' : 'E';
  }

  /** (near, far): las celdas contiguas a un puente, en el lado accesible y en el opuesto. */
  getBridgeAnchorPoints(bridgePoint: Pos): [Pos, Pos] {
    const [br, bc] = bridgePoint;
    let near: Pos = [br, bc];
    let far: Pos = [br, bc];
    for (const direction of this.getBridgeCrossingDirections()) {
      const [dr, dc] = DELTA[direction];
      const neighbor: Pos = [br + dr, bc + dc];
      if (this.isValidExitSide(neighbor[0], neighbor[1])) near = neighbor;
      else far = neighbor;
    }
    return [near, far];
  }

  private chooseBridgePoints(): Pos[] {
    const margin = 10;
    const coords: number[] = [];
    for (let i = margin; i < this.size - margin; i++) coords.push(i);
    const p1 = random.choice(coords);
    const minSep = Math.max(10, Math.floor((this.size - 2 * margin) / 4));
    const farCandidates = coords.filter((c) => Math.abs(c - p1) >= minSep);
    const p2 = farCandidates.length > 0 ? random.choice(farCandidates) : random.choice(coords);
    return this.barrancoAxis === 'row'
      ? [
          [this.barrancoIndex, p1],
          [this.barrancoIndex, p2],
        ]
      : [
          [p1, this.barrancoIndex],
          [p2, this.barrancoIndex],
        ];
  }

  // --- Conectividad -----------------------------------------------------------

  /** BFS entre start y end, exigiendo salidas enfrentadas entre celdas contiguas. */
  checkConnectivity(start: Pos, end: Pos): boolean {
    const queue: Pos[] = [start];
    const visited = new Set<number>([posKey(start[0], start[1])]);
    for (let head = 0; head < queue.length; head++) {
      const [row, col] = queue[head];
      if (row === end[0] && col === end[1]) return true;
      const cell = this.board[row][col];
      for (const direction of DIRECTIONS) {
        if (!cell.exits.has(direction)) continue;
        const [dr, dc] = DELTA[direction];
        const nr = row + dr;
        const nc = col + dc;
        if (!this.inBounds(nr, nc) || visited.has(posKey(nr, nc))) continue;
        const next = this.board[nr][nc];
        if (next.cellType === CellType.EMPTY) continue;
        if (!next.exits.has(oppositeDirection(direction))) continue;
        visited.add(posKey(nr, nc));
        queue.push([nr, nc]);
      }
    }
    return false;
  }

  // --- Salida y camino principal ----------------------------------------------

  /** Posición de la salida, a entre el 75 % y el 100 % de la distancia al borde. */
  generateExitPosition(farSide = false): Pos {
    const center = this.center;
    const maxDistanceToEdge = center - 5;
    const minDistance = Math.trunc(maxDistanceToEdge * 0.75);
    const maxDistance = maxDistanceToEdge;
    const valid = (row: number, col: number) =>
      row >= 5 && row < this.size - 5 && col >= 5 && col < this.size - 5 && this.isValidExitSide(row, col, farSide);

    for (let attempts = 0; attempts < 100; attempts++) {
      const angle = random.uniform(0, 2 * Math.PI);
      const distance = random.uniform(minDistance, maxDistance);
      const row = center + Math.trunc(distance * Math.cos(angle));
      const col = center + Math.trunc(distance * Math.sin(angle));
      if (valid(row, col)) return [row, col];
    }

    // Respaldo: reducir la distancia gradualmente
    const angles = [0, Math.PI / 4, Math.PI / 2, (3 * Math.PI) / 4, Math.PI, (5 * Math.PI) / 4, (3 * Math.PI) / 2, (7 * Math.PI) / 4];
    for (let d = maxDistance; d >= minDistance; d -= 5) {
      for (const angle of angles) {
        let row = center + Math.trunc(d * Math.cos(angle));
        let col = center + Math.trunc(d * Math.sin(angle));
        row = Math.max(5, Math.min(this.size - 6, row));
        col = Math.max(5, Math.min(this.size - 6, col));
        if (valid(row, col)) return [row, col];
      }
    }

    // Último respaldo
    const safeDistance = Math.min(minDistance, Math.floor((this.size - center - 10) / 2));
    let row = center + safeDistance;
    let col = center + safeDistance;
    if (!this.isValidExitSide(row, col, farSide)) {
      if (this.barrancoAxis === 'row') row = center - safeDistance;
      else col = center - safeDistance;
    }
    return [row, col];
  }

  /**
   * Camino tortuoso y sin lazos de start a end: paseo aleatorio sesgado hacia el
   * objetivo (80 %) con retroceso, y BFS como respaldo. Lista ordenada.
   */
  calculateMainPath(start: Pos, end: Pos): Pos[] {
    const path: Pos[] = [start];
    let current: Pos = start;
    const visited = new Set<number>([posKey(start[0], start[1])]);
    const [endRow, endCol] = end;

    let attempts = 0;
    while (!(current[0] === endRow && current[1] === endCol) && attempts < 10000) {
      attempts++;
      const [cr, cc] = current;
      const options: Array<{ pos: Pos; dist: number }> = [];
      for (const [dr, dc] of NEIGHBOR_DELTAS) {
        const nr = cr + dr;
        const nc = cc + dc;
        if (this.inBounds(nr, nc) && !visited.has(posKey(nr, nc)) && !this.isBarrancoLine(nr, nc)) {
          options.push({ pos: [nr, nc], dist: Math.abs(endRow - nr) + Math.abs(endCol - nc) });
        }
      }

      if (options.length === 0) {
        if (path.length > 1) {
          path.pop();
          current = path[path.length - 1];
        } else break;
        continue;
      }

      let next: Pos;
      if (random.random() < 0.8) {
        options.sort((a, b) => a.dist - b.dist);
        next = options[0].pos;
      } else {
        next = random.choice(options).pos;
      }
      visited.add(posKey(next[0], next[1]));
      path.push(next);
      current = next;
    }

    if (!(current[0] === endRow && current[1] === endCol)) {
      const fallback = this.bfsPath(start, end);
      if (fallback) return fallback;
    }
    return path;
  }

  private bfsPath(start: Pos, end: Pos): Pos[] | null {
    const parents = new Map<number, Pos | null>([[posKey(start[0], start[1]), null]]);
    const queue: Pos[] = [start];
    for (let head = 0; head < queue.length; head++) {
      const pos = queue[head];
      if (pos[0] === end[0] && pos[1] === end[1]) {
        const result: Pos[] = [];
        let node: Pos | null = pos;
        while (node) {
          result.push(node);
          node = parents.get(posKey(node[0], node[1])) ?? null;
        }
        return result.reverse();
      }
      for (const [dr, dc] of NEIGHBOR_DELTAS) {
        const nr = pos[0] + dr;
        const nc = pos[1] + dc;
        if (this.inBounds(nr, nc) && !parents.has(posKey(nr, nc)) && !this.isBarrancoLine(nr, nc)) {
          parents.set(posKey(nr, nc), pos);
          queue.push([nr, nc]);
        }
      }
    }
    return null;
  }

  /** Crea todas las celdas del camino principal con sus salidas. */
  private generateMainPathCells(): void {
    if (this.mainPath.size === 0) return;
    const start = this.startPosition;
    const allDirections = new Set<Direction>(DIRECTIONS);

    for (const [row, col] of this.mainPathOrdered) {
      if (row === start[0] && col === start[1]) {
        const exits = new Set(this.board[row][col].exits);
        for (const [dr, dc, direction] of DIRECTIONS_WITH_DELTA) {
          if (this.isInMainPath(row + dr, col + dc)) exits.add(direction);
        }
        this.board[row][col] = new Cell(this.board[row][col].cellType, exits);
        continue;
      }

      const exits = new Set<Direction>();
      for (const [dr, dc, direction] of DIRECTIONS_WITH_DELTA) {
        if (this.isInMainPath(row + dr, col + dc)) exits.add(direction);
      }

      if (row === this.exitPosition[0] && col === this.exitPosition[1]) {
        this.board[row][col] = new Cell(CellType.SALIDA, exits);
      } else if (this.isBridgeCell(row, col)) {
        this.board[row][col] = new Cell(CellType.PASILLO, exits);
      } else {
        const cellType = random.random() < 0.75 ? CellType.PASILLO : CellType.HABITACION;
        const barranco = new Set(this.barrancoFacingDirections(row, col));
        const remaining = () => [...allDirections].filter((d) => !exits.has(d) && !barranco.has(d));
        const [pFirst, pSecond] = cellType === CellType.PASILLO ? [0.8, 0.4] : [0.7, 0.3];

        let rest = remaining();
        if (rest.length > 0 && random.random() < pFirst) {
          exits.add(random.choice(rest));
          rest = remaining();
          if (rest.length > 0 && random.random() < pSecond) exits.add(random.choice(rest));
        }
        this.board[row][col] = new Cell(cellType, exits);
      }
    }

    // Forzar la salida hacia el OTRO punto de puente si el camino linda con él
    for (const [row, col] of this.mainPathOrdered) {
      const cell = this.board[row][col];
      if (cell.cellType === CellType.EMPTY) continue;
      let newExits: Set<Direction> | null = null;
      for (const [dr, dc, direction] of DIRECTIONS_WITH_DELTA) {
        if (this.isBridgeCell(row + dr, col + dc) && !cell.exits.has(direction)) {
          newExits ??= new Set(cell.exits);
          newExits.add(direction);
        }
      }
      if (newExits) this.board[row][col] = new Cell(cell.cellType, newExits);
    }

    // Conexiones bidireccionales entre celdas del camino
    for (const [row, col] of this.mainPathOrdered) {
      let current = this.board[row][col];
      for (const [dr, dc, direction] of DIRECTIONS_WITH_DELTA) {
        const nr = row + dr;
        const nc = col + dc;
        if (!this.isInMainPath(nr, nc)) continue;
        const neighbor = this.board[nr][nc];
        const opposite = oppositeDirection(direction);

        if (current.exits.has(direction) && !neighbor.exits.has(opposite)) {
          const exits = new Set(neighbor.exits);
          exits.add(opposite);
          this.board[nr][nc] = new Cell(neighbor.cellType, exits);
        }
        if (neighbor.exits.has(opposite) && !current.exits.has(direction)) {
          const exits = new Set(current.exits);
          exits.add(direction);
          this.board[row][col] = new Cell(current.cellType, exits);
          current = this.board[row][col];
        }
      }
    }
  }

  /**
   * Salidas aleatorias de una celda nueva (excepto por donde se entró).
   * PASILLO: 1 salida 10 %, 2 30 %, 3 40 %, 4 20 %. HABITACION: 50/30/15/5 %.
   */
  generateRandomExits(excludeDirection: Direction, cellType: CellType, currentPos: Pos): Set<Direction> {
    // Un puente solo tiene las salidas que cruzan el vacío
    if (this.isBridgeCell(currentPos[0], currentPos[1])) {
      const [near, far] = this.getBridgeCrossingDirections();
      return new Set<Direction>([near, far]);
    }

    const exits = new Set<Direction>();
    const opposite = oppositeDirection(excludeDirection);
    exits.add(opposite);
    const [currentRow, currentCol] = currentPos;

    // Si la celda está en el camino principal, asegurar la salida hacia el siguiente tramo
    let required: Direction | null = null;
    if (this.isInMainPath(currentRow, currentCol)) {
      for (const [dr, dc, direction] of [
        [-1, 0, 'N'],
        [1, 0, 'S'],
        [0, -1, 'O'],
        [0, 1, 'E'],
      ] as const) {
        if (this.isInMainPath(currentRow + dr, currentCol + dc) && direction !== opposite) {
          required = direction;
          exits.add(direction);
          break;
        }
      }
    }

    // No generar salidas hacia el barranco ni hacia vecinas sin la salida complementaria
    const forbidden = new Set<Direction>();
    for (const direction of DIRECTIONS) {
      if (direction === excludeDirection || direction === opposite || direction === required) continue;
      const [dr, dc] = DELTA[direction];
      const nr = currentRow + dr;
      const nc = currentCol + dc;
      if (!this.inBounds(nr, nc)) continue;
      if (this.isBarrancoCell(nr, nc)) {
        forbidden.add(direction);
        continue;
      }
      const neighbor = this.board[nr][nc];
      if (neighbor.cellType !== CellType.EMPTY && !neighbor.exits.has(oppositeDirection(direction))) forbidden.add(direction);
    }

    const excluded = new Set<Direction>([excludeDirection, opposite, ...forbidden]);
    if (required) excluded.add(required);
    const others = DIRECTIONS.filter((d) => !excluded.has(d));

    const roll = random.random();
    let numAdditional: number;
    if (cellType === CellType.PASILLO) {
      numAdditional = roll < 0.1 ? 0 : roll < 0.4 ? 1 : roll < 0.8 ? 2 : 3;
    } else {
      numAdditional = roll < 0.5 ? 0 : roll < 0.8 ? 1 : roll < 0.95 ? 2 : 3;
    }
    for (const d of random.sample(others, Math.min(numAdditional, others.length))) exits.add(d);

    // Un puente vecino siempre debe ser alcanzable
    for (const [dr, dc, direction] of DIRECTIONS_WITH_DELTA) {
      if (this.isBridgeCell(currentRow + dr, currentCol + dc)) exits.add(direction);
    }
    return exits;
  }

  // --- Consultas de decoración ------------------------------------------------

  /** Manchas de sangre: celdas a distancia 1-10 de la salida, con probabilidad creciente. */
  hasBloodStains(row: number, col: number): boolean {
    const distance = Math.abs(this.exitPosition[0] - row) + Math.abs(this.exitPosition[1] - col);
    if (distance < 1 || distance > 10) return false;
    const rnd = seeded(row * 100000 + col);
    const probability = 1 - ((distance - 1) / 9) * 0.7;
    return rnd.random() <= probability;
  }

  /** Línea de visión directa: ninguna celda intermedia puede estar vacía. */
  hasLineOfSight(a: Pos, b: Pos): boolean {
    const [r0, c0] = a;
    const [r1, c1] = b;
    const steps = Math.max(Math.abs(r1 - r0), Math.abs(c1 - c0));
    if (steps === 0) return true;
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      const r = Math.trunc(r0 + (r1 - r0) * t + 0.5);
      const c = Math.trunc(c0 + (c1 - c0) * t + 0.5);
      if (!this.inBounds(r, c)) return false;
      if (this.board[r][c].cellType === CellType.EMPTY) return false;
    }
    return true;
  }
}
