/** Dibujado del juego sobre el lienzo: celdas, sprites, superposiciones y pantallas. */
import {
  drawBarrancoDoorCorners,
  drawBrokenLine,
  drawCliffSide,
  drawRoughFloor,
  drawStoneInWalls,
} from './effects';
import {
  drawBloodStains,
  drawCobwebs,
  drawDustParticles,
  drawFountain,
  drawSpiralStairs,
  drawTorches,
  drawWetFootprints,
} from './decorations';
import type { DeepOne, Game } from './game';
import { PLAYER_PALETTE } from './game';
import {
  arc,
  circle,
  context2d,
  createCanvas,
  ellipse,
  fillRect,
  font,
  gray,
  line,
  polygon,
  rgb,
  strokeRect,
  type Canvas,
  type Ctx,
  type RGB,
} from './gfx';
import { CellType, DELTA, oppositeDirection, posKey, type Cell, type Direction } from './models';
import { seeded } from './rng';
import { ticks } from './time';

interface CachedTexture {
  sig: number;
  type: CellType;
  canvas: Canvas;
}

const MAX_TEXTURE_CACHE = 900;

function exitsSignature(cell: Cell): number {
  let sig = 0;
  if (cell.exits.has('N')) sig |= 1;
  if (cell.exits.has('E')) sig |= 2;
  if (cell.exits.has('S')) sig |= 4;
  if (cell.exits.has('O')) sig |= 8;
  return sig;
}

export class Renderer {
  private readonly ctx: Ctx;
  private readonly textureCache = new Map<string, CachedTexture>();

  constructor(private readonly game: Game) {
    this.ctx = game.ctx;
  }

  private get cellSize(): number {
    return this.game.cellSize;
  }

  // ---------------------------------------------------------------------------
  // Fotograma completo
  // ---------------------------------------------------------------------------

  /** Dibuja un fotograma. `frames` = fotogramas de 60 fps transcurridos (para la cámara). */
  draw(frames: number): void {
    const g = this.game;
    const ctx = this.ctx;

    if (g.showingTitle) {
      this.drawTitle();
      return;
    }

    fillRect(ctx, [0, 0, 0], 0, 0, g.width, g.height);

    let [offsetRow, offsetCol] = g.getViewOffset(frames);

    // Temblor de cámara
    if (g.shakeDuration > 0) {
      const elapsed = ticks() - g.shakeStartTime;
      if (elapsed < g.shakeDuration) {
        const intensity = g.shakeIntensity * (1 - elapsed / g.shakeDuration);
        offsetRow += (Math.random() * 2 - 1) * intensity;
        offsetCol += (Math.random() * 2 - 1) * intensity;
      } else {
        g.shakeDuration = 0;
      }
    }

    // Desplazamiento en píxeles para el scroll suave
    const offsetRowInt = Math.trunc(offsetRow);
    const offsetColInt = Math.trunc(offsetCol);
    const pixelOffsetY = Math.trunc((offsetRow - offsetRowInt) * this.cellSize);
    const pixelOffsetX = Math.trunc((offsetCol - offsetColInt) * this.cellSize);

    // Una celda extra en cada dirección para el scroll
    for (let row = -1; row <= g.viewSize; row++) {
      for (let col = -1; col <= g.viewSize; col++) {
        const boardRow = offsetRowInt + row;
        const boardCol = offsetColInt + col;
        if (g.world.inBounds(boardRow, boardCol)) this.drawCell(boardRow, boardCol, row, col, pixelOffsetX, pixelOffsetY);
      }
    }

    this.drawBarriers(offsetRow, offsetCol);

    if (g.showingGameOver) {
      // El jugador muerto se dibuja antes que los monstruos (que lo tapan)
      this.drawPlayer(offsetRow, offsetCol);
      this.drawMonsters(offsetRow, offsetCol);
    } else {
      this.drawMonsters(offsetRow, offsetCol);
      this.drawPlayer(offsetRow, offsetCol);
    }

    this.drawFlyingBat(offsetRow, offsetCol);
    this.drawExitSlabOverlay(offsetRow, offsetCol);

    if (g.debugMode) this.drawDebugInfo();
    this.drawSubtitles();

    // Imagen del pensamiento activo, centrada
    if (g.audio.showingImage && g.audio.imageSurface) {
      const img = g.audio.imageSurface;
      ctx.drawImage(img, Math.floor((g.width - img.width) / 2), Math.floor((g.height - img.height) / 2));
    }

    if (g.askingExitConfirmation) this.drawConfirmation('¿Salir del juego?', 400, 48);
    if (g.askingMainMenuConfirmation) this.drawConfirmation('¿Volver al menú principal?', 450, 40);
    if (g.showingGameOver) this.drawGameOver();

    this.drawDangerOverlay();
    if (g.flashActive) this.drawScreenFlash();
  }

  private drawTitle(): void {
    const g = this.game;
    const ctx = this.ctx;
    if (g.titleImage) {
      ctx.drawImage(g.titleImage, 0, 0);
      return;
    }
    fillRect(ctx, [0, 0, 0], 0, 0, g.width, g.height);
    this.text('DUNGEON GAME', g.width / 2, g.height / 2 - 30, 72, [255, 215, 0], 'center');
    this.text('Pulsa cualquier tecla para empezar', g.width / 2, g.height / 2 + 50, 36, [200, 200, 200], 'center');
  }

  private text(s: string, x: number, y: number, size: number, color: RGB, align: CanvasTextAlign = 'left', alpha = 1): void {
    const ctx = this.ctx;
    ctx.font = font(size);
    ctx.textAlign = align;
    ctx.textBaseline = 'middle';
    ctx.fillStyle = rgb(color, alpha);
    ctx.fillText(s, x, y);
  }

  private measure(s: string, size: number): number {
    this.ctx.font = font(size);
    return this.ctx.measureText(s).width;
  }

  // ---------------------------------------------------------------------------
  // Celdas
  // ---------------------------------------------------------------------------

  /** Pinta una celda de barranco: abismo negro con el borde del acantilado hacia el lado accesible. */
  private drawBarrancoCell(x: number, y: number): void {
    const ctx = this.ctx;
    const size = this.cellSize;
    fillRect(ctx, [4, 4, 5], x, y, size, size);

    const edgeDir = this.game.world.getBarrancoAccessibleEdgeDirection();
    const t = Math.max(2, Math.trunc(size * 0.05));
    const edge: RGB = [26, 22, 20];
    if (edgeDir === 'N') fillRect(ctx, edge, x, y, size, t);
    else if (edgeDir === 'S') fillRect(ctx, edge, x, y + size - t, size, t);
    else if (edgeDir === 'O') fillRect(ctx, edge, x, y, t, size);
    else fillRect(ctx, edge, x + size - t, y, t, size);

    // F4: resaltar el barranco en rojo
    if (this.game.showPath) fillRect(ctx, [255, 0, 0], x, y, size, size, 120 / 255);
  }

