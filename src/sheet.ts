/**
 * Hoja de personaje del Guerrero, al estilo de las de los juegos de rol de mesa (D&D).
 * Por ahora es una ficha fija con unos pocos datos vivos (vida, poder de la espada, exploración).
 */
import { context2d } from './gfx';
import { ticks } from './time';
import { drawWarrior } from './warrior';

/** Datos de la partida que la hoja muestra en vivo. */
export interface SheetData {
  hp: number;
  maxHp: number;
  swordPower: boolean;
  explored: number;
}

interface Ability {
  key: string;
  name: string;
  score: number;
  save: boolean;
}

const ABILITIES: readonly Ability[] = [
  { key: 'FUE', name: 'Fuerza', score: 16, save: true },
  { key: 'DES', name: 'Destreza', score: 12, save: false },
  { key: 'CON', name: 'Constitución', score: 14, save: true },
  { key: 'INT', name: 'Inteligencia', score: 10, save: false },
  { key: 'SAB', name: 'Sabiduría', score: 11, save: false },
  { key: 'CAR', name: 'Carisma', score: 9, save: false },
];

const PROFICIENCY = 2;

/** Habilidades: [nombre, atributo, competente]. */
const SKILLS: ReadonlyArray<readonly [string, string, boolean]> = [
  ['Atletismo', 'FUE', true],
  ['Intimidación', 'CAR', true],
  ['Percepción', 'SAB', false],
  ['Supervivencia', 'SAB', false],
  ['Sigilo', 'DES', false],
  ['Historia', 'INT', false],
  ['Investigación', 'INT', false],
  ['Trato con animales', 'SAB', false],
];

const modifier = (score: number): number => Math.floor((score - 10) / 2);
const signed = (n: number): string => (n >= 0 ? `+${n}` : `${n}`);

function html(): string {
  const byKey = new Map(ABILITIES.map((a) => [a.key, a]));
  const abilities = ABILITIES.map(
    (a) => `
      <div class="sheet-ability" title="${a.name}">
        <div class="sheet-ability-name">${a.name}</div>
        <div class="sheet-ability-mod">${signed(modifier(a.score))}</div>
        <div class="sheet-ability-score">${a.score}</div>
      </div>`,
  ).join('');
  const saves = ABILITIES.map((a) => {
    const value = modifier(a.score) + (a.save ? PROFICIENCY : 0);
    return `<li><span class="sheet-dot${a.save ? ' on' : ''}"></span><b>${signed(value)}</b> ${a.name}</li>`;
  }).join('');
  const skills = SKILLS.map(([name, key, proficient]) => {
    const value = modifier(byKey.get(key)?.score ?? 10) + (proficient ? PROFICIENCY : 0);
    return `<li><span class="sheet-dot${proficient ? ' on' : ''}"></span><b>${signed(value)}</b> ${name} <small>(${key})</small></li>`;
  }).join('');

  return `
  <div class="sheet-paper" role="document">
    <button class="sheet-close" type="button" aria-label="Cerrar la hoja de personaje">✕</button>

    <header class="sheet-head">
      <canvas class="sheet-portrait" width="170" height="210" aria-label="Retrato del Guerrero"></canvas>
      <div class="sheet-title">
        <div class="sheet-class">Guerrero</div>
        <div class="sheet-name">Ser Aldo, el Valiente</div>
        <dl class="sheet-fields">
          <div><dt>Clase y nivel</dt><dd>Guerrero 1</dd></div>
          <div><dt>Trasfondo</dt><dd>Soldado</dd></div>
          <div><dt>Raza</dt><dd>Humano</dd></div>
          <div><dt>Alineamiento</dt><dd>Legal bueno</dd></div>
          <div><dt>Experiencia</dt><dd>0 PX</dd></div>
          <div><dt>Celdas exploradas</dt><dd data-bind="explored">1</dd></div>
        </dl>
      </div>
    </header>

    <div class="sheet-grid">
      <section class="sheet-col">
        <div class="sheet-abilities">${abilities}</div>
        <div class="sheet-box"><span class="sheet-box-value">${signed(PROFICIENCY)}</span><span class="sheet-box-label">Bonificador de competencia</span></div>
        <h3>Tiradas de salvación</h3>
        <ul class="sheet-list">${saves}</ul>
        <h3>Habilidades</h3>
        <ul class="sheet-list">${skills}</ul>
      </section>

      <section class="sheet-col">
        <div class="sheet-vitals">
          <div class="sheet-shield"><span class="sheet-box-value">18</span><span class="sheet-box-label">Clase de armadura</span></div>
          <div class="sheet-box"><span class="sheet-box-value">${signed(modifier(12))}</span><span class="sheet-box-label">Iniciativa</span></div>
          <div class="sheet-box"><span class="sheet-box-value">9 m</span><span class="sheet-box-label">Velocidad</span></div>
        </div>
        <div class="sheet-hp">
          <div class="sheet-hp-label">Puntos de golpe</div>
          <div class="sheet-hp-value"><span data-bind="hp">2</span> / <span data-bind="maxHp">2</span></div>
          <div class="sheet-hearts" data-bind="hearts" aria-hidden="true"></div>
        </div>
        <div class="sheet-row">
          <div class="sheet-box"><span class="sheet-box-value">1d10</span><span class="sheet-box-label">Dados de golpe</span></div>
          <div class="sheet-box"><span class="sheet-box-value">○ ○ ○</span><span class="sheet-box-label">Salvaciones contra muerte</span></div>
        </div>
        <h3>Ataques</h3>
        <table class="sheet-attacks">
          <thead><tr><th>Nombre</th><th>Ataque</th><th>Daño</th></tr></thead>
          <tbody>
            <tr><td>Espada larga</td><td>+5</td><td>1d8+3 cortante</td></tr>
            <tr><td>Embestida de escudo</td><td>+5</td><td>1d4+3 contundente</td></tr>
          </tbody>
        </table>
        <div class="sheet-power" data-bind="power"></div>
        <h3>Equipo</h3>
        <ul class="sheet-plain">
          <li>Cota de mallas y coraza</li>
          <li>Escudo de cometa</li>
          <li>Espada larga</li>
          <li>Yelmo de ranuras con penacho rojo</li>
          <li>Bufanda roja</li>
          <li>Mochila, cuerda y yesca</li>
        </ul>
      </section>

      <section class="sheet-col sheet-wide">
        <h3>Personalidad</h3>
        <dl class="sheet-notes">
          <div><dt>Rasgo</dt><dd>Valiente aunque no lo parezca; habla solo cuando está nervioso.</dd></div>
          <div><dt>Ideal</dt><dd>Salir de la mazmorra con vida y con la espada en la mano.</dd></div>
          <div><dt>Vínculo</dt><dd>Debe volver al inicio para reclamar lo que le espera allí.</dd></div>
          <div><dt>Defecto</dt><dd>Las abominaciones le dejan sin palabras.</dd></div>
        </dl>
        <h3>Rasgos y atributos</h3>
        <ul class="sheet-plain">
          <li><b>Estilo de combate: Defensa.</b> +1 a la CA mientras lleva armadura.</li>
          <li><b>Tomar aliento.</b> Una vez por descanso recupera 1d10+1 puntos de golpe.</li>
          <li><b>Rango militar.</b> Los soldados de bajo rango le obedecen.</li>
        </ul>
      </section>
    </div>
  </div>`;
}

