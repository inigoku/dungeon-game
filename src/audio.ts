/**
 * Audio del juego sobre Web Audio: mezclador (sonidos y canales con volumen,
 * bucles y fundidos) y AudioManager (música, subtítulos y "pensamientos").
 */
import type { Canvas } from './gfx';
import { ticks } from './time';

// ---------------------------------------------------------------------------
// Mezclador
// ---------------------------------------------------------------------------

export class Mixer {
  readonly ctx: AudioContext;

  constructor() {
    const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    this.ctx = new Ctor();
  }

  /** Los navegadores solo permiten sonar tras un gesto del usuario. */
  async resume(): Promise<void> {
    if (this.ctx.state !== 'running') await this.ctx.resume();
  }

  async decode(data: ArrayBuffer): Promise<AudioBuffer> {
    return await this.ctx.decodeAudioData(data);
  }
}

/** Equivalente a pygame.mixer.Sound: un buffer con volumen propio. */
export class Sound {
  volume: number;

  constructor(
    private readonly mixer: Mixer,
    readonly buffer: AudioBuffer,
    volume = 1,
  ) {
    this.volume = volume;
  }

  setVolume(volume: number): void {
    this.volume = volume;
  }

  /** Duración en segundos. */
  getLength(): number {
    return this.buffer.duration;
  }

  /** Reproduce en un canal nuevo (loops = -1 → infinito). */
  play(loops = 0): Channel {
    const channel = new Channel(this.mixer);
    channel.play(this, loops);
    return channel;
  }
}

/** Equivalente a pygame.mixer.Channel: reproduce un sonido cada vez, con su volumen. */
export class Channel {
  private source: AudioBufferSourceNode | null = null;
  private soundGain: GainNode | null = null;
  private readonly channelGain: GainNode;
  private busy = false;
  private volume = 1;

  constructor(private readonly mixer: Mixer) {
    this.channelGain = mixer.ctx.createGain();
    this.channelGain.connect(mixer.ctx.destination);
  }

  /** Empieza a sonar; como en pygame, el volumen del canal vuelve al máximo. */
  play(sound: Sound, loops = 0): void {
    this.stop();
    const { ctx } = this.mixer;
    const source = ctx.createBufferSource();
    source.buffer = sound.buffer;
    source.loop = loops < 0;
    const soundGain = ctx.createGain();
    soundGain.gain.value = sound.volume;
    source.connect(soundGain).connect(this.channelGain);
    this.volume = 1;
    this.channelGain.gain.cancelScheduledValues(0);
    this.channelGain.gain.value = 1;
    source.onended = () => {
      if (this.source !== source) return;
      this.busy = false;
      source.disconnect();
      soundGain.disconnect();
    };
    this.source = source;
    this.soundGain = soundGain;
    this.busy = true;
    source.start();
  }

  setVolume(volume: number): void {
    this.volume = volume;
    this.channelGain.gain.cancelScheduledValues(0);
    this.channelGain.gain.value = volume;
  }

  getVolume(): number {
    return this.volume;
  }

  stop(): void {
    if (this.source) {
      this.source.onended = null;
      try {
        this.source.stop();
      } catch {
        /* ya detenido */
      }
      this.source.disconnect();
      this.soundGain?.disconnect();
    }
    this.source = null;
    this.soundGain = null;
    this.busy = false;
  }

  /** Baja el volumen a cero en `ms` milisegundos y detiene el sonido. */
  fadeout(ms: number): void {
    const { ctx } = this.mixer;
    const gain = this.channelGain.gain;
    gain.cancelScheduledValues(ctx.currentTime);
    gain.setValueAtTime(this.volume, ctx.currentTime);
    gain.linearRampToValueAtTime(0, ctx.currentTime + ms / 1000);
    const source = this.source;
    setTimeout(() => {
      if (this.source === source) this.stop();
    }, ms);
  }