  /** Puente volante: tablones y cuerdas de borde a borde sobre el vacío. */
  private drawBridgeCell(x: number, y: number): void {
    const ctx = this.ctx;
    const size = this.cellSize;
    fillRect(ctx, [4, 4, 5], x, y, size, size);

    const wood: RGB = [94, 64, 36];
    const woodDark: RGB = [60, 40, 22];
    const rope: RGB = [150, 120, 70];
    const plankGap = Math.max(10, Math.trunc(size * 0.12));

    if (this.game.world.barrancoAxis === 'row') {
      const deckW = Math.trunc(size * 0.42);
      const deckX = x + Math.floor((size - deckW) / 2);
      fillRect(ctx, wood, deckX, y, deckW, size);
      for (let py = 0; py < size; py += plankGap) line(ctx, woodDark, deckX, y + py, deckX + deckW, y + py, 3);
      line(ctx, rope, deckX, y, deckX, y + size, 4);
      line(ctx, rope, deckX + deckW, y, deckX + deckW, y + size, 4);
    } else {
      const deckH = Math.trunc(size * 0.42);
      const deckY = y + Math.floor((size - deckH) / 2);
      fillRect(ctx, wood, x, deckY, size, deckH);
      for (let px = 0; px < size; px += plankGap) line(ctx, woodDark, x + px, deckY, x + px, deckY + deckH, 3);
      line(ctx, rope, x, deckY, x + size, deckY, 4);
      line(ctx, rope, x, deckY + deckH, x + size, deckY + deckH, 4);
    }
  }

  /**
   * Textura de suelo + paredes de una celda, horneada una vez y cacheada: el
   * patrón es fijo (semilla = posición), solo cambia con las salidas o el brillo.
   */
  private getCellTexture(
    boardRow: number,
    boardCol: number,
    cell: Cell,
    floorColor: RGB,
    wallBrightness: number,
    drawFullFloor: boolean,
    background: RGB | null,
  ): Canvas {
    const size = this.cellSize;
    const wb = Math.trunc(wallBrightness);
    const bg = background ?? floorColor;
    const key = `${boardRow},${boardCol},${size},${floorColor[0]},${wb},${drawFullFloor ? 1 : 0},${bg.join('-')}`;
    const sig = exitsSignature(cell);
    const cached = this.textureCache.get(key);
    if (cached && cached.sig === sig && cached.type === cell.cellType) return cached.canvas;

    const inset = Math.trunc(size * 0.15);
    const insetSize = size - 2 * inset;
    const canvas = createCanvas(size, size);
    const ctx = context2d(canvas);

    if (drawFullFloor) drawRoughFloor(ctx, 0, 0, size, size, floorColor, boardRow, boardCol);
    else fillRect(ctx, bg, 0, 0, size, size);
    drawStoneInWalls(ctx, size, boardRow, boardCol, 0, 0, cell, wb, null);
    if (insetSize > 0) drawRoughFloor(ctx, inset, inset, insetSize, insetSize, floorColor, boardRow, boardCol);

    this.textureCache.set(key, { sig, type: cell.cellType, canvas });
    if (this.textureCache.size > MAX_TEXTURE_CACHE) {
      // Expulsa las más antiguas (el orden de inserción del Map)
      let toDrop = this.textureCache.size - MAX_TEXTURE_CACHE + 150;
      for (const k of this.textureCache.keys()) {
        if (toDrop-- <= 0) break;
        this.textureCache.delete(k);
      }
    }
    return canvas;
  }

  private drawFloorAndWalls(
    boardRow: number,
    boardCol: number,
    x: number,
    y: number,
    cell: Cell,
    floorColor: RGB,
    brightnessFactor: number,
    drawFullFloor = true,
    background: RGB | null = null,
  ): void {
    const g = this.game;
    const ctx = this.ctx;
    const size = this.cellSize;
    const barrancoDirs = g.world.barrancoFacingDirections(boardRow, boardCol);

    // Las celdas junto al barranco se dibujan en vivo para integrarse con el acantilado
    if (barrancoDirs.length > 0) {
      const inset = Math.trunc(size * 0.15);
      if (drawFullFloor) drawRoughFloor(ctx, x, y, size, size, floorColor, boardRow, boardCol);
      else if (background) fillRect(ctx, background, x, y, size, size);
      const torchCount = g.countTorches(boardRow, boardCol, cell);
      const wallBrightness = Math.trunc((20 + Math.min(120, torchCount * 30)) * brightnessFactor);
      drawStoneInWalls(ctx, size, boardRow, boardCol, x, y, cell, wallBrightness, barrancoDirs);
      drawRoughFloor(ctx, x + inset, y + inset, size - 2 * inset, size - 2 * inset, floorColor, boardRow, boardCol);
      // El acantilado va el último para quedar sólido
      for (const dir of barrancoDirs) drawCliffSide(ctx, size, x, y, dir, boardRow, boardCol);
      drawBarrancoDoorCorners(ctx, size, boardRow, boardCol, x, y, cell, barrancoDirs);
      return;
    }

    const torchCount = g.countTorches(boardRow, boardCol, cell);
    const wallBrightness = (20 + Math.min(120, torchCount * 30)) * brightnessFactor;
    const tile = this.getCellTexture(boardRow, boardCol, cell, floorColor, wallBrightness, drawFullFloor, background);
    ctx.drawImage(tile, x, y);
  }

  /** Color de suelo y factor de brillo de una celda ya visitada o revelada. */
  private floorOf(boardRow: number, boardCol: number, cell: Cell): { color: RGB; factor: number } | null {
    const g = this.game;
    switch (cell.cellType) {
      case CellType.INICIO: {
        const b = 4 * 31;
        return { color: gray(b), factor: b / 255 };
      }
      case CellType.PASILLO:
      case CellType.HABITACION: {
        const torchBrightness = Math.min(130, g.countTorches(boardRow, boardCol, cell) * 31);
        const b = Math.max(0, g.baseBrightness(boardRow, boardCol) + torchBrightness);
        return { color: gray(b), factor: b / 255 };
      }
      case CellType.SALIDA: {
        const b = Math.max(0, 40 + Math.min(130, g.countTorches(boardRow, boardCol, cell) * 31));
        return { color: gray(b), factor: b / 255 };
      }
      default:
        return null;
    }
  }

