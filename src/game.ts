/**
 * Lógica del juego: estado, movimiento, pensamientos, música, monstruos y bucle principal.
 * El dibujado vive en renderer.ts.
 */
import { AudioManager, Sound } from './audio';
import { fitImage, scaleImage, type Assets } from './assets';
import { DEFAULT_BOARD_SIZE, DEFAULT_CELL_SIZE, DEFAULT_VIEW_SIZE } from './config';
import type { Footprint } from './decorations';
import { context2d, type Canvas, type Ctx } from './gfx';
import { InputHandler, type GameInput } from './input';
import { Cell, CellType, DELTA, DIRECTIONS, oppositeDirection, posKey, type Direction, type Pos } from './models';
import { Renderer } from './renderer';
import { random, seeded } from './rng';
import { sleep, ticks } from './time';
import { World } from './world';

export class DeepOne {
  row: number;
  col: number;
  lastActionTime = ticks() + random.randint(0, 2000);
  state: 'IDLE' | 'ROARING' | 'DEAD' = 'IDLE';
  stateStartTime = 0;
  nextActionDelay = random.randint(1500, 2500);
  animating = false;
  animStartTime = 0;
  animDuration = 450;
  fromRow: number;
  fromCol: number;
  dead = false;
  deathTime = 0;
  alerted = false;
  alertStartTime = 0;
  ignoringPlayer = false;

  constructor(row: number, col: number) {
    this.row = row;
    this.col = col;
    this.fromRow = row;
    this.fromCol = col;
  }
}

export interface Barrier {
  row: number;
  col: number;
  startTime: number;
  duration: number;
}

interface RestartButton {
  x: number;
  y: number;
  w: number;
  h: number;
}

export const PLAYER_PALETTE = {
  armor: [90, 90, 90],
  trim: [140, 140, 140],
  skin: [200, 170, 140],
  shield: [70, 70, 70],
  shieldTrim: [140, 120, 80],
  swordHandle: [180, 140, 80],
  swordBlade: [200, 200, 200],
} as const;

const EXIT_IMAGE_BLOCK_MS = 10000;

export class Game implements GameInput {
  // Dimensiones
  readonly size = DEFAULT_BOARD_SIZE;
  readonly initialViewSize = DEFAULT_VIEW_SIZE;
  viewSize = DEFAULT_VIEW_SIZE;
  cellSize = DEFAULT_CELL_SIZE;
  readonly zoomLevels = [5, 7, 11, 21, 51, DEFAULT_BOARD_SIZE];
  currentZoomIndex = 0;
  readonly fixedWindowSize = DEFAULT_VIEW_SIZE * DEFAULT_CELL_SIZE;
  readonly width = this.fixedWindowSize;
  readonly height = this.fixedWindowSize;

  readonly world: World;
  readonly ctx: Ctx;
  readonly audio: AudioManager;
  readonly renderer: Renderer;
  private readonly input: InputHandler;

  // Posición y exploración
  currentPosition: Pos;
  readonly startPosition: Pos;
  visitedCells = new Set<number>();

  // Cámara
  cameraOffsetRow: number;
  cameraOffsetCol: number;
  readonly cameraSpeed = 0.03;
  shakeIntensity = 0;
  shakeDuration = 0;
  shakeStartTime = 0;
  flashActive = false;
  flashStartTime = 0;
  flashDuration = 0;
  flashColor: readonly [number, number, number] = [255, 0, 0];

  // Iluminación
  linesDarkeningEnabled = false;

  // Jugador
  playerAnimSpeed = 0.004;
  playerAnimAmp = 1.0;
  playerWalkDuration = 450;
  playerWalkUntil = 0;
  playerAnimating = false;
  playerAnimStartTime = 0;
  playerAnimFromPos: Pos;
  playerAnimToPos: Pos;
  playerAnimDuration = 450;

  // Título, diálogos e intro
  showingTitle = true;
  titleImage: Canvas | null = null;
  askingExitConfirmation = false;
  askingMainMenuConfirmation = false;
  introAnimActive = false;
  introAnimStartTime = 0;
  introShowWeapons = false;

  // Sonidos
  private readonly ambientSounds: Record<string, Sound> = {};
  private readonly ambientWeights: ReadonlyArray<readonly [string, number]> = [
    ['gota', 0.4],
    ['dos-gotas', 0.4],
    ['murcielago', 0.2],
  ];
  private torchSound: Sound | null = null;
  private bloodSound: Sound | null = null;
  private rafagaSound: Sound | null = null;
  private abominacionSound: Sound | null = null;
  private grunidoSound: Sound | null = null;
  private biteSound: Sound | null = null;
  private swordSound: Sound | null = null;
  private footstepSounds: Sound[] = [];
  private lastFootstepIndex = 0;
  private lastAmbientSoundTime = ticks();
  private nextAmbientSoundDelay = random.randint(3000, 20000);

  // Murciélago
  batFlyingActive = false;
  batFlyingStartTime = 0;
  readonly batFlyingDuration = 1100;
  batFlyingRow = 0;
  batFlyingCol = 0;
  batFromFrac: readonly [number, number] = [0, 0];
  batToFrac: readonly [number, number] = [0, 0];

  // Pensamientos y secuencias
  torchThoughtTriggered = false;
  introThoughtTriggered = false;
  introThoughtFinished = false;
  bloodThoughtTriggered = false;
  rafagaThoughtTriggered = false;
  torchesFlickering = false;
  flickerStartTime = 0;
  torchesExtinguished = false;
  windFadingIn = false;
  exitImageShown = false;
  exitImageStartTime = 0;
  exitThoughtActive = false;
  thoughtPending = false;
  private wasActive = false;

  // Imágenes
  exitImage: Canvas | null = null;
  torchImage: Canvas | null = null;
  bloodImage: Canvas | null = null;
  profundoImage: Canvas | null = null;
  swordImage: Canvas | null = null;

  // Game over
  showingGameOver = false;
  gameOverStartTime = 0;
  gameOverThoughtFinishedTime = 0;
  restartRequested = false;
  restartButtonRect: RestartButton | null = null;

  // Caída por el barranco
  playerFallingActive = false;
  playerFallingStartTime = 0;
  readonly playerFallingDuration = 700;
  playerFallingFromPos: Pos = [0, 0];
  playerFallingDirection: Direction | null = null;
  playerFellIntoBarranco = false;

