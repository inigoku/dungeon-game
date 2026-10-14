/** Manejo de teclado y ratón, desacoplado del juego. */
import type { AudioManager } from './audio';
import type { Direction, Pos } from './models';
import { ticks } from './time';
import type { World } from './world';

/** Lo que el manejador de entrada necesita del juego. */
export interface GameInput {
  readonly world: World;
  readonly audio: AudioManager;
  readonly startPosition: Pos;
  showingGameOver: boolean;
  gameOverStartTime: number;
  restartButtonRect: { x: number; y: number; w: number; h: number } | null;
  restartRequested: boolean;
  thoughtPending: boolean;
  askingExitConfirmation: boolean;
  askingMainMenuConfirmation: boolean;
  askingRestartConfirmation: boolean;
  showingSheet: boolean;
  showingTitle: boolean;
  introAnimActive: boolean;
  autoRevealMode: boolean;
  debugMode: boolean;
  showPath: boolean;
  linesDarkeningEnabled: boolean;
  zoomIn(): void;
  zoomOut(): void;
  placeCellInDirection(direction: Direction): void;
  startGame(): void;
  returnToMainMenu(): void;
  toggleSheet(): void;
  teleportTo(pos: Pos): void;
}

const DIR_MAP: Record<string, Direction> = {
  ArrowUp: 'N',
  ArrowDown: 'S',
  ArrowRight: 'E',
  ArrowLeft: 'O',
  w: 'N',
  s: 'S',
  d: 'E',
  a: 'O',
};

export class InputHandler {
  constructor(private readonly game: GameInput) {}

  /** Procesa una tecla (letras en minúscula). Devuelve false si el juego debe terminar. */
  handleKey(key: string): boolean {
    const game = this.game;

    // 0. Game Over (máxima prioridad)
    if (game.showingGameOver) {
      // Se bloquea todo durante el primer segundo (mordisco / caída)
      if (ticks() - game.gameOverStartTime < 1000) return true;
      if (key === 'r' && game.restartButtonRect) {
        game.restartRequested = true;
        return true;
      }
      return key !== 'Escape';
    }

    // Hoja de personaje abierta: Escape o C la cierran y el resto de teclas se ignora
    if (game.showingSheet) {
      if (key === 'Escape' || key === 'c') game.toggleSheet();
      return true;
    }

    // Entrada bloqueada mientras se espera un pensamiento
    if (game.thoughtPending) return true;

    // 1. Confirmaciones modales
    if (game.askingExitConfirmation) {
      if (key === 's') return false;
      if (key === 'n' || key === 'Escape') game.askingExitConfirmation = false;
      return true;
    }
    if (game.askingRestartConfirmation) {
      if (key === 's') {
        game.askingRestartConfirmation = false;
        game.restartRequested = true;
      } else if (key === 'n' || key === 'Escape') game.askingRestartConfirmation = false;
      return true;
    }
    if (game.askingMainMenuConfirmation) {
      if (key === 's') game.returnToMainMenu();
      else if (key === 'n' || key === 'Escape') game.askingMainMenuConfirmation = false;
      return true;
    }

    // 2. Pantalla de título
    if (game.showingTitle) {
      if (key === 'Escape') return false;
      game.startGame();
      return true;
    }

    // 3. Cualquier tecla cancela el pensamiento activo (y no hace nada más)
    if (game.audio.thoughtActive) {
      game.audio.cancelThought();
      return true;
    }

    // 4. Controles generales
    if (key === 'Escape') {
      game.askingMainMenuConfirmation = true;
      return true;
    }

    switch (key) {
      case 'F2':
        game.autoRevealMode = !game.autoRevealMode;
        break;
      case 'F3':
        game.debugMode = !game.debugMode;
        break;
      case 'F4':
        game.showPath = !game.showPath;
        break;
      case 'F5':
        game.linesDarkeningEnabled = !game.linesDarkeningEnabled;
        break;
      case 'F6':
        game.teleportTo(game.startPosition);
        break;
      case 'F7':
        game.teleportTo(game.world.exitPosition);
        break;
      case 'r':
        if (!game.introAnimActive) game.askingRestartConfirmation = true;
        break;
      case 'c':
        game.toggleSheet();
        break;
      case 'z':
        game.zoomIn();
        break;
      case 'x':
        game.zoomOut();
        break;
      default:
        break;
    }

    // 5. Movimiento (bloqueado durante la animación de introducción)
    if (!game.introAnimActive && Object.hasOwn(DIR_MAP, key)) game.placeCellInDirection(DIR_MAP[key]);
    return true;
  }

  /** Clic en el botón de reiniciar (coordenadas del lienzo). */
  handleClick(x: number, y: number): void {
    const rect = this.game.restartButtonRect;
    if (!this.game.showingGameOver || !rect) return;
    if (x >= rect.x && x < rect.x + rect.w && y >= rect.y && y < rect.y + rect.h) this.game.restartRequested = true;
  }
}
