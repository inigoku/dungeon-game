/** Clases jugables: aspecto del personaje y datos de su hoja de personaje. */
import type { Ctx } from './gfx';
import { drawAtlasFrame, hasAtlas, pickFrame } from './atlas';
import { drawBarbarian } from './barbarian';
import { drawWarrior, type WarriorLook } from './warrior';

export type PlayerClass = 'guerrero' | 'barbaro';

export interface ClassSheetData {
  /** Nombre del personaje. */
  name: string;
  classLevel: string;
  background: string;
  race: string;
  alignment: string;
  /** [clave, nombre, puntuación, competente en la salvación]. */
  abilities: ReadonlyArray<readonly [string, string, number, boolean]>;
  /** [nombre, atributo, competente]. */
  skills: ReadonlyArray<readonly [string, string, boolean]>;
  armorClass: number;
  speed: string;
  hitDie: string;
  /** [nombre, ataque, daño]. */
  attacks: ReadonlyArray<readonly [string, string, string]>;
  equipment: readonly string[];
  personality: ReadonlyArray<readonly [string, string]>;
  /** Rasgos de la clase (admiten <b>negrita</b>). */
  features: readonly string[];
  /** Texto del estado del poder, cuando está dormido y cuando está activo. */
  powerOff: string;
  powerOn: string;
}

export interface ClassInfo {
  id: PlayerClass;
  label: string;
  draw: (ctx: Ctx, cx: number, cy: number, size: number, look: WarriorLook) => void;
  /** Imagen de busto para la hoja de personaje (si no hay, se dibuja el sprite). */
  portrait?: string;
  sheet: ClassSheetData;
}

/** El bárbaro usa su atlas de bitmaps si está cargado; si no, el dibujo vectorial. */
function drawBarbarianBitmapOrVector(ctx: Ctx, cx: number, cy: number, size: number, look: WarriorLook): void {
  if (!hasAtlas('barbaro') || !drawAtlasFrame(ctx, 'barbaro', pickFrame(look), cx, cy, size, look.swordPower)) drawBarbarian(ctx, cx, cy, size, look);
}

/** ¿Esta clase tiene fotogramas para morir, caer, etc.? (si no, se gira y se encoge el dibujo) */
export function hasPoses(cls: PlayerClass): boolean {
  return cls === 'barbaro' && hasAtlas('barbaro');
}