  private drawCell(boardRow: number, boardCol: number, viewRow: number, viewCol: number, pixelOffsetX: number, pixelOffsetY: number): void {
    const g = this.game;
    const ctx = this.ctx;
    const world = g.world;
    const size = this.cellSize;
    const cell = world.board[boardRow][boardCol];
    const x = viewCol * size - pixelOffsetX;
    const y = viewRow * size - pixelOffsetY;

    // El barranco y los puentes no se ven hasta estar junto a ellos
    if (world.isBarrancoCell(boardRow, boardCol)) {
      if (this.isBarrancoRevealed(boardRow, boardCol)) this.drawBarrancoCell(x, y);
      else fillRect(ctx, [0, 0, 0], x, y, size, size);
      return;
    }
    if (world.isBridgeCell(boardRow, boardCol)) {
      if (this.isBarrancoRevealed(boardRow, boardCol)) this.drawBridgeCell(x, y);
      else fillRect(ctx, [0, 0, 0], x, y, size, size);
      return;
    }

    const visited = g.visitedCells.has(posKey(boardRow, boardCol));
    const inPath = world.isInMainPath(boardRow, boardCol);

    // ¿Se revela por F4, o la ilumina una celda visitada del camino con salida hacia ella?
    let revealForPath = false;
    let lightDir: Direction | null = null;
    if (g.showPath && inPath) {
      revealForPath = true;
    } else if (!visited) {
      for (const dir of ['N', 'S', 'E', 'O'] as const) {
        const [dr, dc] = DELTA[dir];
        const ar = boardRow + dr;
        const ac = boardCol + dc;
        if (!world.isInMainPath(ar, ac) || !g.visitedCells.has(posKey(ar, ac))) continue;
        // La vecina mira hacia aquí si tiene la salida opuesta a la dirección en que está
        if (world.board[ar][ac].exits.has(oppositeDirection(dir))) {
          lightDir = dir;
          break;
        }
      }
    }

    if (!visited) {
      if (revealForPath) {
        /* se renderiza normalmente con la superposición de F4 */
      } else if (lightDir) {
        this.drawLitFogCell(boardRow, boardCol, cell, x, y, lightDir);
        return;
      } else {
        fillRect(ctx, [0, 0, 0], x, y, size, size);
        return;
      }
    }

    // 1. Suelo y paredes según el tipo de celda
    let floorColor: RGB = [0, 0, 0];
    let brightnessFactor = 0;
    const floor = this.floorOf(boardRow, boardCol, cell);
    if (floor) {
      floorColor = floor.color;
      brightnessFactor = floor.factor;
      if (cell.cellType === CellType.SALIDA) {
        const wall = Math.trunc(50 * brightnessFactor);
        this.drawFloorAndWalls(boardRow, boardCol, x, y, cell, floorColor, brightnessFactor, false, [wall, wall, wall]);
      } else {
        this.drawFloorAndWalls(boardRow, boardCol, x, y, cell, floorColor, brightnessFactor);
      }
    }

    // 2. Superposición de F4 sobre el camino principal
    if (g.showPath && inPath) fillRect(ctx, [0, 100, 255], x, y, size, size, 80 / 255);

    // 3. Líneas del interior de la celda
    if (cell.cellType !== CellType.EMPTY) this.drawInnerLines(boardRow, boardCol, x, y, cell, floorColor);

    // 4. Conexiones entre celdas
    if (cell.cellType !== CellType.EMPTY) this.drawExits(boardRow, boardCol, x, y, cell.exits);

    // 5. Sangre, huellas, fuente/escalera y telarañas
    if (cell.cellType === CellType.PASILLO || cell.cellType === CellType.HABITACION || cell.cellType === CellType.SALIDA) {
      drawBloodStains(ctx, size, boardRow, boardCol, x, y, brightnessFactor, world.exitPosition);
    }
    const footprints = g.monsterFootprints.get(posKey(boardRow, boardCol));
    if (footprints) drawWetFootprints(ctx, x, y, footprints);

    if (cell.cellType === CellType.INICIO) {
      drawFountain(ctx, size, x, y, brightnessFactor);
      drawDustParticles(ctx, size, x, y, boardRow, boardCol, brightnessFactor);
    } else if (cell.cellType === CellType.SALIDA) {
      drawSpiralStairs(ctx, size, x, y);
    }
    if (cell.cellType === CellType.HABITACION) drawCobwebs(ctx, size, x, y, boardRow, boardCol, brightnessFactor);

    // 6. Antorchas, encima de todo y solo en celdas visitadas
    if (visited && cell.cellType !== CellType.EMPTY) {
      const numTorches = g.countTorches(boardRow, boardCol, cell, false);
      drawTorches(ctx, size, boardRow, boardCol, x, y, cell, numTorches, world.barrancoFacingDirections(boardRow, boardCol));
    }
  }

  private isBarrancoRevealed(row: number, col: number): boolean {
    const visited = this.game.visitedCells;
    if (visited.has(posKey(row, col))) return true;
    return visited.has(posKey(row - 1, col)) || visited.has(posKey(row + 1, col)) || visited.has(posKey(row, col + 1)) || visited.has(posKey(row, col - 1));
  }

  /** Celda sin visitar iluminada desde una vecina visitada: degradado que se apaga hacia dentro. */
  private drawLitFogCell(boardRow: number, boardCol: number, cell: Cell, x: number, y: number, dir: Direction): void {
    const ctx = this.ctx;
    const size = this.cellSize;
    const torchBrightness = Math.min(130, this.game.countTorches(boardRow, boardCol, cell) * 31);
    const brightness = Math.floor(Math.max(0, 10 + torchBrightness) / 2);
    for (let i = 0; i < size; i++) {
      const t = i / size;
      const c = gray(Math.trunc(brightness * (1 - t)));
      if (dir === 'N') fillRect(ctx, c, x, y + i, size, 1);
      else if (dir === 'S') fillRect(ctx, c, x, y + size - 1 - i, size, 1);
      else if (dir === 'E') fillRect(ctx, c, x + size - 1 - i, y, 1, size);
      else fillRect(ctx, c, x + i, y, 1, size);
    }
  }

  /** Líneas quebradas que dibujan el pasillo/sala desde el centro hacia las salidas. */
  private drawInnerLines(row: number, col: number, x: number, y: number, cell: Cell, floorColor: RGB): void {
    const ctx = this.ctx;
    const size = this.cellSize;
    const wide = cell.cellType === CellType.HABITACION || cell.cellType === CellType.INICIO;

    // Para salas e inicio la zona central es más ancha
    const lo = wide ? 0.15 * size : Math.floor((0.8 * size) / 2);
    const hi = wide ? 0.85 * size : Math.floor((1.2 * size) / 2);
    const left = x + lo;
    const right = x + hi;
    const top = y + lo;
    const bottom = y + hi;

    const lineColor: RGB = this.game.linesDarkeningEnabled ? [150, 150, 150] : gray(Math.max(0, floorColor[0] - 20));
    const w = 3;
    const exits = cell.exits;

    if (exits.has('N')) {
      drawBrokenLine(ctx, lineColor, [left, top], [left, y + 0.1 * size], w, row, col, 1);
      drawBrokenLine(ctx, lineColor, [right, top], [right, y + 0.1 * size], w, row, col, 2);
    } else drawBrokenLine(ctx, lineColor, [left, top], [right, top], w, row, col, 3);

    if (exits.has('S')) {
      drawBrokenLine(ctx, lineColor, [left, bottom], [left, y + 0.9 * size], w, row, col, 4);
      drawBrokenLine(ctx, lineColor, [right, bottom], [right, y + 0.9 * size], w, row, col, 5);
    } else drawBrokenLine(ctx, lineColor, [left, bottom], [right, bottom], w, row, col, 6);

    if (exits.has('E')) {
      drawBrokenLine(ctx, lineColor, [right, top], [x + 0.9 * size, top], w, row, col, 7);
      drawBrokenLine(ctx, lineColor, [right, bottom], [x + 0.9 * size, bottom], w, row, col, 8);
    } else drawBrokenLine(ctx, lineColor, [right, top], [right, bottom], w, row, col, 9);

    if (exits.has('O')) {
      drawBrokenLine(ctx, lineColor, [left, top], [x + 0.1 * size, top], w, row, col, 10);
      drawBrokenLine(ctx, lineColor, [left, bottom], [x + 0.1 * size, bottom], w, row, col, 11);
    } else drawBrokenLine(ctx, lineColor, [left, top], [left, bottom], w, row, col, 12);
  }

