/**
 * Lógica del juego: estado, movimiento, pensamientos, música, monstruos y bucle principal.
 * El dibujado vive en renderer.ts.
 */
import { reportError } from './errors';
import { AudioManager, Sound } from './audio';
import { fitImage, type Assets } from './assets';
import { DEFAULT_BOARD_SIZE, DEFAULT_CELL_SIZE, DEFAULT_VIEW_SIZE } from './config';
import type { Footprint } from './decorations';
import { context2d, type Canvas, type Ctx } from './gfx';
import { InputHandler, type GameInput } from './input';
import { CLASSES, initialClass, type PlayerClass } from './classes';
import { CharacterSheet } from './sheet';
import { AdaptivePad, padDirections } from './touchpad';
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

const EXIT_IMAGE_BLOCK_MS = 10000;
/** Tiempo manteniendo el dedo quieto para que aparezca la cruceta táctil. */
const PAD_HOLD_MS = 220;
/** Duración de la pelea con un monstruo (la nube de lucha). */
export const FIGHT_MS = 2600;
/** Tiempo quieto tras el cual el guerrero vuelve a mirar de frente. */
export const FACE_FRONT_AFTER_MS = 3000;
/** Factor de separación de los dedos que equivale a un nivel de zoom. */
const PINCH_STEP = 1.3;

export class Game implements GameInput {
  // Dimensiones
  readonly size = DEFAULT_BOARD_SIZE;
  readonly initialViewSize = DEFAULT_VIEW_SIZE;
  viewSize = DEFAULT_VIEW_SIZE;
  cellSize = DEFAULT_CELL_SIZE;
  readonly zoomLevels = [3, 4, DEFAULT_VIEW_SIZE, 7, 11, 21, 51, DEFAULT_BOARD_SIZE];
  /** Nivel de zoom inicial: la vista de 5×5 (hay dos niveles más cercanos). */
  currentZoomIndex = 2;
  readonly fixedWindowSize = DEFAULT_VIEW_SIZE * DEFAULT_CELL_SIZE;
  /** Tamaño lógico del lienzo: el lado corto mide siempre `fixedWindowSize`; el otro se amplía según la ventana. */
  width = this.fixedWindowSize;
  height = this.fixedWindowSize;

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
  /** true mientras el jugador ha desplazado la vista arrastrando */
  cameraManual = false;
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
  /** Hacia dónde mira el guerrero (la última dirección en que intentó moverse). */
  playerFacing: Direction = 'S';
  /** Instante del último intento de movimiento; pasado un rato quieto, el guerrero vuelve a mirar de frente. */
  lastMoveAttemptTime = 0;
  /** Pelea en curso entre el guerrero y un Profundo: el dibujo muestra una nube de lucha. */
  fight: { monster: DeepOne; row: number; col: number; start: number; shakes: number } | null = null;
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
  askingRestartConfirmation = false;
  showingSheet = false;
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

  // Game over
  showingGameOver = false;
  gameOverStartTime = 0;
  gameOverThoughtFinishedTime = 0;
  restartRequested = false;
  restartButtonRect: RestartButton | null = null;
  /** Botones Sí/No de las confirmaciones (coordenadas del lienzo), solo mientras se muestran. */
  confirmButtons: { yes: RestartButton; no: RestartButton } | null = null;

  // Caída por el barranco
  playerFallingActive = false;
  playerFallingStartTime = 0;
  readonly playerFallingDuration = 700;
  playerFallingFromPos: Pos = [0, 0];
  playerFallingDirection: Direction | null = null;
  playerFellIntoBarranco = false;

  // Salud
  /** Corazones de la clase: el caballero 4, el bárbaro 3 y la exploradora 2. */
  readonly maxHealth: number;
  playerHealth: number;
  invulnerable = false;
  readonly invulnerableDuration = 2000;
  lastDamageTime = 0;