export class CharacterSheet {
  private readonly root: HTMLElement;
  private readonly portrait: HTMLCanvasElement;
  private readonly bind = new Map<string, HTMLElement>();
  private raf = 0;
  private open_ = false;
  private lastHearts = '';

  constructor(
    parent: HTMLElement,
    private readonly onClose: () => void,
    private readonly read: () => SheetData,
  ) {
    this.root = document.createElement('div');
    this.root.id = 'sheet';
    this.root.hidden = true;
    this.root.setAttribute('role', 'dialog');
    this.root.setAttribute('aria-label', 'Hoja de personaje');
    this.root.innerHTML = html();
    parent.append(this.root);

    this.portrait = this.root.querySelector<HTMLCanvasElement>('.sheet-portrait') as HTMLCanvasElement;
    this.root.querySelectorAll<HTMLElement>('[data-bind]').forEach((el) => this.bind.set(el.dataset.bind ?? '', el));
    this.root.querySelector('.sheet-close')?.addEventListener('click', () => this.onClose());
    // Tocar fuera de la hoja también la cierra
    this.root.addEventListener('click', (e) => {
      if (e.target === this.root) this.onClose();
    });
  }

  get isOpen(): boolean {
    return this.open_;
  }

  show(): void {
    this.open_ = true;
    this.root.hidden = false;
    this.root.scrollTop = 0;
    const loop = () => {
      if (!this.open_) return;
      this.refresh();
      this.raf = requestAnimationFrame(loop);
    };
    loop();
  }

  hide(): void {
    this.open_ = false;
    this.root.hidden = true;
    cancelAnimationFrame(this.raf);
  }

  dispose(): void {
    this.hide();
    this.root.remove();
  }

  private set(key: string, value: string): void {
    const el = this.bind.get(key);
    if (el && el.textContent !== value) el.textContent = value;
  }

  /** Actualiza los datos vivos y redibuja el retrato (respira, ondea el penacho...). */
  private refresh(): void {
    const data = this.read();
    this.set('hp', String(data.hp));
    this.set('maxHp', String(data.maxHp));
    this.set('explored', String(data.explored));
    this.set('power', data.swordPower ? '⚔ Poder de la espada: ¡activo! Los monstruos huyen y caen a su paso.' : '⚔ Poder de la espada: dormida. Vuelve al inicio tras ver la salida para despertarla.');
    const hearts = '♥'.repeat(Math.max(0, data.hp)) + '♡'.repeat(Math.max(0, data.maxHp - data.hp));
    if (hearts !== this.lastHearts) {
      this.lastHearts = hearts;
      this.set('hearts', hearts);
    }

    const ctx = context2d(this.portrait);
    const { width, height } = this.portrait;
    ctx.clearRect(0, 0, width, height);
    const grad = ctx.createRadialGradient(width / 2, height / 2, 10, width / 2, height / 2, width * 0.75);
    grad.addColorStop(0, 'rgba(255,240,205,0.9)');
    grad.addColorStop(1, 'rgba(184,140,84,0.55)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, width, height);
    drawWarrior(ctx, width / 2, height / 2 + 6, 196, {
      walkAngle: 0,
      moving: false,
      facing: 'S',
      headTurn: 0,
      showWeapons: true,
      swordPower: data.swordPower,
      now: ticks(),
    });
  }
}