  /** Brillo del suelo de una celda (0 si está vacía), para los degradados de conexión. */
  private neighborFloorBrightness(row: number, col: number): number {
    const g = this.game;
    const cell = g.world.board[row][col];
    if (cell.cellType === CellType.EMPTY) return 0;
    return g.getCellBrightness(row, col);
  }

  /** Degradado de brillo entre dos celdas conectadas y marcas de salida (modo F5). */
  private drawExits(row: number, col: number, x: number, y: number, exits: ReadonlySet<Direction>): void {
    const g = this.game;
    const ctx = this.ctx;
    const world = g.world;
    const size = this.cellSize;

    for (const direction of ['N', 'S', 'E', 'O'] as const) {
      if (!exits.has(direction)) continue;
      const [dr, dc] = DELTA[direction];
      const nr = row + dr;
      const nc = col + dc;
      if (!world.inBounds(nr, nc)) continue;
      const neighbor = world.board[nr][nc];
      if (neighbor.cellType === CellType.EMPTY || !neighbor.exits.has(oppositeDirection(direction))) continue;

      const b1 = this.neighborFloorBrightness(row, col);
      const b2 = this.neighborFloorBrightness(nr, nc);
      const avg = Math.floor((b1 + b2) / 2);
      const thickness = Math.trunc(size * 0.22);
      const along = Math.trunc(size * 0.44);
      const offset = Math.trunc(size * 0.28);

      if (direction === 'N') this.gradientRect(x + offset, y, along, thickness, avg, b1, true);
      else if (direction === 'S') this.gradientRect(x + offset, y + size - thickness, along, thickness, b1, avg, true);
      else if (direction === 'E') this.gradientRect(x + size - thickness, y + offset, thickness, along, b1, avg, false);
      else this.gradientRect(x, y + offset, thickness, along, avg, b1, false);
    }

    // Marcas de las salidas: solo con el modo de líneas con contraste (F5)
    if (!g.linesDarkeningEnabled) return;

    const exitColor: RGB = [150, 150, 150];
    const thickness = 8;
    const midL = x + Math.floor((0.8 * size) / 2);
    const midR = x + Math.floor((1.2 * size) / 2);
    const midD = y + Math.floor((0.8 * size) / 2);
    const midU = y + Math.floor((1.2 * size) / 2);

    // [id base, línea A, línea B, cruce]
    type Seg = readonly [readonly [number, number], readonly [number, number]];
    const geometry: Record<Direction, { lines: [Seg, Seg]; cross: Seg; ids: [number, number, number] }> = {
      N: {
        lines: [
          [[midL, y], [midL, y + 0.1 * size]],
          [[midR, y], [midR, y + 0.1 * size]],
        ],
        cross: [[midL, y + 0.05 * size], [midR, y + 0.05 * size]],
        ids: [20, 21, 22],
      },
      S: {
        lines: [
          [[midL, y + size], [midL, y + 0.8 * size]],
          [[midR, y + size], [midR, y + 0.8 * size]],
        ],
        cross: [[midL, y + size - 0.05 * size], [midR, y + size - 0.05 * size]],
        ids: [30, 31, 32],
      },
      E: {
        lines: [
          [[x + size, midD], [x + 0.8 * size, midD]],
          [[x + size, midU], [x + 0.8 * size, midU]],
        ],
        cross: [[x + size - 0.05 * size, midD], [x + size - 0.05 * size, midU]],
        ids: [40, 41, 42],
      },
      O: {
        lines: [
          [[x, midD], [x + 0.1 * size, midD]],
          [[x, midU], [x + 0.1 * size, midU]],
        ],
        cross: [[x + 0.05 * size, midD], [x + 0.05 * size, midU]],
        ids: [50, 51, 52],
      },
    };

    for (const direction of ['N', 'S', 'E', 'O'] as const) {
      const [dr, dc] = DELTA[direction];
      const nr = row + dr;
      const nc = col + dc;
      const inside = world.inBounds(nr, nc);
      const neighbor = inside ? world.board[nr][nc] : null;
      const geo = geometry[direction];

      if (exits.has(direction)) {
        const empty = neighbor?.cellType === CellType.EMPTY;
        const connected = !!neighbor && !empty && neighbor.exits.has(oppositeDirection(direction));
        drawBrokenLine(ctx, exitColor, geo.lines[0][0], geo.lines[0][1], thickness, row, col, geo.ids[0]);
        drawBrokenLine(ctx, exitColor, geo.lines[1][0], geo.lines[1][1], thickness, row, col, geo.ids[1]);
        // Salida al borde o hacia una vecina que no la corresponde: tachada
        if (!inside || (!connected && !empty)) {
          drawBrokenLine(ctx, exitColor, geo.cross[0], geo.cross[1], thickness, row, col, geo.ids[2]);
        }
      } else if (neighbor && neighbor.cellType !== CellType.EMPTY && neighbor.exits.has(oppositeDirection(direction))) {
        // La vecina tiene salida hacia aquí pero esta celda no: cruz en el borde
        const mark = geometry[direction].cross;
        line(ctx, exitColor, mark[0][0], mark[0][1], mark[1][0], mark[1][1], 2);
      }
    }
  }

  private gradientRect(x: number, y: number, w: number, h: number, start: number, end: number, vertical: boolean): void {
    if (w <= 0 || h <= 0) return;
    const ctx = this.ctx;
    const count = vertical ? h : w;
    for (let i = 0; i < count; i++) {
      const t = i / Math.max(1, count - 1);
      const b = Math.max(0, Math.min(255, Math.trunc(start + (end - start) * t)));
      ctx.fillStyle = `rgb(${b},${b},${b})`;
      if (vertical) ctx.fillRect(x, y + i, w, 1);
      else ctx.fillRect(x + i, y, 1, h);
    }
  }

  // ---------------------------------------------------------------------------
  // Efectos y superposiciones
  // ---------------------------------------------------------------------------

  /** Barreras mágicas que impiden a los monstruos pisar inicio/salida o salir del camino. */
  private drawBarriers(offsetRow: number, offsetCol: number): void {
    const g = this.game;
    const ctx = this.ctx;
    const size = this.cellSize;
    const now = ticks();
    g.activeBarriers = g.activeBarriers.filter((b) => now - b.startTime < b.duration);

    for (const barrier of g.activeBarriers) {
      const viewRow = barrier.row - offsetRow;
      const viewCol = barrier.col - offsetCol;
      if (viewRow < -1 || viewRow > g.viewSize || viewCol < -1 || viewCol > g.viewSize) continue;

      const x = Math.trunc(viewCol * size);
      const y = Math.trunc(viewRow * size);
      const progress = (now - barrier.startTime) / barrier.duration;
      const alpha = Math.trunc(180 * (1 - progress)) / 255;
      const color: RGB = [100, 200, 255];

      fillRect(ctx, color, x, y, size, size, alpha * 0.3); // resplandor interior
      strokeRect(ctx, color, x, y, size, size, 4, alpha);
      line(ctx, color, x, y, x + size, y + size, 3, alpha);
      line(ctx, color, x + size, y, x, y + size, 3, alpha);
    }
  }