  // Salud
  readonly maxHealth = 2;
  playerHealth = this.maxHealth;
  invulnerable = false;
  readonly invulnerableDuration = 2000;
  lastDamageTime = 0;

  // Monstruos
  deepOnes: DeepOne[] = [];
  deepOnesSpawned = false;
  monsterFootprints = new Map<number, Footprint[]>();
  hasEncounteredMonsters = false;
  exitVisited = false;
  hasSwordPower = false;
  swordThoughtTriggered = false;
  swordMusicStarted = false;
  activeBarriers: Barrier[] = [];

  // Depuración
  debugMode = false;
  showPath = false;
  autoRevealMode = false;

  private torchStaticCache = new Map<number, { sig: number; count: number }>();
  private lastFootprintCleanup = 0;
  private disposed = false;
  private resolveRun: ((restart: boolean) => void) | null = null;
  private lastFrameTime = 0;
  private readonly keyQueue: GameKeyEvent[] = [];
  private readonly clickQueue: Array<{ x: number; y: number }> = [];
  /** Pasos pendientes de un recorrido automático iniciado con un clic. */
  private autoWalk: Direction[] = [];
  private readonly cleanups: Array<() => void> = [];

  constructor(
    readonly canvas: HTMLCanvasElement,
    private readonly assets: Assets,
  ) {
    canvas.width = this.width;
    canvas.height = this.height;
    this.ctx = context2d(canvas);

    this.world = new World(this.size);
    const center = this.world.center;
    this.startPosition = this.world.startPosition;
    this.currentPosition = [center, center];
    this.visitedCells.add(posKey(center, center));
    this.playerAnimFromPos = this.currentPosition;
    this.playerAnimToPos = this.currentPosition;

    this.cameraOffsetRow = center - Math.floor(this.viewSize / 2);
    this.cameraOffsetCol = center - Math.floor(this.viewSize / 2);

    this.audio = new AudioManager(assets.mixer, assets.buffers);
    this.loadSounds();
    this.loadImages();

    this.renderer = new Renderer(this);
    this.input = new InputHandler(this);
    this.bindEvents();
  }

  // --- Carga de recursos --------------------------------------------------------

  private sound(name: string, volume: number): Sound | null {
    const buffer = this.assets.buffers[name];
    return buffer ? new Sound(this.assets.mixer, buffer, volume) : null;
  }

  private loadSounds(): void {
    for (const [name, volume] of [
      ['gota', 0.5],
      ['dos-gotas', 0.5],
      ['murcielago', 0.6],
    ] as const) {
      const s = this.sound(name, volume);
      if (s) this.ambientSounds[name] = s;
    }
    this.torchSound = this.sound('antorchas', 0.7);
    this.bloodSound = this.sound('sangre', 0.7);
    this.rafagaSound = this.sound('rafaga', 0.9);
    this.abominacionSound = this.sound('abominacion', 0.8);
    this.grunidoSound = this.sound('grunido', 0.8);
    this.biteSound = this.sound('mordisco', 1.0);
    this.swordSound = this.sound('espada', 0.8);
    this.footstepSounds = [this.sound('paso1', 0.4), this.sound('paso2', 0.4)].filter((s): s is Sound => s !== null);
  }

  private loadImages(): void {
    const { images } = this.assets;
    if (images['titulo']) this.titleImage = scaleImage(images['titulo'], this.width, this.height);
    else this.showingTitle = false;

    const scaleToBox = (img: HTMLImageElement | null, box: number): Canvas | null =>
      img ? fitImage(img, box, box) : null;

    if (images['losa']) this.exitImage = fitImage(images['losa'], this.width * 0.9, (this.height - 120) * 0.9);
    if (images['profundo']) this.profundoImage = fitImage(images['profundo'], this.width * 0.9, this.height - 200);
    this.swordImage = scaleToBox(images['espada'], Math.min(this.width, this.height) * 0.8);
    this.torchImage = scaleToBox(images['antorcha'], Math.min(this.width, this.height) * 0.6);
    this.bloodImage = scaleToBox(images['sangre'], Math.min(this.width, this.height) * 0.6);
  }

  // --- Entrada ----------------------------------------------------------------