export const CLASSES: Record<PlayerClass, ClassInfo> = {
  guerrero: {
    id: 'guerrero',
    label: 'Guerrero',
    draw: drawWarrior,
    sheet: {
      name: 'Ser Aldo, el Valiente',
      classLevel: 'Guerrero 1',
      background: 'Soldado',
      race: 'Humano',
      alignment: 'Legal bueno',
      abilities: [
        ['FUE', 'Fuerza', 16, true],
        ['DES', 'Destreza', 12, false],
        ['CON', 'Constitución', 14, true],
        ['INT', 'Inteligencia', 10, false],
        ['SAB', 'Sabiduría', 11, false],
        ['CAR', 'Carisma', 9, false],
      ],
      skills: [
        ['Atletismo', 'FUE', true],
        ['Intimidación', 'CAR', true],
        ['Percepción', 'SAB', false],
        ['Supervivencia', 'SAB', false],
        ['Sigilo', 'DES', false],
        ['Historia', 'INT', false],
        ['Investigación', 'INT', false],
        ['Trato con animales', 'SAB', false],
      ],
      armorClass: 18,
      speed: '9 m',
      hitDie: '1d10',
      attacks: [
        ['Espada larga', '+5', '1d8+3 cortante'],
        ['Embestida de escudo', '+5', '1d4+3 contundente'],
      ],
      equipment: ['Cota de mallas y coraza', 'Escudo de cometa', 'Espada larga', 'Yelmo de ranuras con penacho rojo', 'Bufanda roja', 'Mochila, cuerda y yesca'],
      personality: [
        ['Rasgo', 'Valiente aunque no lo parezca; habla solo cuando está nervioso.'],
        ['Ideal', 'Salir de la mazmorra con vida y con la espada en la mano.'],
        ['Vínculo', 'Debe volver al inicio para reclamar lo que le espera allí.'],
        ['Defecto', 'Las abominaciones le dejan sin palabras.'],
      ],
      features: [
        '<b>Estilo de combate: Defensa.</b> +1 a la CA mientras lleva armadura.',
        '<b>Tomar aliento.</b> Una vez por descanso recupera 1d10+1 puntos de golpe.',
        '<b>Rango militar.</b> Los soldados de bajo rango le obedecen.',
      ],
      powerOff: '⚔ Poder de la espada: dormida. Vuelve al inicio tras ver la salida para despertarla.',
      powerOn: '⚔ Poder de la espada: ¡activo! Los monstruos huyen y caen a su paso.',
    },
  },
  barbaro: {
    id: 'barbaro',
    label: 'Bárbaro',
    draw: drawBarbarianBitmapOrVector,
    portrait: 'retrato_barbaro',
    sheet: {
      name: 'Brak, el Furioso',
      classLevel: 'Bárbaro 1',
      background: 'Forastero',
      race: 'Semiorco',
      alignment: 'Caótico neutral',
      abilities: [
        ['FUE', 'Fuerza', 17, true],
        ['DES', 'Destreza', 14, false],
        ['CON', 'Constitución', 16, true],
        ['INT', 'Inteligencia', 8, false],
        ['SAB', 'Sabiduría', 12, false],
        ['CAR', 'Carisma', 9, false],
      ],
      skills: [
        ['Atletismo', 'FUE', true],
        ['Supervivencia', 'SAB', true],
        ['Intimidación', 'CAR', false],
        ['Percepción', 'SAB', false],
        ['Sigilo', 'DES', false],
        ['Historia', 'INT', false],
        ['Investigación', 'INT', false],
        ['Trato con animales', 'SAB', false],
      ],
      armorClass: 15,
      speed: '9 m',
      hitDie: '1d12',
      attacks: [
        ['Daga curva (derecha)', '+5', '1d4+3 cortante'],
        ['Daga curva (izquierda)', '+5', '1d4+3 cortante'],
      ],
      equipment: ['Dos dagas curvas de filo dentado', 'Taparrabos de cuero', 'Cinturones y correas de cuero, con hebilla en X', 'Bolsas del cinturón', 'Descalzo: no necesita más'],
      personality: [
        ['Rasgo', 'Gruñe más que habla, y casi siempre tiene razón.'],
        ['Ideal', 'Libertad: ninguna mazmorra lo retiene.'],
        ['Vínculo', 'Su melena negra es su orgullo: nadie se la toca.'],
        ['Defecto', 'Pierde la calma con facilidad.'],
      ],
      features: [
        '<b>Furia.</b> Dos veces por descanso: +2 al daño y resistencia a daño físico durante un minuto.',
        '<b>Defensa sin armadura.</b> CA = 10 + DES + CON mientras no lleva armadura.',
        '<b>Sentido del peligro.</b> Ventaja en las salvaciones de DES contra lo que pueda ver venir.',
      ],
      powerOff: '⚔ Furia de las dagas: dormida. Vuelve al inicio tras ver la salida para despertarla.',
      powerOn: '⚔ Furia de las dagas: ¡activa! Los monstruos huyen y caen a su paso.',
    },
  },
};

export const CLASS_IDS = Object.keys(CLASSES) as PlayerClass[];

const STORAGE_KEY = 'dungeon-clase';

function isClass(value: unknown): value is PlayerClass {
  return typeof value === 'string' && value in CLASSES;
}

/** Clase elegida: `?clase=barbaro` en la dirección, o la última que se usó. */
export function initialClass(): PlayerClass {
  try {
    const fromUrl = new URLSearchParams(location.search).get('clase');
    if (isClass(fromUrl)) return fromUrl;
    const stored = localStorage.getItem(STORAGE_KEY);
    if (isClass(stored)) return stored;
  } catch {
    /* sin acceso al almacenamiento */
  }
  return 'guerrero';
}

export function rememberClass(cls: PlayerClass): void {
  try {
    localStorage.setItem(STORAGE_KEY, cls);
  } catch {
    /* sin acceso al almacenamiento */
  }
}