  private drawExitSlabOverlay(offsetRow: number, offsetCol: number): void {
    const g = this.game;
    const ctx = this.ctx;
    const size = this.cellSize;
    const [exitRow, exitCol] = g.world.exitPosition;
    if (!g.visitedCells.has(posKey(exitRow, exitCol))) return;

    const viewRow = exitRow - offsetRow;
    const viewCol = exitCol - offsetCol;
    if (viewRow < -1 || viewRow > g.viewSize || viewCol < -1 || viewCol > g.viewSize) return;

    const x = Math.trunc(viewCol * size);
    const y = Math.trunc(viewRow * size);
    const w = Math.trunc(size * 0.28);
    const h = Math.trunc(size * 0.16);
    const slabX = x + Math.floor((size - w) / 2);
    const slabY = y + Math.floor(size / 2) + Math.trunc(size * 0.13);
    fillRect(ctx, [90, 90, 90], slabX, slabY, w, h);
    strokeRect(ctx, [60, 60, 60], slabX, slabY, w, h, 2);
    for (let i = 0; i < 4; i++) {
      const ry = slabY + Math.trunc(h * (0.25 + 0.15 * i));
      line(ctx, [20, 20, 20], slabX + 6, ry, slabX + w - 6, ry, 1);
    }
  }

  /** Tinte rojo por salud baja y proximidad de monstruos. */
  private drawDangerOverlay(): void {
    const g = this.game;
    if (g.showingGameOver) return;

    let alpha = 0;
    const now = ticks();
    if (g.playerHealth < g.maxHealth) {
      const pulse = (Math.sin(now * 0.005) + 1) * 0.5;
      alpha = 30 + Math.trunc(pulse * 70);
    }
    if (g.hasEncounteredMonsters) {
      let closest = Infinity;
      for (const monster of g.deepOnes) {
        if (monster.dead) continue;
        const dist = Math.abs(monster.row - g.currentPosition[0]) + Math.abs(monster.col - g.currentPosition[1]);
        if (dist < closest) closest = dist;
      }
      if (closest < 6) {
        const proximity = Math.trunc((1 - closest / 6) * 100);
        alpha = Math.min(200, alpha + proximity);
      }
    }
    if (alpha > 0) fillRect(this.ctx, [255, 0, 0], 0, 0, g.width, g.height, alpha / 255);
  }

  private drawScreenFlash(): void {
    const g = this.game;
    const elapsed = ticks() - g.flashStartTime;
    if (elapsed >= g.flashDuration) {
      g.flashActive = false;
      return;
    }
    const alpha = Math.trunc(180 * (1 - elapsed / g.flashDuration));
    fillRect(this.ctx, g.flashColor, 0, 0, g.width, g.height, alpha / 255);
  }

  private drawDebugInfo(): void {
    const g = this.game;
    const ctx = this.ctx;
    const [row, col] = g.currentPosition;
    const [exitRow, exitCol] = g.world.exitPosition;
    const distance = Math.abs(exitRow - row) + Math.abs(exitCol - col);
    const dRow = exitRow - row;
    const dCol = exitCol - col;
    const direction = Math.abs(dRow) > Math.abs(dCol) ? (dRow > 0 ? 'Sur' : 'Norte') : dCol > 0 ? 'Este' : 'Oeste';
    const onPath = g.world.isInMainPath(row, col);

    const lines = [
      `Posición: (${row}, ${col})`,
      `Salida: (${exitRow}, ${exitCol})`,
      `Distancia: ${distance} celdas`,
      `Dirección: ${direction}`,
      `En camino: ${onPath ? 'SÍ' : 'NO'}`,
    ];
    fillRect(ctx, [0, 0, 0], 10, 10, 250, lines.length * 25 + 20, 200 / 255);
    lines.forEach((s, i) => {
      const color: RGB = s.includes('En camino: SÍ') ? [0, 255, 0] : [255, 255, 255];
      this.text(s, 20, 20 + i * 25 + 10, 24, color);
    });
  }

  private drawSubtitles(): void {
    const g = this.game;
    if (!g.audio.showingSubtitles) return;
    const ctx = this.ctx;

    // Dividir el texto en líneas que quepan (margen de 20 px a cada lado)
    const maxWidth = g.width - 40;
    const lines: string[] = [];
    let current: string[] = [];
    for (const word of g.audio.subtitleText.split(' ')) {
      const test = [...current, word].join(' ');
      if (this.measure(test, 32) <= maxWidth) current.push(word);
      else {
        if (current.length > 0) lines.push(current.join(' '));
        current = [word];
      }
    }
    if (current.length > 0) lines.push(current.join(' '));

    const lineHeight = 36;
    const boxHeight = Math.max(80, lines.length * lineHeight + 20);
    fillRect(ctx, [0, 0, 0], 0, g.height - boxHeight, g.width, boxHeight, 160 / 255);
    const startY = g.height - boxHeight + 10;
    lines.forEach((s, i) => this.text(s, Math.floor(g.width / 2), startY + i * lineHeight + lineHeight / 2, 32, [255, 255, 255], 'center'));
  }

  private drawConfirmation(title: string, dialogW: number, titleSize: number): void {
    const g = this.game;
    const ctx = this.ctx;
    fillRect(ctx, [0, 0, 0], 0, 0, g.width, g.height, 180 / 255);
    const dialogH = 150;
    const dx = Math.floor((g.width - dialogW) / 2);
    const dy = Math.floor((g.height - dialogH) / 2);
    fillRect(ctx, [40, 40, 40], dx, dy, dialogW, dialogH);
    strokeRect(ctx, [200, 200, 200], dx, dy, dialogW, dialogH, 3);
    this.text(title, dx + dialogW / 2, dy + 50, titleSize, [255, 255, 255], 'center');
    this.text('S = Sí  /  N = No', dx + dialogW / 2, dy + 105, 32, [200, 200, 200], 'center');
  }

  private drawGameOver(): void {
    const g = this.game;
    const ctx = this.ctx;
    const now = ticks();
    const elapsed = now - g.gameOverStartTime;

    // Primer segundo: pasa a escala de grises poco a poco
    if (elapsed < 1000) {
      const progress = elapsed / 1000;
      ctx.save();
      ctx.filter = `grayscale(${progress})`;
      ctx.drawImage(g.canvas, 0, 0);
      ctx.restore();
      return;
    }

    if (g.audio.thoughtActive) return;

    // GAME OVER parpadeante: 2 s visible, 2 s oculto
    if ((now - g.gameOverStartTime) % 4000 < 2000) {
      const textW = this.measure('GAME OVER', 64);
      const textH = 46;
      const cx = g.width / 2;
      const cy = g.height - 100;
      fillRect(ctx, [0, 0, 0], cx - textW / 2 - 20, cy - textH / 2 - 10, textW + 40, textH + 20, 180 / 255);
      this.text('GAME OVER', cx, cy, 64, [200, 0, 0], 'center');
    }

    if (g.gameOverThoughtFinishedTime > 0) {
      // Fundido a negro durante 10 s
      const fadeElapsed = now - g.gameOverThoughtFinishedTime;
      const fadeDuration = 10000;
      if (fadeElapsed > 0) {
        const alpha = Math.min(255, Math.trunc(255 * (fadeElapsed / fadeDuration)));
        if (alpha > 0) fillRect(ctx, [0, 0, 0], 0, 0, g.width, g.height, alpha / 255);
      }

      // Botón de reiniciar tras el fundido
      if (fadeElapsed > fadeDuration) {
        const alpha = Math.min(255, Math.trunc(255 * ((fadeElapsed - fadeDuration) / 2000))) / 255;
        const w = 200;
        const h = 50;
        const x = Math.floor((g.width - w) / 2);
        const y = Math.floor((g.height - h) / 2) + 100;
        g.restartButtonRect = { x, y, w, h };
        fillRect(ctx, [50, 0, 0], x, y, w, h, alpha);
        strokeRect(ctx, [150, 0, 0], x, y, w, h, 2, alpha);
        this.text('REINICIAR (R)', x + w / 2, y + h / 2, 36, [255, 255, 255], 'center', alpha);
      }
    }
  }