  getBusy(): boolean {
    return this.busy;
  }
}

// ---------------------------------------------------------------------------
// AudioManager
// ---------------------------------------------------------------------------

export type SoundEntry = readonly [Sound | null, number];
export type ImageEntry = readonly [Canvas | null, number];
export type SubtitleEntry = readonly [string, number];

interface Thought {
  startTicks: number;
  maxDuration: number;
  sounds: Array<{ start: number; sound: Sound }>;
  images: Array<{ start: number; image: Canvas; duration: number }>;
  subtitles: Array<{ start: number; text: string; duration: number }>;
  soundIndex: number;
  imageIndex: number;
  subtitleIndex: number;
  channels: Channel[];
}

export class AudioManager {
  readonly musicChannel: Channel;
  readonly musicSounds: Record<string, Sound> = {};
  currentMusic: string | null = null;
  introSound: Sound | null = null;
  cthulhuPlayed = false;
  musicVolume = 0.5;

  // Fundidos
  fadingOut = false;
  fadingIn = false;
  private fadeStartTime = 0;
  private fadeDuration = 1000;
  private fadeFromVolume = 0.5;
  private fadeToVolume = 0;
  private pendingMusicLoad: string | null = null;

  // Subtítulos
  showingSubtitles = false;
  subtitleText = '';
  private subtitleStartTime = 0;
  private subtitleDuration = 0;

  // Pensamientos
  thoughtActive = false;
  thoughtBlocksMovement = false;
  private thought: Thought | null = null;

  // Imagen del pensamiento
  showingImage = false;
  imageSurface: Canvas | null = null;
  imageStartTime = 0;
  imageDuration = 0;

  private swordHumSound: Sound | null;
  private swordHumChannel: Channel | null = null;
  private barrancoWindChannel: Channel | null = null;

  constructor(
    mixer: Mixer,
    buffers: Record<string, AudioBuffer | null>,
  ) {
    this.musicChannel = new Channel(mixer);
    this.musicChannel.setVolume(0.5);

    for (const key of ['intro', 'adagio', 'cthulhu', 'viento', 'alataque']) {
      const buffer = buffers[key];
      if (buffer) this.musicSounds[key] = new Sound(mixer, buffer);
    }
    const hum = buffers['zumbido_espada'];
    this.swordHumSound = hum ? new Sound(mixer, hum, 0.3) : null;

    this.introSound = this.musicSounds['intro'] ?? null;

    // Reproducir adagio desde el principio en bucle
    if (this.musicSounds['adagio']) {
      this.currentMusic = 'adagio';
      this.musicChannel.play(this.musicSounds['adagio'], -1);
      this.musicChannel.setVolume(this.musicVolume);
    }
  }

  /** Detiene todo el audio (al reiniciar la partida). */
  dispose(): void {
    this.cancelThought();
    this.stopMusic();
    this.barrancoWindChannel?.stop();
    this.barrancoWindChannel = null;
  }

  playMusic(key: string, loops = -1): void {
    const sound = this.musicSounds[key];
    if (!sound) return;
    this.currentMusic = key;
    this.musicChannel.play(sound, loops);
    this.musicChannel.setVolume(this.musicVolume);
  }

  stopMusic(): void {
    this.musicChannel.stop();
    this.currentMusic = null;
    this.stopSwordHum();
  }

  startFadeOut(duration = 1000, nextMusic: string | null = null): void {
    this.fadingOut = true;
    this.fadingIn = false;
    this.fadeStartTime = ticks();
    this.fadeDuration = duration;
    this.fadeFromVolume = this.musicVolume;
    this.fadeToVolume = 0;
    this.pendingMusicLoad = nextMusic;
  }

  startFadeIn(duration = 1000, targetVolume = 0.5): void {
    this.fadingIn = true;
    this.fadingOut = false;
    this.fadeStartTime = ticks();
    this.fadeDuration = duration;
    this.fadeFromVolume = 0;
    this.fadeToVolume = targetVolume;
    this.musicVolume = 0;
    this.musicChannel.setVolume(0);
  }