  // Monstruos
  deepOnes: DeepOne[] = [];
  deepOnesSpawned = false;
  monsterFootprints = new Map<number, Footprint[]>();
  exitVisited = false;
  hasSwordPower = false;
  swordThoughtTriggered = false;
  swordMusicStarted = false;
  activeBarriers: Barrier[] = [];

  // Depuración
  debugMode = false;
  showPath = false;
  autoRevealMode = false;

  // Movimiento automático por clic/toque
  autoTarget: Pos | null = null;
  private autoPath: Pos[] = [];
  private autoNextStepTime = 0;

  private torchStaticCache = new Map<number, { sig: number; count: number }>();
  private lastFootprintCleanup = 0;
  private disposed = false;
  private resolveRun: ((restart: boolean) => void) | null = null;
  private lastFrameTime = 0;
  private readonly keyQueue: GameKeyEvent[] = [];
  private readonly clickQueue: Array<{ x: number; y: number }> = [];
  private readonly cleanups: Array<() => void> = [];

  constructor(
    readonly canvas: HTMLCanvasElement,
    private readonly assets: Assets,
    readonly playerClass: PlayerClass = initialClass(),
  ) {
    this.ctx = context2d(canvas);
    this.maxHealth = CLASSES[playerClass].hearts;
    this.playerHealth = this.maxHealth;

    this.world = new World(this.size);
    const center = this.world.center;
    this.startPosition = this.world.startPosition;
    this.currentPosition = [center, center];
    this.visitedCells.add(posKey(center, center));
    this.playerAnimFromPos = this.currentPosition;
    this.playerAnimToPos = this.currentPosition;

    this.resizeTo(canvas.clientWidth, canvas.clientHeight);
    this.cameraOffsetRow = this.cameraTarget(center, this.height);
    this.cameraOffsetCol = this.cameraTarget(center, this.width);

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

  private imageSlot(image: Canvas | null, duration: number): Array<[Canvas, number]> | null {
    return image ? [[image, duration]] : null;
  }

  private loadImages(): void {
    if (this.assets.images['titulo']) this.fitTitleImage();
    else this.showingTitle = false;
  }

  /** El título ocupa el máximo posible de la ventana, sea cual sea su forma. */
  private fitTitleImage(): void {
    const title = this.assets.images['titulo'];
    if (title) this.titleImage = fitImage(title, this.width, this.height);
  }

  /**
   * Imagen de un pensamiento ajustada a la ventana actual. En móvil (pantalla táctil o vertical)
   * ocupa el máximo posible; en escritorio deja el margen `factor` para ver el mapa alrededor.
   * `reserveY` es la altura que se deja libre abajo para los subtítulos.
   */
  private thoughtImage(name: string, factor: number, reserveY = 0): Canvas | null {
    const img = this.assets.images[name];
    if (!img) return null;
    const full = this.height > this.width || (typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches);
    const f = full ? 1 : factor;
    return fitImage(img, this.width * f, (this.height - reserveY) * f);
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
    // Puntero (ratón o dedo): un toque corto va a una celda; arrastrar desplaza la vista
    const toLogical = (e: PointerEvent): [number, number] => {
      const rect = this.canvas.getBoundingClientRect();
      return [((e.clientX - rect.left) * this.width) / rect.width, ((e.clientY - rect.top) * this.height) / rect.height];
    };
    const stage = this.canvas.parentElement ?? document.body;
    const pad = new AdaptivePad(stage);
    this.cleanups.push(() => pad.dispose());
    let drag: {
      id: number;
      startX: number;
      startY: number;
      lastX: number;
      lastY: number;
      dragged: boolean;
      /** Toque táctil en el cuadrante inferior izquierdo: puede abrir la cruceta adaptativa. */
      padCandidate: boolean;
      padActive: boolean;
      startClientX: number;
      startClientY: number;
      clientX: number;
      clientY: number;
      holdTimer: number;
      repeatTimer: number;
      directions: Direction[];
      nextStepAt: number;
    } | null = null;

    const closePad = () => {
      this.resetPadSteps();
      if (!drag) return;
      window.clearTimeout(drag.holdTimer);
      window.clearInterval(drag.repeatTimer);
      if (drag.padActive) pad.hide();
      drag.padActive = false;
    };
    const openPad = () => {
      if (!drag || drag.padActive) return;
      const rect = this.canvas.getBoundingClientRect();
      drag.padActive = true;
      drag.dragged = true; // ya no es un toque: al soltar no se manda a una celda
      pad.show(drag.startClientX - rect.left, drag.startClientY - rect.top);
      // Mientras se mantiene el dedo desplazado, da un paso cada vez que acaba el anterior
      drag.repeatTimer = window.setInterval(() => {
        if (!drag || drag.directions.length === 0 || this.autoMoveBlocked()) return;
        const now = ticks();
        if (now < drag.nextStepAt) return;
        drag.nextStepAt = now + this.playerWalkDuration;
        this.padStep(drag.directions);
      }, 50);
    };
    const updatePadDirection = () => {
      if (!drag?.padActive) return;
      drag.directions = padDirections(drag.clientX - drag.startClientX, drag.clientY - drag.startClientY);
      pad.setActive(drag.directions);
    };

    // Pellizco con dos dedos: separar acerca (como +) y juntar aleja (como -)
    const touches = new Map<number, { x: number; y: number }>();
    let pinchDistance: number | null = null;
    const touchDistance = (): number => {
      const [a, b] = [...touches.values()];
      return Math.hypot(a.x - b.x, a.y - b.y);
    };

    const onPointerDown = (e: PointerEvent) => {
      if (e.pointerType === 'mouse' && e.button !== 0) return;
      if (e.pointerType === 'touch') {
        touches.set(e.pointerId, { x: e.clientX, y: e.clientY });
      }
      // Un toque o clic cancela el pensamiento activo (y no hace nada más)
      if (this.audio.thoughtActive && !this.showingTitle && !this.showingGameOver) {
        this.audio.cancelThought();
        closePad();
        drag = null;
        return;
      }
      if (e.pointerType === 'touch') {
        if (touches.size >= 2) {
          // El segundo dedo anula el toque, el arrastre o la cruceta en curso
          closePad();
          drag = null;
          pinchDistance = touchDistance();
          return;
        }
      }
      closePad();
      const [x, y] = toLogical(e);
      const padCandidate = e.pointerType === 'touch' && !this.showingTitle && !this.showingGameOver && x < this.width / 2 && y > this.height / 2;
      drag = {
        id: e.pointerId,
        startX: x,
        startY: y,
        lastX: x,
        lastY: y,
        dragged: false,
        padCandidate,
        padActive: false,
        startClientX: e.clientX,
        startClientY: e.clientY,
        clientX: e.clientX,
        clientY: e.clientY,
        holdTimer: 0,
        repeatTimer: 0,
        directions: [],
        nextStepAt: 0,
      };
      if (padCandidate) drag.holdTimer = window.setTimeout(openPad, PAD_HOLD_MS);
      this.canvas.setPointerCapture(e.pointerId);
    };
    const onPointerMove = (e: PointerEvent) => {
      if (touches.has(e.pointerId)) touches.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pinchDistance !== null) {
        if (touches.size < 2 || this.showingTitle || this.showingGameOver) return;
        const distance = touchDistance();
        if (distance > pinchDistance * PINCH_STEP) {
          this.zoomIn();
          pinchDistance = distance;
        } else if (distance < pinchDistance / PINCH_STEP) {
          this.zoomOut();
          pinchDistance = distance;
        }
        return;
      }
      if (!drag || e.pointerId !== drag.id) return;
      const [x, y] = toLogical(e);
      drag.clientX = e.clientX;
      drag.clientY = e.clientY;
      if (drag.padCandidate) {
        // Un arrastre corto (o mantener pulsado) abre la cruceta en vez de desplazar la vista
        if (!drag.padActive && Math.hypot(x - drag.startX, y - drag.startY) >= 10) {
          openPad();
        }
        updatePadDirection();
        return;
      }
      if (!drag.dragged && Math.hypot(x - drag.startX, y - drag.startY) < 10) return;
      drag.dragged = true;
      this.panCamera(x - drag.lastX, y - drag.lastY);
      drag.lastX = x;
      drag.lastY = y;
    };
    const endTouch = (e: PointerEvent): boolean => {
      touches.delete(e.pointerId);
      if (pinchDistance === null) return false;
      // Al terminar el pellizco, el dedo que queda no cuenta como toque
      if (touches.size === 0) pinchDistance = null;
      return true;
    };
    const onPointerUp = (e: PointerEvent) => {
      if (endTouch(e)) return;
      if (!drag || e.pointerId !== drag.id) return;
      closePad();
      const wasDrag = drag.dragged;
      drag = null;
      if (!wasDrag) {
        const [x, y] = toLogical(e);
        this.clickQueue.push({ x, y });
      }
    };
    const onPointerCancel = (e: PointerEvent) => {
      endTouch(e);
      closePad();
      drag = null;
    };
    const observer = new ResizeObserver(() => this.resizeTo(this.canvas.clientWidth, this.canvas.clientHeight));
    observer.observe(this.canvas);
    this.cleanups.push(() => observer.disconnect());
    window.addEventListener('keydown', onKeyDown);
    this.canvas.addEventListener('pointerdown', onPointerDown);
    this.canvas.addEventListener('pointermove', onPointerMove);
    this.canvas.addEventListener('pointerup', onPointerUp);
    this.canvas.addEventListener('pointercancel', onPointerCancel);
    this.cleanups.push(
      () => window.removeEventListener('keydown', onKeyDown),
      () => this.canvas.removeEventListener('pointerdown', onPointerDown),
      () => this.canvas.removeEventListener('pointermove', onPointerMove),
      () => this.canvas.removeEventListener('pointerup', onPointerUp),
      () => this.canvas.removeEventListener('pointercancel', onPointerCancel),
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
        images: this.imageSlot(this.thoughtImage('profundo', 0.9, 200), duration + 1500),
        subtitles: [['¡¡¡AAAARRRRGGGHH!!!!', duration + 1500]],
        blocksMovement: true,
      });
    })();
  }

  fallIntoBarranco(direction: Direction): void {
    if (this.showingGameOver) return;
    console.log('[GAME OVER] El jugador ha caído por el barranco.');
    // La caída mata al instante, tenga los corazones que tenga
    this.playerHealth = 0;

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

  /** Celdas visibles en horizontal y en vertical (incluida la celda parcial del borde). */
  get viewCols(): number {
    return Math.ceil(this.width / this.cellSize);
  }

  get viewRows(): number {
    return Math.ceil(this.height / this.cellSize);
  }

  /**
   * Ajusta el lienzo a la ventana: el lado corto mide 630 y el largo se amplía
   * para dibujar todas las celdas que quepan (sin bandas negras).
   */
  resizeTo(cssWidth: number, cssHeight: number): void {
    if (cssWidth <= 0 || cssHeight <= 0) return;
    const aspect = cssWidth / cssHeight;
    const long = Math.round(this.fixedWindowSize * Math.min(Math.max(aspect, 1 / aspect), 4));
    this.width = aspect >= 1 ? long : this.fixedWindowSize;
    this.height = aspect >= 1 ? this.fixedWindowSize : long;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.fitTitleImage();
    this.updateCameraTarget();
  }

  /** Desplazamiento de cámara (en celdas) que centra la posición `pos` en un eje de `span` píxeles. */
  private cameraTarget(pos: number, span: number): number {
    const cells = span / this.cellSize;
    // Si el tablero es más pequeño que la vista, se centra
    if (this.size <= cells) return (this.size - cells) / 2;
    return Math.max(0, Math.min(pos + 0.5 - cells / 2, this.size - cells));
  }

  /** Interpola la cámara hacia el jugador y devuelve el desplazamiento flotante. */
  getViewOffset(frames: number): [number, number] {
    // Con la vista desplazada a mano la cámara se queda donde está
    if (this.cameraManual) return [this.cameraOffsetRow, this.cameraOffsetCol];
    const [playerRow, playerCol] = this.currentPosition;
    const targetRow = this.cameraTarget(playerRow, this.height);
    const targetCol = this.cameraTarget(playerCol, this.width);

    // Factor equivalente a aplicar `cameraSpeed` una vez por cada frame a 60 fps
    const k = 1 - Math.pow(1 - this.cameraSpeed, frames);
    this.cameraOffsetRow += (targetRow - this.cameraOffsetRow) * k;
    this.cameraOffsetCol += (targetCol - this.cameraOffsetCol) * k;
    return [this.cameraOffsetRow, this.cameraOffsetCol];
  }

  /**
   * Desplaza la vista siguiendo el arrastre (en píxeles lógicos): el personaje
   * queda descentrado y la cámara no lo sigue hasta que vuelva a moverse.
   */
  panCamera(dxPx: number, dyPx: number): void {
    if (this.showingTitle) return;
    this.cameraManual = true;
    const limit = (offset: number, span: number): number => {
      const cells = span / this.cellSize;
      if (this.size <= cells) return (this.size - cells) / 2;
      return Math.max(-2, Math.min(offset, this.size - cells + 2));
    };
    this.cameraOffsetCol = limit(this.cameraOffsetCol - dxPx / this.cellSize, this.width);
    this.cameraOffsetRow = limit(this.cameraOffsetRow - dyPx / this.cellSize, this.height);
  }

  centerCameraInstantly(targetRow: number, targetCol: number): void {
    this.cameraManual = false;
    this.cameraOffsetRow = this.cameraTarget(targetRow, this.height);
    this.cameraOffsetCol = this.cameraTarget(targetCol, this.width);
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

  /** Recentra la cámara (sin interpolar) en el jugador tras cambiar el zoom o el tamaño. */
  updateCameraTarget(): void {
    this.centerCameraInstantly(this.currentPosition[0], this.currentPosition[1]);
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

  /** Última dirección en que se movió la cruceta y dirección que encontró pared en el paso anterior. */
  private padLast: Direction | null = null;
  private padBlocked: Direction | null = null;

  /** ¿Entrar en esa dirección lo precipitaría al barranco? */
  private wouldFall(direction: Direction): boolean {
    const [row, col] = this.currentPosition;
    const [dr, dc] = DELTA[direction];
    return (
      !this.world.board[row][col].exits.has(direction) && this.world.inBounds(row + dr, col + dc) && this.world.isBarrancoCell(row + dr, col + dc)
    );
  }

  private resetPadSteps(): void {
    this.padLast = null;
    this.padBlocked = null;
  }

  /**
   * Un paso con la cruceta. Con dos direcciones (diagonal) se alternan, así que se avanza en
   * escalera. Si una está bloqueada por una pared se usa la otra y se "caracolea" por la pared;
   * en cuanto la dirección bloqueada se abre (una puerta), se entra por ella enseguida.
   * Con una diagonal nunca se elige una dirección que lleve al barranco si hay otra.
   */
  private padStep(directions: readonly Direction[]): void {
    this.cancelAutoMove();
    this.cameraManual = false;
    let order = directions.length > 1 ? directions.filter((d) => !this.wouldFall(d)) : [...directions];
    if (order.length === 0) order = [...directions];
    if (order.length > 1) {
      // Primero la que encontró pared la vez anterior; si no, la contraria a la última (escalera)
      const first = this.padBlocked && order.includes(this.padBlocked) ? this.padBlocked : order.find((d) => d !== this.padLast) ?? order[0];
      order = [first, ...order.filter((d) => d !== first)];
    }
    for (const direction of order) {
      const before = this.currentPosition;
      this.placeCellInDirection(direction);
      if (this.currentPosition !== before || this.showingGameOver) {
        this.padBlocked = order.length > 1 && direction !== order[0] ? order[0] : null;
        this.padLast = direction;
        return;
      }
    }
  }

  /** Mueve al jugador un paso (creando la celda destino si aún no existe). */
  placeCellInDirection(direction: Direction): void {
    if (this.audio.thoughtActive && this.audio.thoughtBlocksMovement) return;
    if (this.exitImageShown && ticks() - this.exitImageStartTime < EXIT_IMAGE_BLOCK_MS) return;

    if (this.fight) return;
    this.playerFacing = direction;
    this.lastMoveAttemptTime = ticks();
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
    this.cameraManual = false; // al moverse, la cámara vuelve a seguir al personaje
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

    // ¿Caminó hacia un monstruo? Empieza la pelea; el resultado llega cuando termina la nube
    for (const monster of this.deepOnes) {
      if (monster.row === row && monster.col === col && !monster.dead) {
        this.startFight(monster);
        if (!this.hasSwordPower && this.fight) {
          this.visitedCells.add(posKey(row, col));
          this.revealAdjacentCells(row, col);
          return;
        }
      }
    }

    this.visitedCells.add(posKey(row, col));
    this.revealAdjacentCells(row, col);

    // Volver al inicio tras visitar la salida: poder de la espada
    if (row === this.startPosition[0] && col === this.startPosition[1] && this.exitVisited && !this.hasSwordPower) {
      this.hasSwordPower = true;
      this.playerHealth = this.maxHealth; // el poder de la espada también cura todos los corazones
      this.thoughtPending = true;
      this.swordThoughtTriggered = true;
      this.audio.startFadeOut(500);
      void this.delayedThought(500, () => {
        this.audio.triggerThought({
          sounds: this.swordSound ? [[this.swordSound, 0]] : [],
          images: this.imageSlot(this.thoughtImage('espada', 0.8), 5000),
          subtitles: [['¡El poder de la espada sagrada! Tus heridas se curan.', 5000]],
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
          images: this.imageSlot(this.thoughtImage('sangre', 0.6), 0),
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
          images: this.imageSlot(this.thoughtImage('antorcha', 0.6), 0),
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
          images: this.imageSlot(this.thoughtImage('losa', 0.9, 120), imageDuration),
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

  /** Empieza la pelea con un monstruo: la nube tapa a ambos y el resultado llega al terminar. */
  private startFight(monster: DeepOne): void {
    if (this.fight || monster.dead) return;
    // Sin la espada, mientras dura la invulnerabilidad el monstruo no puede herirle
    if (!this.hasSwordPower && this.invulnerable) return;
    const now = ticks();
    this.cancelAutoMove();
    monster.alerted = false;
    monster.animating = false;
    monster.state = 'IDLE';
    this.fight = { monster, row: this.currentPosition[0], col: this.currentPosition[1], start: now, shakes: 0 };
    this.triggerCameraShake(1.5, 700);
    this.grunidoSound?.setVolume(0.9);
    this.grunidoSound?.play();
  }

  private updateFight(now: number): void {
    const fight = this.fight;
    if (!fight) return;
    if (this.showingGameOver || this.disposed) {
      this.fight = null;
      return;
    }
    const elapsed = now - fight.start;
    // Sacudidas y gruñidos mientras dura la pelea
    if (fight.shakes < 2 && elapsed > 900 * (fight.shakes + 1)) {
      fight.shakes++;
      this.triggerCameraShake(1.2, 500);
      this.grunidoSound?.play();
    }
    if (elapsed < FIGHT_MS) return;

    this.fight = null;
    const monster = fight.monster;
    if (this.hasSwordPower) {
      if (!monster.dead) {
        monster.dead = true;
        monster.deathTime = now;
        monster.state = 'DEAD';
      }
    } else {
      this.takeDamage();
    }
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
      if (monster.dead || monster === this.fight?.monster) continue;

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

          if (monster.row === this.currentPosition[0] && monster.col === this.currentPosition[1]) this.startFight(monster);
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

  private sheet: CharacterSheet | null = null;

  /** Abre o cierra la hoja de personaje (la partida queda en pausa mientras está abierta). */
  toggleSheet(): void {
    if (this.showingSheet) {
      this.showingSheet = false;
      this.sheet?.hide();
      return;
    }
    if (
      this.showingTitle || this.showingGameOver || this.introAnimActive || this.fight || this.thoughtPending ||
      this.audio.thoughtActive || this.askingExitConfirmation || this.askingMainMenuConfirmation || this.askingRestartConfirmation
    ) return;
    this.cancelAutoMove();
    this.sheet ??= new CharacterSheet(
      document.body,
      CLASSES[this.playerClass],
      () => this.toggleSheet(),
      () => ({ hp: this.playerHealth, maxHp: this.maxHealth, swordPower: this.hasSwordPower, explored: this.visitedCells.size }),
    );
    this.showingSheet = true;
    this.sheet.show();
  }

  returnToMainMenu(): void {
    this.showingTitle = true;
    this.askingMainMenuConfirmation = false;
    this.askingRestartConfirmation = false;
    if (this.showingSheet) this.toggleSheet();
    this.audio.stopMusic();
    if (this.audio.thoughtActive) this.audio.cancelThought();
  }

  teleportTo(pos: Pos): void {
    this.currentPosition = pos;
    this.playerAnimating = false;
    this.centerCameraInstantly(pos[0], pos[1]);
    this.visitedCells.add(posKey(pos[0], pos[1]));
  }

  // --- Movimiento automático ----------------------------------------------------

  /** Clic o toque en el lienzo (coordenadas lógicas). */
  private handleClick(x: number, y: number): void {
    if (this.showingGameOver) {
      this.input.handleClick(x, y);
      return;
    }
    // Confirmaciones: los botones Sí/No equivalen a S y N; el resto de la pantalla no hace nada
    if (this.askingExitConfirmation || this.askingMainMenuConfirmation || this.askingRestartConfirmation) {
      const hit = (r: RestartButton) => x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h;
      const buttons = this.confirmButtons;
      if (buttons && hit(buttons.yes)) {
        if (!this.input.handleKey('s')) this.finish(false);
      } else if (buttons && hit(buttons.no)) {
        this.input.handleKey('n');
      }
      return;
    }
    // Tocar el título equivale a pulsar una tecla
    if (this.showingTitle) {
      this.input.handleKey('Enter');
      return;
    }
    const row = Math.floor(this.cameraOffsetRow + y / this.cellSize);
    const col = Math.floor(this.cameraOffsetCol + x / this.cellSize);
    this.startAutoMove(row, col);
  }

  /** Va andando hasta una celda visible si hay camino; un clic nuevo siempre detiene el trayecto anterior. */
  startAutoMove(row: number, col: number): void {
    this.cancelAutoMove();
    if (this.autoMoveBlocked() || !this.world.inBounds(row, col)) return;
    const visited = (r: number, c: number) => this.visitedCells.has(posKey(r, c)) && this.world.board[r][c].cellType !== CellType.EMPTY;
    const path = visited(row, col)
      ? this.world.findPath(this.currentPosition, [row, col], visited)
      : this.pathToUnrevealed(row, col, visited);
    if (!path || path.length === 0) return;
    this.autoPath = path;
    this.autoTarget = [row, col];
    this.autoNextStepTime = 0;
  }

  /**
   * Camino hasta una celda sin revelar contigua a una revelada: va a la vecina
   * revelada más cercana que tenga salida hacia ella y luego entra en la celda.
   */
  private pathToUnrevealed(row: number, col: number, visited: (r: number, c: number) => boolean): Pos[] | null {
    const world = this.world;
    if (world.isBarrancoCell(row, col) || world.isBridgeCell(row, col)) return null;
    let best: Pos[] | null = null;
    for (const direction of DIRECTIONS) {
      const [dr, dc] = DELTA[direction];
      // Vecina desde la que se entra a la celda pulsada
      const nr = row - dr;
      const nc = col - dc;
      if (!world.inBounds(nr, nc) || !visited(nr, nc) || !world.board[nr][nc].exits.has(direction)) continue;
      const steps = world.findPath(this.currentPosition, [nr, nc], visited);
      if (steps && (!best || steps.length < best.length)) best = steps;
    }
    return best && [...best, [row, col]];
  }

  cancelAutoMove(): void {
    this.autoPath = [];
    this.autoTarget = null;
  }

  private autoMoveBlocked(): boolean {
    return (
      this.showingTitle ||
      this.showingGameOver ||
      this.introAnimActive ||
      this.thoughtPending ||
      this.askingExitConfirmation ||
      this.askingMainMenuConfirmation ||
      this.askingRestartConfirmation ||
      this.showingSheet ||
      this.fight !== null ||
      (this.audio.thoughtActive && this.audio.thoughtBlocksMovement) ||
      (this.exitImageShown && ticks() - this.exitImageStartTime < EXIT_IMAGE_BLOCK_MS)
    );
  }

  private updateAutoMove(now: number): void {
    if (!this.autoTarget) return;
    // Un pensamiento, diálogo o el fin de la partida interrumpen el trayecto
    if (this.autoMoveBlocked()) {
      this.cancelAutoMove();
      return;
    }
    if (now < this.autoNextStepTime) return;

    const next = this.autoPath[0];
    const [row, col] = this.currentPosition;
    const direction: Direction = next[0] < row ? 'N' : next[0] > row ? 'S' : next[1] > col ? 'E' : 'O';
    const health = this.playerHealth;
    this.placeCellInDirection(direction);

    // Si no se llegó a la celda prevista (bloqueo, monstruo...) o hubo daño, se detiene
    if (this.currentPosition[0] !== next[0] || this.currentPosition[1] !== next[1] || this.playerHealth < health) {
      this.cancelAutoMove();
      return;
    }
    this.autoPath.shift();
    this.autoNextStepTime = now + this.playerWalkDuration;
    if (this.autoPath.length === 0) this.cancelAutoMove();
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
    this.sheet?.dispose();
    this.sheet = null;
    this.audio.dispose();
    // Nada de la partida anterior debe seguir sonando (pasos, gritos, gruñidos, ambiente...)
    this.assets.mixer.stopAll();
    this.resolveRun?.(restart);
    this.resolveRun = null;
  }

  /**
   * Un fotograma. Si algo falla dentro, el error se muestra en pantalla y el bucle sigue: antes una sola
   * excepción dejaba el juego congelado en el último dibujo, sin forma de salir.
   */
  private frame = (): void => {
    if (this.disposed) return;
    try {
      if (!this.tick()) return;
    } catch (error) {
      reportError(error);
    }
    requestAnimationFrame(this.frame);
  };

  /** Devuelve false cuando la partida termina y no hay que pedir otro fotograma. */
  private tick(): boolean {
    if (this.restartRequested) {
      this.finish(true);
      return false;
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

    if (this.showingSheet && this.showingGameOver) this.toggleSheet();
    if (!this.showingSheet) {
      this.updateFight(now);
      this.updateMonsters();
    }

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
      this.cancelAutoMove(); // cualquier tecla cancela el movimiento automático
      this.cameraManual = false; // y la cámara vuelve al personaje
      if (!this.input.handleKey(ev.key)) running = false;
    }
    for (const click of this.clickQueue.splice(0)) this.handleClick(click.x, click.y);
    this.updateAutoMove(now);

    try {
      this.renderer.draw(frames);
    } catch (error) {
      reportError(error);
    }

    if (!running) {
      this.finish(false);
      return false;
    }
    return true;
  }
}

interface GameKeyEvent {
  key: string;
}