  /** Charco de sangre que se expande lentamente (8 s) con un efecto de líquido. */
  private drawBloodPool(cx: number, cy: number, startTime: number, seed: number): void {
    const progress = Math.min(1, (ticks() - startTime) / 8000);
    if (progress <= 0) return;
    const maxRadius = Math.trunc(this.cellSize * 0.65);
    const radius = Math.trunc(maxRadius * progress);
    if (radius < 1) return;

    const rnd = seeded(seed);
    const t = ticks();
    for (let i = 0; i < 15; i++) {
      const angle = rnd.uniform(0, 2 * Math.PI);
      const dist = radius * Math.sqrt(rnd.random());
      const bx = cx + Math.trunc(dist * Math.cos(angle));
      const by = cy + Math.trunc(dist * Math.sin(angle));
      const pulse = Math.sin(t * 0.005 + i * 13) * 0.15 + 1;
      const blobSize = Math.trunc(radius * rnd.uniform(0.2, 0.5) * pulse);
      const red = rnd.randint(60, 100);
      if (blobSize < 1) continue;
      circle(this.ctx, [red, 0, 0], bx, by, blobSize);
    }
  }

  // ---------------------------------------------------------------------------
  // Monstruos, jugador y murciélago
  // ---------------------------------------------------------------------------

  private drawMonsters(offsetRow: number, offsetCol: number): void {
    const g = this.game;
    const ctx = this.ctx;
    const size = this.cellSize;
    // Muertos primero, para que los vivos se dibujen encima
    const sorted = [...g.deepOnes].sort((a, b) => (a.dead ? 0 : 1) - (b.dead ? 0 : 1));

    for (const monster of sorted) {
      let row = monster.row;
      let col = monster.col;
      if (monster.dead) monster.animating = false;

      if (monster.animating) {
        const t = monster.animDuration > 0 ? Math.min(1, (ticks() - monster.animStartTime) / monster.animDuration) : 1;
        row = monster.fromRow + (monster.row - monster.fromRow) * t;
        col = monster.fromCol + (monster.col - monster.fromCol) * t;
        if (t >= 1) monster.animating = false;
      }

      const viewRow = row - offsetRow;
      const viewCol = col - offsetCol;
      if (viewRow < -1.5 || viewRow > g.viewSize + 0.5 || viewCol < -1.5 || viewCol > g.viewSize + 0.5) continue;

      const centerX = Math.trunc(viewCol * size) + Math.floor(size / 2);
      const centerY = Math.trunc(viewRow * size) + Math.floor(size / 2);
      const spriteSize = Math.trunc(size * 0.45);

      if (monster.dead) {
        this.drawBloodPool(centerX, centerY, monster.deathTime, monster.row * 1000 + monster.col);
        // Cadáver tendido (rotado 90°)
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(-Math.PI / 2);
        this.drawDeepOneSprite(ctx, 0, 0, spriteSize, monster);
        ctx.restore();
        continue;
      }
      this.drawDeepOneSprite(ctx, centerX, centerY, spriteSize, monster);
    }
  }

  /** Sprite de un Profundo (humanoide pez, verde azulado). */
  private drawDeepOneSprite(ctx: Ctx, cx: number, cy: number, size: number, monster: DeepOne | null): void {
    const s = Math.max(8, Math.trunc(size));
    const skin: RGB = [40, 140, 100];
    const skinDark: RGB = [30, 110, 80];
    const belly: RGB = [60, 160, 120];
    const eyeCol: RGB = [255, 230, 50];
    const pupilCol: RGB = [0, 0, 0];
    const mouthCol: RGB = [20, 60, 40];
    const now = ticks();
    const half = (n: number) => Math.floor(n / 2);

    const breath = Math.sin(now * 0.003) * (s * 0.03);
    const bodyW = Math.trunc(s * 0.55);
    const bodyH = Math.trunc(s * 0.65);
    const bodyY = cy - Math.floor(bodyH / 4) + Math.trunc(breath);

    const roaring = monster?.state === 'ROARING';
    const roarT = roaring && monster ? now - monster.stateStartTime : 0;

    // Espinas dorsales
    const spineW = Math.trunc(s * 0.08);
    const spineH = Math.trunc(s * 0.15);
    for (let i = 0; i < 3; i++) {
      const sy = bodyY - half(bodyH) + i * (spineH + 2);
      polygon(ctx, skinDark, [[cx - half(bodyW) + 5, sy + spineH], [cx - half(bodyW) - spineW, sy + half(spineH)], [cx - half(bodyW) + 5, sy]]);
      polygon(ctx, skinDark, [[cx + half(bodyW) - 5, sy + spineH], [cx + half(bodyW) + spineW, sy + half(spineH)], [cx + half(bodyW) - 5, sy]]);
    }

    // Piernas
    const legW = Math.trunc(s * 0.16);
    const legH = Math.trunc(s * 0.45);
    const legY = bodyY + Math.floor(bodyH / 3);
    const walkOffset = monster?.animating ? Math.trunc(Math.sin((now - monster.animStartTime) * 0.02) * (s * 0.1)) : 0;
    ellipse(ctx, skin, cx - Math.floor(bodyW / 4) - half(legW), legY + walkOffset, legW, legH);
    ellipse(ctx, skin, cx + Math.floor(bodyW / 4) - half(legW), legY - walkOffset, legW, legH);

    // Brazos largos
    const armW = Math.trunc(s * 0.14);
    const armH = Math.trunc(s * 0.55);
    if (roaring) {
      const armOffsetY = -Math.trunc(Math.sin(roarT * 0.02) * (s * 0.15)) - s * 0.25;
      ellipse(ctx, skin, cx - half(bodyW) - armW, bodyY + armOffsetY, armW, armH);
      ellipse(ctx, skin, cx + half(bodyW), bodyY + armOffsetY, armW, armH);
    } else {
      ellipse(ctx, skin, cx - half(bodyW) - half(armW), bodyY, armW, armH);
      ellipse(ctx, skin, cx + half(bodyW) - half(armW), bodyY, armW, armH);
    }

    // Cuerpo y vientre
    ellipse(ctx, skin, cx - half(bodyW), bodyY - half(bodyH), bodyW, bodyH);
    ellipse(ctx, belly, cx - Math.floor(bodyW / 3), bodyY - Math.floor(bodyH / 3), Math.floor(bodyW / 1.5), Math.floor(bodyH / 1.5));

    // Escamas
    for (let i = 0; i < 3; i++) {
      const sy = bodyY - Math.floor(bodyH / 4) + i * (s * 0.1);
      arc(ctx, skinDark, cx - s * 0.1, sy, s * 0.2, s * 0.1, 0, 3.14, 1);
    }

    // Cabeza de pez
    const headW = Math.trunc(s * 0.5);
    const headH = Math.trunc(s * 0.55);
    const headY = bodyY - half(bodyH) - Math.floor(headH / 3);
    const crest = Math.trunc(s * 0.1);
    polygon(ctx, skinDark, [[cx, headY - half(headH) - crest], [cx - crest, headY - half(headH) + crest], [cx + crest, headY - half(headH) + crest]]);
    ellipse(ctx, skin, cx - half(headW), headY - half(headH), headW, headH);

    // Boca ancha
    const mouthY = headY + Math.trunc(headH * 0.25);
    const mouthW = Math.trunc(headW * 0.6);
    if (roaring) ellipse(ctx, mouthCol, cx - half(mouthW), mouthY, mouthW, Math.trunc(headH * 0.25));
    else arc(ctx, mouthCol, cx - half(mouthW), mouthY - 5, mouthW, 10, 3.14, 2 * 3.14, 2);

    // Ojos saltones
    const eyeR = Math.trunc(s * 0.13);
    const eyeY = headY - Math.trunc(headH * 0.1);
    const pupilOffset = roaring ? Math.trunc(Math.sin(roarT * 0.015) * (eyeR * 0.5)) : 0;
    const eyeDx = Math.trunc(headW * 0.35);
    const pupilR = Math.max(1, Math.trunc(eyeR * 0.3));
    circle(ctx, eyeCol, cx - eyeDx, eyeY, eyeR);
    circle(ctx, pupilCol, cx - eyeDx + pupilOffset, eyeY, pupilR);
    circle(ctx, eyeCol, cx + eyeDx, eyeY, eyeR);
    circle(ctx, pupilCol, cx + eyeDx + pupilOffset, eyeY, pupilR);

    // Aletas laterales
    const finW = Math.trunc(s * 0.18);
    const finH = Math.trunc(s * 0.25);
    polygon(ctx, skin, [[cx - half(headW) + 5, headY], [cx - half(headW) - finW, headY - half(finH)], [cx - half(headW) - finW, headY + half(finH)]]);
    polygon(ctx, skin, [[cx + half(headW) - 5, headY], [cx + half(headW) + finW, headY - half(finH)], [cx + half(headW) + finW, headY + half(finH)]]);

    // Indicador de alerta (!)
    if (monster?.alerted && !monster.dead) {
      const bob = Math.trunc(Math.sin(now * 0.01) * 2);
      const alertY = headY - half(headH) - Math.trunc(s * 0.3) + bob;
      const red: RGB = [255, 0, 0];
      const dot = Math.max(2, Math.trunc(s * 0.08));
      circle(ctx, red, cx, alertY, dot);
      const lineW = Math.max(2, Math.trunc(s * 0.06));
      const lineH = Math.trunc(s * 0.25);
      fillRect(ctx, red, cx - half(lineW), alertY - dot - 2 - lineH, lineW, lineH);
    }
  }