  updateFades(): void {
    const elapsed = ticks() - this.fadeStartTime;
    if (this.fadingOut) {
      if (elapsed >= this.fadeDuration) {
        this.fadingOut = false;
        this.musicVolume = this.fadeToVolume;
        this.musicChannel.setVolume(this.musicVolume);
        this.musicChannel.stop();
        if (this.pendingMusicLoad) {
          this.playMusic(this.pendingMusicLoad);
          this.pendingMusicLoad = null;
          this.startFadeIn(this.fadeDuration, 0.5);
        }
      } else {
        this.musicVolume = this.fadeFromVolume + (this.fadeToVolume - this.fadeFromVolume) * (elapsed / this.fadeDuration);
        this.musicChannel.setVolume(this.musicVolume);
      }
    } else if (this.fadingIn) {
      if (elapsed >= this.fadeDuration) {
        this.fadingIn = false;
        this.musicVolume = this.fadeToVolume;
        this.musicChannel.setVolume(this.musicVolume);
      } else {
        this.musicVolume = this.fadeFromVolume + (this.fadeToVolume - this.fadeFromVolume) * (elapsed / this.fadeDuration);
        this.musicChannel.setVolume(this.musicVolume);
      }
    }
  }

  showSubtitle(text: string, duration: number): void {
    this.showingSubtitles = true;
    this.subtitleText = text;
    this.subtitleStartTime = ticks();
    this.subtitleDuration = duration;
  }

  /** Caduca los subtítulos sueltos (los de un pensamiento los gestiona el pensamiento). */
  updateSubtitles(): void {
    if (this.thoughtActive) return;
    if (this.showingSubtitles && ticks() - this.subtitleStartTime >= this.subtitleDuration) {
      this.showingSubtitles = false;
      this.subtitleText = '';
    }
  }

  /**
   * Lanza un "pensamiento": sonidos, imágenes y subtítulos sincronizados.
   * Duración 0 en sonidos = duración del audio; en imágenes = duración del sonido.
   * Un pensamiento nuevo interrumpe al anterior.
   */
  triggerThought(opts: {
    sounds?: SoundEntry[];
    images?: ImageEntry[] | null;
    subtitles?: SubtitleEntry[] | null;
    blocksMovement?: boolean;
  }): void {
    const { sounds = [], images = null, subtitles = null, blocksMovement = false } = opts;

    if (images) {
      for (const [, duration] of images) {
        if (duration < 0 || (duration === 0 && sounds.length === 0)) {
          console.error('Duración de imagen inválida');
          return;
        }
      }
    }
    if (subtitles?.some(([, duration]) => duration <= 0)) {
      console.error('Los subtítulos requieren duración > 0');
      return;
    }

    if (this.thoughtActive) this.cancelThought();

    // Línea de tiempo de sonidos (secuenciales)
    const soundTimeline: Thought['sounds'] = [];
    let cursor = 0;
    for (const [sound, durationMs] of sounds) {
      if (!sound) continue;
      const actual = durationMs === 0 ? Math.trunc(sound.getLength() * 1000) : durationMs;
      soundTimeline.push({ start: cursor, sound });
      cursor += actual;
    }
    const soundTotal = cursor;
    let maxDuration = soundTotal;

    const imageTimeline: Thought['images'] = [];
    cursor = 0;
    for (const [image, durationMs] of images ?? []) {
      if (!image) continue;
      const actual = durationMs === 0 ? soundTotal : durationMs;
      if (actual <= 0) continue;
      imageTimeline.push({ start: cursor, image, duration: actual });
      cursor += actual;
    }
    maxDuration = Math.max(maxDuration, cursor);

    const subtitleTimeline: Thought['subtitles'] = [];
    cursor = 0;
    for (const [text, durationMs] of subtitles ?? []) {
      if (!text) continue;
      subtitleTimeline.push({ start: cursor, text, duration: durationMs });
      cursor += durationMs;
    }
    maxDuration = Math.max(maxDuration, cursor);

    const thought: Thought = {
      startTicks: ticks(),
      maxDuration,
      sounds: soundTimeline,
      images: imageTimeline,
      subtitles: subtitleTimeline,
      soundIndex: 0,
      imageIndex: 0,
      subtitleIndex: 0,
      channels: [],
    };
    this.thought = thought;
    this.thoughtActive = true;
    this.thoughtBlocksMovement = blocksMovement;

    // El primer instante se procesa ya (suena el audio y aparece el primer subtítulo)
    this.stepThought();
  }

