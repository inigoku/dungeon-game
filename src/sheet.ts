/**
 * Hoja de personaje de la clase elegida, al estilo de las de los juegos de rol de mesa (D&D).
 * Por ahora es una ficha fija con unos pocos datos vivos (vida, poder del arma, exploración).
 */
import type { ClassInfo } from './classes';
import { drawPortraitImage } from './atlas';
import { context2d } from './gfx';
import { ticks } from './time';

/** Datos de la partida que la hoja muestra en vivo. */
export interface SheetData {
  hp: number;
  maxHp: number;
  swordPower: boolean;
  explored: number;
}

const PROFICIENCY = 2;

const modifier = (score: number): number => Math.floor((score - 10) / 2);
const signed = (n: number): string => (n >= 0 ? `+${n}` : `${n}`);

function html(info: ClassInfo): string {
  const d = info.sheet;
  const byKey = new Map(d.abilities.map(([key, , score]) => [key, score]));
  const abilities = d.abilities
    .map(
      ([, name, score]) => `
      <div class="sheet-ability" title="${name}">
        <div class="sheet-ability-name">${name}</div>
        <div class="sheet-ability-mod">${signed(modifier(score))}</div>
        <div class="sheet-ability-score">${score}</div>
      </div>`,
    )
    .join('');
  const saves = d.abilities
    .map(([, name, score, proficient]) => {
      const value = modifier(score) + (proficient ? PROFICIENCY : 0);
      return `<li><span class="sheet-dot${proficient ? ' on' : ''}"></span><b>${signed(value)}</b> ${name}</li>`;
    })
    .join('');
  const skills = d.skills
    .map(([name, key, proficient]) => {
      const value = modifier(byKey.get(key) ?? 10) + (proficient ? PROFICIENCY : 0);
      return `<li><span class="sheet-dot${proficient ? ' on' : ''}"></span><b>${signed(value)}</b> ${name} <small>(${key})</small></li>`;
    })
    .join('');
  const initiative = modifier(byKey.get('DES') ?? 10);
  const attacks = d.attacks.map(([name, hit, dmg]) => `<tr><td>${name}</td><td>${hit}</td><td>${dmg}</td></tr>`).join('');
  const equipment = d.equipment.map((e) => `<li>${e}</li>`).join('');
  const personality = d.personality.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
  const features = d.features.map((f) => `<li>${f}</li>`).join('');

  return `
  <div class="sheet-paper" role="document">
    <button class="sheet-close" type="button" aria-label="Cerrar la hoja de personaje">✕</button>

    <header class="sheet-head">
      <canvas class="sheet-portrait" width="170" height="210" aria-label="Retrato de ${info.label}"></canvas>
      <div class="sheet-title">
        <div class="sheet-class">${info.label}</div>
        <div class="sheet-name">${d.name}</div>
        <dl class="sheet-fields">
          <div><dt>Clase y nivel</dt><dd>${d.classLevel}</dd></div>
          <div><dt>Trasfondo</dt><dd>${d.background}</dd></div>
          <div><dt>Raza</dt><dd>${d.race}</dd></div>
          <div><dt>Alineamiento</dt><dd>${d.alignment}</dd></div>
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
          <div class="sheet-shield"><span class="sheet-box-value">${d.armorClass}</span><span class="sheet-box-label">Clase de armadura</span></div>
          <div class="sheet-box"><span class="sheet-box-value">${signed(initiative)}</span><span class="sheet-box-label">Iniciativa</span></div>
          <div class="sheet-box"><span class="sheet-box-value">${d.speed}</span><span class="sheet-box-label">Velocidad</span></div>
        </div>
        <div class="sheet-hp">
          <div class="sheet-hp-label">Puntos de golpe</div>
          <div class="sheet-hp-value"><span data-bind="hp">2</span> / <span data-bind="maxHp">2</span></div>
          <div class="sheet-hearts" data-bind="hearts" aria-hidden="true"></div>
        </div>
        <div class="sheet-row">
          <div class="sheet-box"><span class="sheet-box-value">${d.hitDie}</span><span class="sheet-box-label">Dados de golpe</span></div>
          <div class="sheet-box"><span class="sheet-box-value">○ ○ ○</span><span class="sheet-box-label">Salvaciones contra muerte</span></div>
        </div>
        <h3>Ataques</h3>
        <table class="sheet-attacks">
          <thead><tr><th>Nombre</th><th>Ataque</th><th>Daño</th></tr></thead>
          <tbody>${attacks}</tbody>
        </table>
        <div class="sheet-power" data-bind="power"></div>
        <h3>Equipo</h3>
        <ul class="sheet-plain">${equipment}</ul>
      </section>

      <section class="sheet-col sheet-wide">
        <h3>Personalidad</h3>
        <dl class="sheet-notes">${personality}</dl>
        <h3>Rasgos y atributos</h3>
        <ul class="sheet-plain">${features}</ul>
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
    private readonly info: ClassInfo,
    private readonly onClose: () => void,
    private readonly read: () => SheetData,
  ) {
    this.root = document.createElement('div');
    this.root.id = 'sheet';
    this.root.hidden = true;
    this.root.setAttribute('role', 'dialog');
    this.root.setAttribute('aria-label', 'Hoja de personaje');
    this.root.innerHTML = html(info);
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
    this.set('power', data.swordPower ? this.info.sheet.powerOn : this.info.sheet.powerOff);
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
    if (this.info.portrait && drawPortraitImage(ctx, this.info.portrait, width, height)) return;
    this.info.draw(ctx, width / 2, height / 2 + 6, 196, {
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