  private drawPlayer(offsetRow: number, offsetCol: number): void {
    const g = this.game;
    const ctx = this.ctx;
    const size = this.cellSize;

    // Parpadeo mientras es invulnerable
    if (g.invulnerable && Math.floor(ticks() / 100) % 2 === 0) return;

    if (g.playerFallingActive) {
      this.drawPlayerFalling(offsetRow, offsetCol);
      return;
    }
    if (g.playerFellIntoBarranco) return;

    let playerRow: number;
    let playerCol: number;
    if (g.playerAnimating) {
      const t = Math.min(1, (ticks() - g.playerAnimStartTime) / g.playerAnimDuration);
      const [fromRow, fromCol] = g.playerAnimFromPos;
      const [toRow, toCol] = g.playerAnimToPos;
      playerRow = fromRow + (toRow - fromRow) * t;
      playerCol = fromCol + (toCol - fromCol) * t;
      if (t >= 1) {
        g.playerAnimating = false;
        [playerRow, playerCol] = g.currentPosition;
      }
    } else {
      [playerRow, playerCol] = g.currentPosition;
    }

    const centerX = (playerCol - offsetCol) * size + Math.floor(size / 2);
    const centerY = (playerRow - offsetRow) * size + Math.floor(size / 2);
    const spriteSize = Math.trunc(size * 0.6);
    const inGameOverDelay = g.showingGameOver && ticks() - g.gameOverStartTime < 1000;

    if (g.showingGameOver && !g.audio.thoughtActive && !inGameOverDelay) {
      // Guerrero tendido sobre un charco de sangre que se expande
      if (g.gameOverThoughtFinishedTime > 0) {
        const [pr, pc] = g.currentPosition;
        this.drawBloodPool(centerX, centerY, g.gameOverThoughtFinishedTime, pr * 1000 + pc);
      }
      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(-Math.PI / 2);
      this.drawWarriorSprite(ctx, 0, 0, spriteSize);
      ctx.restore();
    } else {
      this.drawWarriorSprite(ctx, Math.trunc(centerX), Math.trunc(centerY), spriteSize);
    }
  }

  /** Caída por el barranco: se aleja, gira y se desvanece. */
  private drawPlayerFalling(offsetRow: number, offsetCol: number): void {
    const g = this.game;
    const ctx = this.ctx;
    const size = this.cellSize;
    const t = Math.min(1, (ticks() - g.playerFallingStartTime) / g.playerFallingDuration);
    if (t >= 1) {
      g.playerFallingActive = false;
      g.playerFellIntoBarranco = true;
      return;
    }

    const [dr, dc] = g.playerFallingDirection ? DELTA[g.playerFallingDirection] : [0, 0];
    const [fromRow, fromCol] = g.playerFallingFromPos;
    const row = fromRow + dr * 1.4 * t;
    const col = fromCol + dc * 1.4 * t;
    const centerX = (col - offsetCol) * size + Math.floor(size / 2);
    const centerY = (row - offsetRow) * size + Math.floor(size / 2);

    const scale = Math.max(0.05, 1 - t);
    const spriteSize = Math.max(2, Math.trunc(size * 0.6 * scale));

    ctx.save();
    ctx.globalAlpha = Math.max(0, Math.trunc(255 * (1 - t))) / 255;
    ctx.translate(centerX, centerY);
    ctx.rotate(-((t * 220) * Math.PI) / 180);
    this.drawWarriorSprite(ctx, 0, 0, spriteSize);
    ctx.restore();
  }