  cancelThought(): void {
    const thought = this.thought;
    if (!this.thoughtActive || !thought) return;
    for (const channel of thought.channels) channel.stop();
    this.finishThought();
  }

  private finishThought(): void {
    this.showingSubtitles = false;
    this.subtitleText = '';
    this.showingImage = false;
    this.imageSurface = null;
    this.thoughtActive = false;
    this.thoughtBlocksMovement = false;
    this.thought = null;
  }

  /** Avanza el pensamiento activo según el tiempo transcurrido. */
  updateThoughts(): void {
    if (this.thoughtActive) this.stepThought();
  }

  private stepThought(): void {
    const t = this.thought;
    if (!t) return;
    const elapsed = ticks() - t.startTicks;

    // Sonidos: se lanza cada uno al llegar su momento
    while (t.soundIndex < t.sounds.length && elapsed >= t.sounds[t.soundIndex].start) {
      t.channels.push(t.sounds[t.soundIndex].sound.play());
      t.soundIndex++;
    }

    // Subtítulos
    if (t.subtitleIndex < t.subtitles.length) {
      const next = t.subtitles[t.subtitleIndex];
      if (elapsed >= next.start) {
        this.showingSubtitles = true;
        this.subtitleText = next.text;
        this.subtitleDuration = next.duration;
        this.subtitleStartTime = ticks();
        t.subtitleIndex++;
      } else if (t.subtitleIndex > 0) {
        const prev = t.subtitles[t.subtitleIndex - 1];
        if (elapsed >= prev.start + prev.duration) {
          this.showingSubtitles = false;
          this.subtitleText = '';
        }
      }
    }

    // Imágenes
    if (t.imageIndex < t.images.length) {
      const next = t.images[t.imageIndex];
      if (elapsed >= next.start) {
        this.showingImage = true;
        this.imageSurface = next.image;
        this.imageDuration = next.duration;
        this.imageStartTime = ticks();
        t.imageIndex++;
      } else if (t.imageIndex > 0) {
        const prev = t.images[t.imageIndex - 1];
        if (elapsed >= prev.start + prev.duration) {
          this.showingImage = false;
          this.imageSurface = null;
        }
      }
    }

    if (elapsed >= t.maxDuration) this.finishThought();
  }

  playSwordHum(): void {
    if (!this.swordHumSound) return;
    if (this.swordHumChannel?.getBusy()) return;
    this.swordHumChannel = this.swordHumSound.play(-1);
  }

  stopSwordHum(): void {
    this.swordHumChannel?.stop();
    this.swordHumChannel = null;
  }

  /** Viento del barranco: 0 lo detiene; >0 suena a ese volumen. */
  setBarrancoWindVolume(volume: number): void {
    if (volume <= 0) {
      this.barrancoWindChannel?.stop();
      this.barrancoWindChannel = null;
      return;
    }
    const wind = this.musicSounds['viento'];
    if (!wind) return;
    if (!this.barrancoWindChannel || !this.barrancoWindChannel.getBusy()) {
      this.barrancoWindChannel = wind.play(-1);
    }
    this.barrancoWindChannel.setVolume(volume);
  }
}
