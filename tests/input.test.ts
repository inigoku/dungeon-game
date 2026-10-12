import { describe, expect, it, vi } from 'vitest';
import { InputHandler, type GameInput } from '../src/input';
import type { Direction } from '../src/models';
import { ticks } from '../src/time';

function fakeGame(overrides: Partial<GameInput> = {}) {
  const moves: Direction[] = [];
  const game = {
    world: { exitPosition: [10, 10] },
    audio: { thoughtActive: false, cancelThought: vi.fn() },
    startPosition: [50, 50],
    showingGameOver: false,
    gameOverStartTime: 0,
    restartButtonRect: null,
    restartRequested: false,
    thoughtPending: false,
    askingExitConfirmation: false,
    askingMainMenuConfirmation: false,
    showingTitle: false,
    introAnimActive: false,
    autoRevealMode: false,
    debugMode: false,
    showPath: false,
    linesDarkeningEnabled: false,
    zoomIn: vi.fn(),
    zoomOut: vi.fn(),
    placeCellInDirection: (d: Direction) => moves.push(d),
    startGame: vi.fn(),
    returnToMainMenu: vi.fn(),
    teleportTo: vi.fn(),
    ...overrides,
  } as unknown as GameInput;
  return { game, moves };
}

describe('InputHandler', () => {
  it('mapea WASD y flechas a direcciones', () => {
    const { game, moves } = fakeGame();
    const input = new InputHandler(game);
    for (const k of ['w', 's', 'd', 'a', 'ArrowUp', 'ArrowDown', 'ArrowRight', 'ArrowLeft']) input.handleKey(k);
    expect(moves).toEqual(['N', 'S', 'E', 'O', 'N', 'S', 'E', 'O']);
  });

  it('no se mueve durante la animación de introducción', () => {
    const { game, moves } = fakeGame({ introAnimActive: true });
    new InputHandler(game).handleKey('w');
    expect(moves).toEqual([]);
  });

  it('en el título cualquier tecla empieza y Escape sale', () => {
    const { game } = fakeGame({ showingTitle: true });
    const input = new InputHandler(game);
    expect(input.handleKey('Enter')).toBe(true);
    expect(game.startGame).toHaveBeenCalledTimes(1);
    expect(input.handleKey('Escape')).toBe(false);
  });

  it('Escape durante el juego cancela el pensamiento o pregunta por el menú', () => {
    const { game } = fakeGame();
    const input = new InputHandler(game);
    input.handleKey('Escape');
    expect(game.askingMainMenuConfirmation).toBe(true);
    expect(input.handleKey('n')).toBe(true);
    expect(game.askingMainMenuConfirmation).toBe(false);

    const thinking = fakeGame({ audio: { thoughtActive: true, cancelThought: vi.fn() } as never });
    new InputHandler(thinking.game).handleKey('Escape');
    expect(thinking.game.audio.cancelThought).toHaveBeenCalled();
    expect(thinking.game.askingMainMenuConfirmation).toBe(false);
  });

  it('confirmar con S vuelve al menú principal', () => {
    const { game } = fakeGame({ askingMainMenuConfirmation: true });
    new InputHandler(game).handleKey('s');
    expect(game.returnToMainMenu).toHaveBeenCalled();
  });

  it('bloquea la entrada mientras se espera un pensamiento', () => {
    const { game, moves } = fakeGame({ thoughtPending: true });
    new InputHandler(game).handleKey('w');
    expect(moves).toEqual([]);
  });

  it('Game Over: ignora todo el primer segundo y luego permite reiniciar con R', () => {
    const { game } = fakeGame({ showingGameOver: true, gameOverStartTime: ticks() });
    const input = new InputHandler(game);
    game.restartButtonRect = { x: 0, y: 0, w: 10, h: 10 };
    expect(input.handleKey('Escape')).toBe(true); // bloqueado el primer segundo
    expect(game.restartRequested).toBe(false);

    game.gameOverStartTime = ticks() - 5000;
    input.handleKey('r');
    expect(game.restartRequested).toBe(true);
    expect(input.handleKey('Escape')).toBe(false); // ahora sí sale
  });

  it('Game Over: R no hace nada si el botón aún no es visible', () => {
    const { game } = fakeGame({ showingGameOver: true, gameOverStartTime: ticks() - 5000 });
    new InputHandler(game).handleKey('r');
    expect(game.restartRequested).toBe(false);
  });

  it('el clic en el botón de reiniciar lo activa', () => {
    const { game } = fakeGame({ showingGameOver: true });
    game.restartButtonRect = { x: 10, y: 10, w: 100, h: 40 };
    const input = new InputHandler(game);
    input.handleClick(5, 5);
    expect(game.restartRequested).toBe(false);
    input.handleClick(50, 30);
    expect(game.restartRequested).toBe(true);
  });

  it('las teclas de función alternan modos y teletransportan', () => {
    const { game } = fakeGame();
    const input = new InputHandler(game);
    input.handleKey('F2');
    input.handleKey('F3');
    input.handleKey('F4');
    input.handleKey('F5');
    expect([game.autoRevealMode, game.debugMode, game.showPath, game.linesDarkeningEnabled]).toEqual([true, true, true, true]);
    input.handleKey('F6');
    input.handleKey('F7');
    expect(game.teleportTo).toHaveBeenNthCalledWith(1, [50, 50]);
    expect(game.teleportTo).toHaveBeenNthCalledWith(2, [10, 10]);
    input.handleKey('z');
    input.handleKey('x');
    expect(game.zoomIn).toHaveBeenCalled();
    expect(game.zoomOut).toHaveBeenCalled();
  });
});