  /** Guerrero procedimental (vectorial) centrado en (cx, cy); escala con `size`. */
  private drawWarriorSprite(ctx: Ctx, cx: number, cy: number, size: number): void {
    const g = this.game;
    const s = Math.max(8, Math.trunc(size));
    const headR = Math.max(4, Math.floor(s / 6));
    const bodyH = Math.max(8, Math.floor(s / 2));
    const bodyW = Math.max(6, Math.floor(s / 3));
    const P = PLAYER_PALETTE;

    // Animación de introducción: caída desde arriba y miradas a los lados
    let introOffsetY = 0;
    let headTurn = 0;
    if (g.introAnimActive) {
      const elapsed = ticks() - g.introAnimStartTime;
      if (elapsed < 800) introOffsetY = Math.trunc(-this.cellSize * (1 - elapsed / 800));
      else if (elapsed < 2800) headTurn = Math.floor(-headR / 2);
      else if (elapsed < 4800) headTurn = Math.floor(headR / 2);
      else if (elapsed < 5300) g.introShowWeapons = true;
      else {
        g.introAnimActive = false;
        g.introShowWeapons = true;
      }
    }
    cy += introOffsetY;

    // Sombra
    const shadowW = Math.trunc(bodyW * 1.2);
    ellipse(ctx, [10, 10, 10], cx - Math.floor(shadowW / 2), cy + Math.floor(bodyH / 2), shadowW, Math.max(4, Math.floor(s / 6)));

    // Oscilación al caminar
    const t = ticks();
    const walking = t < g.playerWalkUntil;
    const phase = walking ? Math.sin(t * g.playerAnimSpeed * 2 * Math.PI) * g.playerAnimAmp : 0;

    // Piernas
    const legH = Math.max(6, Math.floor(s / 6));
    const leftLeg = Math.trunc(phase * legH * 0.5);
    const rightLeg = Math.trunc(-phase * legH * 0.5);
    const lx = cx - Math.floor(bodyW / 4);
    const rx = cx + Math.floor(bodyW / 4);
    const legY0 = cy + Math.floor(bodyH / 2);
    line(ctx, [60, 60, 60], lx, legY0, lx, legY0 + legH + leftLeg, 3);
    line(ctx, [60, 60, 60], rx, legY0, rx, legY0 + legH + rightLeg, 3);

    // Cuerpo (armadura)
    const bodyX = cx - Math.floor(bodyW / 2);
    const bodyTop = cy - Math.floor(bodyH / 4);
    fillRect(ctx, P.armor, bodyX, bodyTop, bodyW, bodyH);
    strokeRect(ctx, P.trim, bodyX, bodyTop, bodyW, bodyH, 2);

    // Brazos / guanteletes
    const armW = Math.max(4, Math.floor(s / 10));
    const armY = cy - Math.floor(bodyH / 8) + Math.trunc(-phase * Math.floor(bodyH / 8));
    const armH = Math.floor(bodyH / 3);
    const armLX = cx - Math.floor(bodyW / 2) - armW;
    const armRX = cx + Math.floor(bodyW / 2);
    fillRect(ctx, P.armor, armLX, armY, armW, armH);
    fillRect(ctx, P.armor, armRX, armY, armW, armH);
    strokeRect(ctx, P.trim, armLX, armY, armW, armH, 1);
    strokeRect(ctx, P.trim, armRX, armY, armW, armH, 1);

    // Escudo y espada, solo tras la introducción
    if (g.introShowWeapons) {
      const swordX = cx + Math.floor(bodyW / 2) + armW + 2 + Math.trunc(phase * 2);

      if (g.hasSwordPower) {
        const glowR = Math.max(15, Math.floor(s / 2));
        circle(ctx, [200, 240, 255], swordX, cy - Math.floor(bodyH / 2) + Math.trunc(-phase * 2), glowR, 0, 100 / 255);
      }

      const shieldR = Math.max(8, Math.floor(s / 6));
      const shieldX = cx - Math.floor(bodyW / 2) - armW - Math.floor(shieldR / 2) + Math.trunc(-phase * 3);
      const shieldY = cy + Math.trunc(phase * 2);
      circle(ctx, P.shield, shieldX, shieldY, shieldR);
      circle(ctx, P.shieldTrim, shieldX, shieldY, shieldR, 2);

      const swordH = Math.max(12, Math.floor(s / 3));
      const swordW = Math.max(3, Math.floor(s / 30));
      const y1 = cy - Math.floor(bodyH / 8) + Math.trunc(-phase * 2);
      const y2 = y1 - swordH + Math.trunc(phase * 4);
      const blade: RGB = g.hasSwordPower ? [220, 250, 255] : P.swordBlade;
      line(ctx, P.swordHandle, swordX, y1, swordX, y1 + 6, swordW + 2);
      line(ctx, blade, swordX, y1, swordX, y2, swordW);
    }

    // Cabeza y casco
    const headX = cx + headTurn;
    const headY = cy - Math.floor(bodyH / 2) + headR;
    circle(ctx, P.skin, headX, headY, headR);
    const helmetH = Math.max(6, headR + 2);
    fillRect(ctx, P.trim, headX - headR - 2, headY - helmetH, headR * 2 + 4, helmetH);
    strokeRect(ctx, [160, 160, 160], headX - headR - 2, headY - helmetH, headR * 2 + 4, helmetH, 1);
    line(ctx, [30, 30, 30], headX - headR, headY - 1, headX + headR, headY - 1, 2);
    const eyeR = Math.max(1, Math.floor(headR / 4));
    circle(ctx, [10, 10, 10], headX - Math.floor(headR / 2), headY - 1, eyeR);
    circle(ctx, [10, 10, 10], headX + Math.floor(headR / 2), headY - 1, eyeR);
  }

  private drawFlyingBat(offsetRow: number, offsetCol: number): void {
    const g = this.game;
    if (!g.batFlyingActive) return;
    const t = (ticks() - g.batFlyingStartTime) / g.batFlyingDuration;
    if (t >= 1) {
      g.batFlyingActive = false;
      return;
    }

    const [fromRow, fromCol] = g.batFromFrac;
    const [toRow, toCol] = g.batToFrac;
    const flutter = Math.sin(t * Math.PI * 6) * 0.06;
    const batRow = g.batFlyingRow + fromRow + (toRow - fromRow) * t;
    const batCol = g.batFlyingCol + fromCol + (toCol - fromCol) * t + flutter;
    const size = this.cellSize;
    const cx = Math.trunc((batCol - offsetCol) * size + Math.floor(size / 2));
    const cy = Math.trunc((batRow - offsetRow) * size + Math.floor(size / 2));
    this.drawBatSprite(cx, cy, Math.trunc(size * 0.35), t * Math.PI * 10);
  }

  /** Murciélago procedimental con alas aleteando. */
  private drawBatSprite(cx: number, cy: number, size: number, flapPhase: number): void {
    const ctx = this.ctx;
    const color: RGB = [15, 15, 20];
    const half = Math.max(2, Math.floor(size / 2));
    const wingTipY = Math.trunc(-half * 0.7 * Math.sin(flapPhase));

    polygon(ctx, color, [[cx, cy], [cx - half, cy + wingTipY], [cx - Math.trunc(half * 0.55), cy + Math.trunc(half * 0.35)]]);
    polygon(ctx, color, [[cx, cy], [cx + half, cy + wingTipY], [cx + Math.trunc(half * 0.55), cy + Math.trunc(half * 0.35)]]);

    const bodyW = Math.max(2, Math.trunc(half * 0.5));
    const bodyH = Math.max(2, Math.trunc(half * 0.35));
    ellipse(ctx, color, cx - Math.floor(bodyW / 2), cy - Math.floor(bodyH / 2), bodyW, bodyH);
  }
}