  private bindEvents(): void {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const key = e.key.length === 1 ? e.key.toLowerCase() : e.key;
      // Evita el scroll con las flechas y las acciones del navegador en F2..F7
      if (key.startsWith('Arrow') || /^F[2-7]$/.test(key)) e.preventDefault();
      // Como en pygame sin repetición de teclas: mantener pulsado no repite
      if (e.repeat) return;
      this.keyQueue.push({ key });
    };
    const onMouseDown = (e: MouseEvent) => {
      if (e.button !== 0) return;
      const rect = this.canvas.getBoundingClientRect();
      this.clickQueue.push({
        x: ((e.clientX - rect.left) * this.width) / rect.width,
        y: ((e.clientY - rect.top) * this.height) / rect.height,
      });
    };
    window.addEventListener('keydown', onKeyDown);
    this.canvas.addEventListener('mousedown', onMouseDown);
    this.cleanups.push(
      () => window.removeEventListener('keydown', onKeyDown),
      () => this.canvas.removeEventListener('mousedown', onMouseDown),
    );
  }

  // --- Efectos ----------------------------------------------------------------

  triggerCameraShake(intensity: number, duration: number): void {
    this.shakeIntensity = intensity;
    this.shakeDuration = duration;
    this.shakeStartTime = ticks();
  }

  triggerScreenFlash(color: readonly [number, number, number], duration: number): void {
    this.flashActive = true;
    this.flashStartTime = ticks();
    this.flashDuration = duration;
    this.flashColor = color;
  }

  triggerBarrierEffect(row: number, col: number): void {
    const now = ticks();
    const existing = this.activeBarriers.find((b) => b.row === row && b.col === col);
    if (existing) {
      existing.startTime = now;
      return;
    }
    this.activeBarriers.push({ row, col, startTime: now, duration: 800 });
  }

  private playBite(fadeOutMs = 0): void {
    if (!this.biteSound) return;
    const channel = this.biteSound.play();
    channel.setVolume(1.0);
    if (fadeOutMs > 0) channel.fadeout(fadeOutMs);
  }

  takeDamage(): void {
    if (this.invulnerable) return;

    this.playerHealth -= 1;
    this.lastDamageTime = ticks();
    this.invulnerable = true;
    this.hasEncounteredMonsters = true;
    this.triggerScreenFlash([255, 0, 0], 300);

    if (this.playerHealth <= 0) {
      this.triggerGameOver();
    } else {
      this.playBite();
      this.audio.showSubtitle('¡Has sido herido! ¡Huye!', 2000);
      this.triggerCameraShake(5.0, 500);
    }
  }

  triggerGameOver(): void {
    if (this.showingGameOver) return;
    console.log('[GAME OVER] El jugador ha sido devorado.');
    this.showingGameOver = true;
    this.gameOverStartTime = ticks();

    this.audio.stopMusic();
    if (this.audio.thoughtActive) this.audio.cancelThought();

    this.playBite();
    this.triggerScreenFlash([200, 0, 0], 200);

    void (async () => {
      await sleep(1000);
      if (this.disposed) return;
      const duration = this.biteSound ? Math.trunc(this.biteSound.getLength() * 1000) : 3000;
      this.audio.triggerThought({
        images: this.profundoImage ? [[this.profundoImage, duration + 1500]] : null,
        subtitles: [['¡¡¡AAAARRRRGGGHH!!!!', duration + 1500]],
        blocksMovement: true,
      });
    })();
  }

  fallIntoBarranco(direction: Direction): void {
    if (this.showingGameOver) return;
    console.log('[GAME OVER] El jugador ha caído por el barranco.');

    // Viento superfuerte en el instante de la caída
    this.audio.setBarrancoWindVolume(1.0);

    this.showingGameOver = true;
    this.gameOverStartTime = ticks();
    this.audio.stopMusic();
    if (this.audio.thoughtActive) this.audio.cancelThought();

    this.playerFallingActive = true;
    this.playerFallingStartTime = this.gameOverStartTime;
    this.playerFallingFromPos = this.currentPosition;
    this.playerFallingDirection = direction;
    this.playerAnimating = false;

    // Grito que se apaga poco a poco, como si se alejara al precipitarse
    this.playBite(900);
    this.triggerScreenFlash([150, 20, 10], 250);

    void (async () => {
      await sleep(1000);
      if (this.disposed) return;
      const duration = this.biteSound ? Math.trunc(this.biteSound.getLength() * 1000) : 3000;
      this.audio.triggerThought({
        subtitles: [['¡¡¡AAAAAAHHHH!!!', duration + 1500]],
        blocksMovement: true,
      });
    })();
  }

  // --- Cámara y zoom -------------------------------------------------------------

  /** Interpola la cámara hacia el jugador y devuelve el desplazamiento flotante. */
  getViewOffset(frames: number): [number, number] {
    const [playerRow, playerCol] = this.currentPosition;
    const maxOffset = this.size - this.viewSize;
    const half = Math.floor(this.viewSize / 2);
    const targetRow = Math.max(0, Math.min(playerRow - half, maxOffset));
    const targetCol = Math.max(0, Math.min(playerCol - half, maxOffset));

    // Factor equivalente a aplicar `cameraSpeed` una vez por cada frame a 60 fps
    const k = 1 - Math.pow(1 - this.cameraSpeed, frames);
    this.cameraOffsetRow += (targetRow - this.cameraOffsetRow) * k;
    this.cameraOffsetCol += (targetCol - this.cameraOffsetCol) * k;
    this.cameraOffsetRow = Math.max(0, Math.min(this.cameraOffsetRow, maxOffset));
    this.cameraOffsetCol = Math.max(0, Math.min(this.cameraOffsetCol, maxOffset));
    return [this.cameraOffsetRow, this.cameraOffsetCol];
  }

  centerCameraInstantly(targetRow: number, targetCol: number): void {
    const half = Math.floor(this.viewSize / 2);
    const maxOffset = this.size - this.viewSize;
    this.cameraOffsetRow = Math.max(0, Math.min(targetRow - half, maxOffset));
    this.cameraOffsetCol = Math.max(0, Math.min(targetCol - half, maxOffset));
  }

  private setZoomIndex(index: number): void {
    this.currentZoomIndex = index;
    this.viewSize = this.zoomLevels[index];
    this.cellSize = Math.floor(this.fixedWindowSize / this.viewSize);
    this.updateCameraTarget();
  }

  zoomIn(): void {
    if (this.currentZoomIndex > 0) this.setZoomIndex(this.currentZoomIndex - 1);
  }

  zoomOut(): void {
    if (this.currentZoomIndex < this.zoomLevels.length - 1) this.setZoomIndex(this.currentZoomIndex + 1);
  }

  /** Recentra la cámara (sin interpolar) en el jugador tras cambiar el zoom. */
  updateCameraTarget(): void {
    const [playerRow, playerCol] = this.currentPosition;
    if (this.viewSize >= this.size) {
      this.cameraOffsetRow = 0;
      this.cameraOffsetCol = 0;
      return;
    }
    const half = Math.floor(this.viewSize / 2);
    const maxOffset = this.size - this.viewSize;
    this.cameraOffsetRow = Math.max(0, Math.min(playerRow - half, maxOffset));
    this.cameraOffsetCol = Math.max(0, Math.min(playerCol - half, maxOffset));
  }

  // --- Antorchas, sangre y brillo -----------------------------------------------

  hasBloodStains(row: number, col: number): boolean {
    return this.world.hasBloodStains(row, col);
  }

  hasTorches(row: number, col: number): boolean {
    const cell = this.world.board[row][col];
    if (cell.cellType !== CellType.PASILLO && cell.cellType !== CellType.HABITACION && cell.cellType !== CellType.SALIDA) return false;
    const [er, ec] = this.startPosition;
    return Math.abs(er - row) + Math.abs(ec - col) >= 5;
  }

  /**
   * Cuántas antorchas se dibujan en la celda. Solo en el camino principal, a
   * partir de 5 celdas de la entrada; la probabilidad baja al acercarse a la salida.
   */
  countTorches(row: number, col: number, cell: Cell, includeSword = true): number {
    // Iluminación mágica de la espada: equivale a 3 antorchas en la celda del jugador
    if (includeSword && this.hasSwordPower && row === this.currentPosition[0] && col === this.currentPosition[1]) return 3;

    if (this.torchesExtinguished) return 0;

    if (this.torchesFlickering) {
      const elapsed = ticks() - this.flickerStartTime;
      // Parpadeo lento (500 ms) los 3 primeros segundos y rápido (100 ms) después
      const interval = elapsed < 3000 ? 500 : 100;
      if (Math.floor(elapsed / interval) % 2 === 0) return 0;
    }

    if (this.introAnimActive) return 0;
    if (!this.introThoughtFinished) return 0;
    if (!this.world.isInMainPath(row, col)) return 0;

    const [sr, sc] = this.startPosition;
    if (Math.abs(sr - row) + Math.abs(sc - col) < 5) return 0;

    // Parte estática (depende solo de la posición y las salidas): se memoiza
    let sig = 0;
    if (cell.exits.has('N')) sig |= 1;
    if (cell.exits.has('E')) sig |= 2;
    if (cell.exits.has('S')) sig |= 4;
    if (cell.exits.has('O')) sig |= 8;
    const key = posKey(row, col);
    const cached = this.torchStaticCache.get(key);
    if (cached && cached.sig === sig) return cached.count;

    const [exitRow, exitCol] = this.world.exitPosition;
    const barranco = new Set(this.world.barrancoFacingDirections(row, col));
    let availableWalls = 0;
    for (const d of ['N', 'S', 'E', 'O'] as const) {
      if (!cell.exits.has(d) && !barranco.has(d)) availableWalls++;
    }

    let count: number;
    if (row === exitRow && col === exitCol) {
      // En la salida hay siempre al menos una antorcha
      count = availableWalls === 0 ? 0 : Math.max(1, availableWalls);
    } else {
      const distanceToExit = Math.abs(exitRow - row) + Math.abs(exitCol - col);
      const totalDistance = Math.abs(exitRow - sr) + Math.abs(exitCol - sc);
      const progress = totalDistance > 0 ? 1 - distanceToExit / totalDistance : 0.5;
      const baseProbability = 0.4 - progress * 0.3; // del 40 % al 10 %
      const rnd = seeded(row * 100000 + col);
      let desired = 0;
      for (let i = 0; i < 4; i++) if (rnd.random() < baseProbability) desired++;
      count = Math.min(desired, availableWalls);
    }
    this.torchStaticCache.set(key, { sig, count });
    return count;
  }

  /** Brillo del suelo de una celda según antorchas y distancia a la entrada. */
  getCellBrightness(row: number, col: number): number {
    const cell = this.world.board[row][col];
    switch (cell.cellType) {
      case CellType.EMPTY:
        return 0;
      case CellType.INICIO:
        return 4 * 31;
      case CellType.SALIDA:
        return Math.max(0, 40 + Math.min(130, this.countTorches(row, col, cell) * 31));
      default: {
        const torchBrightness = Math.min(130, this.countTorches(row, col, cell) * 31);
        return Math.max(0, this.baseBrightness(row, col) + torchBrightness);
      }
    }
  }

  /** Oscurecimiento por distancia a la entrada: 20 en el inicio, 0 en la salida. */
  baseBrightness(row: number, col: number): number {
    const [sr, sc] = this.startPosition;
    const [er, ec] = this.world.exitPosition;
    const distanceFromStart = Math.abs(sr - row) + Math.abs(sc - col);
    const totalDistance = Math.abs(er - sr) + Math.abs(ec - sc);
    const progress = totalDistance > 0 ? distanceFromStart / totalDistance : 0.5;
    return Math.trunc(20 * (1 - progress));
  }

  // --- Movimiento ----------------------------------------------------------------

  private playFootstep(): void {
    if (this.footstepSounds.length === 0) return;
    this.footstepSounds[this.lastFootstepIndex % this.footstepSounds.length].play();
    this.lastFootstepIndex++;
  }

  /** Mueve al jugador un paso (creando la celda destino si aún no existe). */
  placeCellInDirection(direction: Direction): void {
    if (this.audio.thoughtActive && this.audio.thoughtBlocksMovement) return;
    if (this.exitImageShown && ticks() - this.exitImageStartTime < EXIT_IMAGE_BLOCK_MS) return;

    const world = this.world;
    const [currentRow, currentCol] = this.currentPosition;
    const currentCell = world.board[currentRow][currentCol];
    const [dr, dc] = DELTA[direction];
    const targetRow = currentRow + dr;
    const targetCol = currentCol + dc;

    if (!currentCell.exits.has(direction)) {
      // Sin salida porque da al barranco: el jugador se precipita
      if (world.inBounds(targetRow, targetCol) && world.isBarrancoCell(targetRow, targetCol)) this.fallIntoBarranco(direction);
      return;
    }
    if (!world.inBounds(targetRow, targetCol)) return;

    const opposite = oppositeDirection(direction);
    const targetCell = world.board[targetRow][targetCol];

    if (targetCell.cellType !== CellType.EMPTY) {
      // Solo se puede pasar si la celda destino tiene la salida complementaria
      if (!targetCell.exits.has(opposite)) return;
    } else {
      this.createCell(direction, targetRow, targetCol, opposite);
    }

    this.enterCell(targetRow, targetCol);
  }

  // --- Recorrido automático por clic -------------------------------------------

  /** Celda del tablero bajo un punto del lienzo, o null si queda fuera. */
  private boardCellAt(x: number, y: number): Pos | null {
    const row = Math.floor(this.cameraOffsetRow + y / this.cellSize);
    const col = Math.floor(this.cameraOffsetCol + x / this.cellSize);
    return this.world.inBounds(row, col) ? [row, col] : null;
  }

  /**
   * Un clic en una celda sin revelar, contigua a una revelada, lleva al jugador
   * hasta una celda revelada vecina (la más cercana con camino y salida hacia
   * ella) y después a la celda pulsada.
   */
  private startAutoWalk(x: number, y: number): void {
    this.autoWalk = [];
    if (
      this.showingTitle || this.showingGameOver || this.introAnimActive || this.thoughtPending ||
      this.audio.thoughtActive || this.askingExitConfirmation || this.askingMainMenuConfirmation
    ) return;
    const target = this.boardCellAt(x, y);
    if (!target) return;
    const [tr, tc] = target;
    const world = this.world;
    if (this.visitedCells.has(posKey(tr, tc)) || world.isBarrancoCell(tr, tc) || world.isBridgeCell(tr, tc)) return;

    // BFS desde el jugador por celdas reveladas conectadas en ambos sentidos
    const start = this.currentPosition;
    const startKey = posKey(start[0], start[1]);
    const parents = new Map<number, { from: number; dir: Direction }>();
    const seen = new Set<number>([startKey]);
    const queue: Pos[] = [start];
    for (let i = 0; i < queue.length; i++) {
      const [row, col] = queue[i];
      const cell = world.board[row][col];
      for (const dir of cell.exits) {
        const [dr, dc] = DELTA[dir];
        const nr = row + dr;
        const nc = col + dc;
        const key = posKey(nr, nc);
        if (!world.inBounds(nr, nc) || seen.has(key) || !this.visitedCells.has(key)) continue;
        const next = world.board[nr][nc];
        if (next.cellType === CellType.EMPTY || !next.exits.has(oppositeDirection(dir))) continue;
        seen.add(key);
        parents.set(key, { from: posKey(row, col), dir });
        queue.push([nr, nc]);
      }
    }

    // BFS recorre por distancia creciente: la primera vecina válida es la más cercana
    for (const [row, col] of queue) {
      const dir = DIRECTIONS.find((d) => {
        const [dr, dc] = DELTA[d];
        return row + dr === tr && col + dc === tc;
      });
      if (!dir || !world.board[row][col].exits.has(dir)) continue;
      const path: Direction[] = [dir];
      for (let key = posKey(row, col); key !== startKey; ) {
        const step = parents.get(key)!;
        path.unshift(step.dir);
        key = step.from;
      }
      this.autoWalk = path;
      return;
    }
  }

  /** Da el siguiente paso del recorrido automático cuando termina el anterior. */
  private stepAutoWalk(now: number): void {
    if (this.autoWalk.length === 0) return;
    if (this.showingGameOver || this.showingTitle || this.thoughtPending || this.audio.thoughtActive) {
      this.autoWalk = [];
      return;
    }
    if (now < this.playerWalkUntil) return;
    const before = this.currentPosition;
    this.placeCellInDirection(this.autoWalk.shift()!);
    if (this.currentPosition === before) this.autoWalk = [];
  }

  private createCell(direction: Direction, row: number, col: number, opposite: Direction): void {
    const world = this.world;
    if (row === world.exitPosition[0] && col === world.exitPosition[1]) {
      world.board[row][col] = new Cell(CellType.SALIDA, new Set<Direction>([opposite]));
    } else if (world.isBridgeCell(row, col)) {
      world.board[row][col] = new Cell(CellType.PASILLO, world.generateRandomExits(direction, CellType.PASILLO, [row, col]));
    } else {
      const cellType = random.random() < 0.75 ? CellType.PASILLO : CellType.HABITACION;
      const exits = world.generateRandomExits(direction, cellType, [row, col]);
      // Si una vecina tiene salida hacia aquí, mantener esa conexión
      for (const d of ['N', 'E', 'S', 'O'] as const) {
        const [dr, dc] = DELTA[d];
        const nr = row + dr;
        const nc = col + dc;
        if (!world.inBounds(nr, nc)) continue;
        const neighbor = world.board[nr][nc];
        if (neighbor.cellType !== CellType.EMPTY && neighbor.exits.has(oppositeDirection(d))) exits.add(d);
      }
      world.board[row][col] = new Cell(cellType, exits);
    }
  }

  /** Efectos de entrar en una celda: pasos, animación, monstruos y pensamientos. */
  private enterCell(row: number, col: number): void {
    this.playFootstep();

    if (this.hasBloodStains(row, col) && this.ambientSounds['dos-gotas']) {
      const splash = this.ambientSounds['dos-gotas'];
      splash.setVolume(0.3);
      splash.play();
    }

    // Animación suave del muñeco entre la posición antigua y la nueva
    const now = ticks();
    this.playerAnimFromPos = this.currentPosition;
    this.playerAnimToPos = [row, col];
    this.playerAnimating = true;
    this.playerAnimStartTime = now;
    this.playerWalkUntil = now + this.playerWalkDuration;
    this.currentPosition = [row, col];

    for (const monster of this.deepOnes) monster.ignoringPlayer = false;

    // ¿Caminó hacia un monstruo?
    for (const monster of this.deepOnes) {
      if (monster.row === row && monster.col === col) {
        if (this.hasSwordPower) {
          if (!monster.dead) {
            monster.dead = true;
            monster.deathTime = ticks();
            monster.state = 'DEAD';
          }
        } else {
          this.takeDamage();
          return;
        }
      }
    }

    this.visitedCells.add(posKey(row, col));
    this.revealAdjacentCells(row, col);

    // Volver al inicio tras visitar la salida: poder de la espada
    if (row === this.startPosition[0] && col === this.startPosition[1] && this.exitVisited && !this.hasSwordPower) {
      this.hasSwordPower = true;
      this.thoughtPending = true;
      this.swordThoughtTriggered = true;
      this.audio.startFadeOut(500);
      void this.delayedThought(500, () => {
        this.audio.triggerThought({
          sounds: this.swordSound ? [[this.swordSound, 0]] : [],
          images: this.swordImage ? [[this.swordImage, 5000]] : null,
          subtitles: [['¡El poder de la espada sagrada!', 5000]],
          blocksMovement: true,
        });
      });
    }

    const cell = this.world.board[row][col];

    // Pensamiento de sangre
    if (!this.bloodThoughtTriggered && this.bloodSound && this.hasBloodStains(row, col)) {
      this.bloodThoughtTriggered = true;
      this.thoughtPending = true;
      const sound = this.bloodSound;
      void this.delayedThought(1000, () => {
        this.audio.triggerThought({
          sounds: [[sound, 0]],
          images: this.bloodImage ? [[this.bloodImage, 0]] : null,
          subtitles: [['¿Es eso... sangre?!?', 6000]],
          blocksMovement: true,
        });
      });
      return;
    }

    // Pensamiento de antorchas
    if (!this.torchThoughtTriggered && this.torchSound && this.hasTorches(row, col) && this.countTorches(row, col, cell) > 0) {
      this.torchThoughtTriggered = true;
      this.thoughtPending = true;
      const sound = this.torchSound;
      void this.delayedThought(1000, () => {
        this.audio.triggerThought({
          sounds: [[sound, 0]],
          images: this.torchImage ? [[this.torchImage, 0]] : null,
          subtitles: [['Una antorcha encendida... ¡Interesante!', 6000]],
          blocksMovement: true,
        });
      });
      return;
    }

    // Llegada a la celda final
    if (row === this.world.exitPosition[0] && col === this.world.exitPosition[1] && !this.exitImageShown) {
      this.exitImageShown = true;
      this.exitImageStartTime = ticks();
      this.exitVisited = true;
      this.exitThoughtActive = true;
      void (async () => {
        await sleep(1000);
        if (this.disposed || !this.abominacionSound) return;
        const imageDuration = Math.trunc(this.abominacionSound.getLength() * 1000) + 2000;
        this.audio.triggerThought({
          sounds: [[this.abominacionSound, 0]],
          images: this.exitImage ? [[this.exitImage, imageDuration]] : null,
          subtitles: [['¿Qué es esta abominación?', imageDuration]],
          blocksMovement: true,
        });
      })();
    }
  }

  /** Espera y lanza un pensamiento; libera el bloqueo de entrada al terminar. */
  private async delayedThought(delayMs: number, trigger: () => void): Promise<void> {
    await sleep(delayMs);
    if (this.disposed) return;
    trigger();
    this.thoughtPending = false;
  }

  /** Con la revelación automática (F2), marca como visitadas las celdas con salida conectada. */
  revealAdjacentCells(row: number, col: number): void {
    if (!this.autoRevealMode) return;
    const cell = this.world.board[row][col];
    for (const direction of cell.exits) {
      const [dr, dc] = DELTA[direction];
      const ar = row + dr;
      const ac = col + dc;
      if (this.world.inBounds(ar, ac)) this.visitedCells.add(posKey(ar, ac));
    }
  }

  // --- Sonido ambiental y música -------------------------------------------------

  startBatFlyingAnimation(): void {
    this.batFlyingActive = true;
    this.batFlyingStartTime = ticks();
    [this.batFlyingRow, this.batFlyingCol] = this.currentPosition;
    const paths: Array<readonly [readonly [number, number], readonly [number, number]]> = [
      [[0, -0.5], [0, 0.5]],
      [[0, 0.5], [0, -0.5]],
      [[-0.5, 0], [0.5, 0]],
      [[0.5, 0], [-0.5, 0]],
      [[-0.5, -0.5], [0.5, 0.5]],
      [[0.5, 0.5], [-0.5, -0.5]],
      [[-0.5, 0.5], [0.5, -0.5]],
      [[0.5, -0.5], [-0.5, 0.5]],
    ];
    [this.batFromFrac, this.batToFrac] = random.choice(paths);
  }

  /** Viento según la distancia al barranco: suave a 2 celdas, fuerte al lado. */
  private updateBarrancoWind(): void {
    if (this.playerFallingActive || this.playerFellIntoBarranco) return;
    if (this.audio.currentMusic === 'viento') {
      this.audio.setBarrancoWindVolume(0);
      return;
    }
    const [row, col] = this.currentPosition;
    const distance = Math.abs((this.world.barrancoAxis === 'row' ? row : col) - this.world.barrancoIndex);
    const volume = distance <= 1 ? 0.7 : distance === 2 ? 0.25 : 0;
    this.audio.setBarrancoWindVolume(volume);
  }

  /** Música según la distancia al inicio (adagio) y a la salida (cthulhu). */
  private updateMusicVolumeByDistance(): void {
    const audio = this.audio;

    if (this.hasSwordPower) {
      if (!this.swordMusicStarted) return;
      if (audio.currentMusic !== 'alataque' && audio.musicSounds['alataque']) {
        audio.currentMusic = 'alataque';
        audio.musicChannel.play(audio.musicSounds['alataque'], -1);
        audio.musicChannel.setVolume(0.8);
      }
      return;
    }

    const [sr, sc] = this.startPosition;
    const [er, ec] = this.world.exitPosition;
    const [cr, cc] = this.currentPosition;
    const distanceFromStart = Math.hypot(cr - sr, cc - sc);
    const distanceToExit = Math.hypot(cr - er, cc - ec);
    const adagioVolume = () => Math.max(0.05, Math.min(0.5, 0.5 - (distanceFromStart / 5) * 0.45));

    if (audio.currentMusic === 'adagio' && !audio.cthulhuPlayed) {
      audio.musicChannel.setVolume(adagioVolume());
      if (distanceToExit <= 5 && audio.musicSounds['cthulhu']) {
        audio.musicChannel.stop();
        audio.currentMusic = 'cthulhu';
        audio.musicChannel.play(audio.musicSounds['cthulhu'], -1);
        audio.musicChannel.setVolume(0.05);
        audio.cthulhuPlayed = true;
      }
    } else if (audio.cthulhuPlayed) {
      if (cr === er && cc === ec) {
        if (!this.windFadingIn && audio.currentMusic === 'cthulhu') audio.musicChannel.setVolume(1.0);
      } else if (distanceFromStart <= 5 && audio.musicSounds['adagio']) {
        audio.musicChannel.stop();
        audio.currentMusic = 'adagio';
        audio.musicChannel.play(audio.musicSounds['adagio'], -1);
        audio.musicChannel.setVolume(adagioVolume());
        audio.cthulhuPlayed = false;
      } else {
        audio.musicChannel.setVolume(Math.max(0.05, Math.min(1.0, 1.0 - (distanceToExit / 5) * 0.95)));
      }
    }
  }

  private updateAmbientSounds(): void {
    if (this.showingTitle || Object.keys(this.ambientSounds).length === 0) return;
    const now = ticks();
    if (now - this.lastAmbientSoundTime <= this.nextAmbientSoundDelay) return;

    const roll = random.random();
    let cumulative = 0;
    for (const [name, weight] of this.ambientWeights) {
      cumulative += weight;
      if (roll <= cumulative && this.ambientSounds[name]) {
        this.ambientSounds[name].play();
        if (name === 'murcielago') this.startBatFlyingAnimation();
        break;
      }
    }
    this.lastAmbientSoundTime = now;
    this.nextAmbientSoundDelay = random.randint(5000, 15000);
  }

  // --- Monstruos -------------------------------------------------------------

  private cleanupFootprints(): void {
    const now = ticks();
    for (const [key, footprints] of this.monsterFootprints) {
      const alive = footprints.filter((fp) => now - fp.time < 15000);
      if (alive.length === 0) this.monsterFootprints.delete(key);
      else this.monsterFootprints.set(key, alive);
    }
  }

  private isOccupied(row: number, col: number): boolean {
    return this.deepOnes.some((m) => m.row === row && m.col === col);
  }

  private updateMonsters(): void {
    const now = ticks();
    const world = this.world;
    const manhattan = (a: Pos, b: Pos) => Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
    const isStartOrExit = (r: number, c: number) =>
      (r === this.startPosition[0] && c === this.startPosition[1]) || (r === world.exitPosition[0] && c === world.exitPosition[1]);
    const steps: ReadonlyArray<readonly [number, number]> = [
      [-1, 0],
      [1, 0],
      [0, -1],
      [0, 1],
    ];

    for (const monster of this.deepOnes) {
      if (monster.dead) continue;

      // Indicador de alerta
      if (!this.hasSwordPower) {
        if (world.hasLineOfSight([monster.row, monster.col], this.currentPosition) && !monster.ignoringPlayer) {
          monster.alerted = true;
          monster.alertStartTime = now;
        } else if (now - monster.alertStartTime > 1000) {
          monster.alerted = false;
        }
      } else {
        monster.alerted = false;
      }

      if (monster.state === 'ROARING' && now - monster.stateStartTime > 1500) monster.state = 'IDLE';

      if (now - monster.lastActionTime <= monster.nextActionDelay) continue;
      monster.lastActionTime = now;

      // Persecución más rápida si el jugador está a 5 celdas o menos
      const dist = manhattan([monster.row, monster.col], this.currentPosition);
      monster.nextActionDelay = dist <= 5 ? random.randint(800, 1200) : random.randint(1500, 2500);

      const roll = random.random();
      const fleeing = this.hasSwordPower;
      const moveProb = fleeing ? 0.8 : 0.25;

      if (roll < moveProb) {
        let next: Pos | null = null;

        if (fleeing) {
          // Con la espada, los monstruos huyen (sin pisar inicio ni salida)
          const candidates: Pos[] = [];
          for (const [dr, dc] of steps) {
            const nr = monster.row + dr;
            const nc = monster.col + dc;
            if (!world.isInMainPath(nr, nc)) continue;
            if (isStartOrExit(nr, nc)) {
              this.triggerBarrierEffect(nr, nc);
              continue;
            }
            if (!this.isOccupied(nr, nc)) candidates.push([nr, nc]);
          }
          if (candidates.length > 0) {
            candidates.sort((a, b) => manhattan(b, this.currentPosition) - manhattan(a, this.currentPosition));
            next = candidates[0];
          }
        } else if (world.hasLineOfSight([monster.row, monster.col], this.currentPosition) && !monster.ignoringPlayer) {
          // Perseguir al jugador por el camino principal
          const neighbors: Pos[] = steps.map(([dr, dc]) => [monster.row + dr, monster.col + dc] as Pos);
          neighbors.sort((a, b) => manhattan(a, this.currentPosition) - manhattan(b, this.currentPosition));
          const [tr, tc] = neighbors[0];
          if (!world.isInMainPath(tr, tc) || isStartOrExit(tr, tc)) {
            // Una barrera mágica le impide salir del camino o entrar al inicio/salida
            this.triggerBarrierEffect(tr, tc);
            monster.ignoringPlayer = true;
            monster.alerted = false;
          } else if (!this.isOccupied(tr, tc)) {
            next = [tr, tc];
          }
        } else {
          // Paseo aleatorio si no ve al jugador
          const candidates: Pos[] = [];
          for (const [dr, dc] of steps) {
            const nr = monster.row + dr;
            const nc = monster.col + dc;
            if (world.isInMainPath(nr, nc) && !isStartOrExit(nr, nc) && !this.isOccupied(nr, nc)) candidates.push([nr, nc]);
          }
          if (candidates.length > 0) next = random.choice(candidates);
        }

        if (next) {
          // Huella húmeda donde estaba
          const fpKey = posKey(monster.row, monster.col);
          const list = this.monsterFootprints.get(fpKey) ?? [];
          list.push({
            relX: Math.trunc(this.cellSize * random.uniform(0.3, 0.7)),
            relY: Math.trunc(this.cellSize * random.uniform(0.3, 0.7)),
            time: now,
          });
          this.monsterFootprints.set(fpKey, list);

          // Pisada húmeda si está cerca
          const stepDist = manhattan([monster.row, monster.col], this.currentPosition);
          if (stepDist < 12 && this.footstepSounds.length > 0) {
            const sound = random.choice(this.footstepSounds);
            sound.setVolume(Math.max(0.1, 0.5 - (stepDist / 12) * 0.4));
            sound.play();
          }

          monster.fromRow = monster.row;
          monster.fromCol = monster.col;
          [monster.row, monster.col] = next;
          monster.animating = true;
          monster.animStartTime = now;

          if (monster.row === this.currentPosition[0] && monster.col === this.currentPosition[1]) {
            if (this.hasSwordPower) {
              monster.dead = true;
              monster.deathTime = now;
              monster.state = 'DEAD';
            } else {
              this.takeDamage();
            }
          }
        }
      } else if (roll < moveProb + 0.25) {
        // Rugido
        monster.state = 'ROARING';
        monster.stateStartTime = now;
        if (dist < 10 && this.grunidoSound) {
          this.grunidoSound.setVolume(Math.max(0.1, 0.8 - (dist / 10) * 0.7));
          this.grunidoSound.play();
          if (dist < 6) this.triggerCameraShake(0.2 * (1 - dist / 6), 500);
        }
      }
    }
  }

  // --- Secuencia final (ráfaga) -------------------------------------------------

  private startRafagaSequence(): void {
    if (!this.rafagaSound) return;
    this.audio.musicChannel.stop();
    this.audio.triggerThought({ sounds: [[this.rafagaSound, 0]], blocksMovement: true });
    this.torchesFlickering = true;
    this.flickerStartTime = ticks();

    // Zoom out al máximo al empezar
    this.setZoomIndex(this.zoomLevels.length - 1);

    void (async () => {
      // Las antorchas parpadean 5 segundos
      await sleep(5000);
      if (this.disposed) return;

      // Se apagan y aparecen los monstruos
      this.torchesFlickering = false;
      this.torchesExtinguished = true;
      if (!this.deepOnesSpawned) {
        this.deepOnesSpawned = true;
        const [cr, cc] = this.currentPosition;
        const spawnPoints: Pos[] = [];
        for (const [r, c] of this.world.mainPathOrdered) {
          const isStart = r === this.startPosition[0] && c === this.startPosition[1];
          const isExit = r === this.world.exitPosition[0] && c === this.world.exitPosition[1];
          if (!isStart && !isExit && Math.abs(r - cr) + Math.abs(c - cc) >= 7) spawnPoints.push([r, c]);
        }
        if (spawnPoints.length > 0) {
          const count = Math.min(spawnPoints.length, random.randint(5, 10));
          this.deepOnes = random.sample(spawnPoints, count).map(([r, c]) => new DeepOne(r, c));
          console.log(`Aparecen ${this.deepOnes.length} Profundos`);
        }
      }

      // Un segundo en la oscuridad y zoom in
      await sleep(1000);
      if (this.disposed) return;
      this.setZoomIndex(0);

      if (this.audio.musicSounds['viento']) {
        this.audio.currentMusic = 'viento';
        this.audio.musicChannel.play(this.audio.musicSounds['viento'], -1);
        this.audio.musicChannel.setVolume(1.0);
      }
    })();
  }

  // --- Acciones llamadas desde la entrada ----------------------------------------

  /** Empieza la partida desde la pantalla de título. */
  startGame(): void {
    this.showingTitle = false;
    // Cancelar el pensamiento de intro y marcar que terminó (para que salgan las antorchas)
    if (this.audio.thoughtActive) {
      this.audio.cancelThought();
      this.introThoughtFinished = true;
    }
    this.introAnimActive = true;
    this.introAnimStartTime = ticks();
  }

  returnToMainMenu(): void {
    this.showingTitle = true;
    this.askingMainMenuConfirmation = false;
    this.audio.stopMusic();
    if (this.audio.thoughtActive) this.audio.cancelThought();
  }

  teleportTo(pos: Pos): void {
    this.currentPosition = pos;
    this.playerAnimating = false;
    this.centerCameraInstantly(pos[0], pos[1]);
    this.visitedCells.add(posKey(pos[0], pos[1]));
  }

  // --- Bucle principal ---------------------------------------------------------

  /** Ejecuta la partida. Resuelve true si hay que reiniciar y false si se sale. */
  run(): Promise<boolean> {
    return new Promise((resolve) => {
      this.resolveRun = resolve;

      // Primer frame (título) y pensamiento de introducción
      this.renderer.draw(1);
      if (this.showingTitle && !this.introThoughtTriggered && this.audio.introSound) {
        this.introThoughtTriggered = true;
        this.audio.triggerThought({
          sounds: [[this.audio.introSound, 0]],
          subtitles: [
            ['Usa A, W, S y D para moverte.', 4000],
            ['Haz zoom con Z y X.', 4000],
            ['Explora la mazmorra... encuentra la salida...', 6000],
            ['Ten cuidado con lo que acecha en las sombras.', 6000],
            ['¡Buena suerte, valiente guerrero!', 14000],
          ],
          blocksMovement: false,
        });
      }

      this.lastFrameTime = performance.now();
      requestAnimationFrame(this.frame);
    });
  }

  private finish(restart: boolean): void {
    this.disposed = true;
    for (const cleanup of this.cleanups) cleanup();
    this.audio.dispose();
    this.resolveRun?.(restart);
    this.resolveRun = null;
  }

  private frame = (): void => {
    if (this.disposed) return;
    if (this.restartRequested) {
      this.finish(true);
      return;
    }

    const nowMs = performance.now();
    // Frames de 60 fps transcurridos (limitado para no dar saltos tras pausar la pestaña)
    const frames = Math.min(5, Math.max(0.1, (nowMs - this.lastFrameTime) / (1000 / 60)));
    this.lastFrameTime = nowMs;
    const now = ticks();

    if (this.invulnerable && now - this.lastDamageTime > this.invulnerableDuration) this.invulnerable = false;

    const audio = this.audio;
    audio.updateFades();
    audio.updateSubtitles();
    audio.updateThoughts();

    const wasActive = this.wasActive;
    const active = audio.thoughtActive;

    // Fin del pensamiento de introducción: aparecen las antorchas
    if (wasActive && !active && this.introThoughtTriggered && !this.introThoughtFinished) this.introThoughtFinished = true;

    // Fin del pensamiento de la espada: arranca la música de ataque
    if (wasActive && !active && this.swordThoughtTriggered && !this.swordMusicStarted) {
      this.swordMusicStarted = true;
      if (audio.musicSounds['alataque']) {
        audio.currentMusic = 'alataque';
        audio.musicChannel.play(audio.musicSounds['alataque'], -1);
        audio.startFadeIn(1000, 0.8);
      }
      audio.playSwordHum();
    }

    // Fin del pensamiento de la salida: secuencia de la ráfaga
    if (wasActive && !active && this.exitThoughtActive && !this.rafagaThoughtTriggered) {
      this.rafagaThoughtTriggered = true;
      this.startRafagaSequence();
    }

    // Fin del pensamiento de Game Over
    if (wasActive && !active && this.showingGameOver && this.gameOverThoughtFinishedTime === 0) {
      this.gameOverThoughtFinishedTime = now;
    }

    this.wasActive = audio.thoughtActive;

    this.updateMonsters();

    if (now - this.lastFootprintCleanup > 1000) {
      this.lastFootprintCleanup = now;
      this.cleanupFootprints();
    }

    // Música y viento (no durante fundidos ni tras el game over)
    if (!this.showingTitle && !this.introAnimActive && !audio.fadingOut && !audio.fadingIn && !this.windFadingIn && !this.showingGameOver) {
      this.updateMusicVolumeByDistance();
    }
    if (!this.showingTitle && !this.introAnimActive && !this.showingGameOver) this.updateBarrancoWind();

    this.updateAmbientSounds();

    // Eventos de entrada acumulados desde el último frame
    let running = true;
    for (const ev of this.keyQueue.splice(0)) {
      this.autoWalk = [];
      if (!this.input.handleKey(ev.key)) running = false;
    }
    for (const click of this.clickQueue.splice(0)) {
      this.input.handleClick(click.x, click.y);
      this.startAutoWalk(click.x, click.y);
    }
    this.stepAutoWalk(now);

    this.renderer.draw(frames);

    if (!running) {
      this.finish(false);
      return;
    }
    requestAnimationFrame(this.frame);
  };
}

interface GameKeyEvent {
  key: string;
}
