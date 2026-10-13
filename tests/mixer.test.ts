import { afterEach, describe, expect, it, vi } from 'vitest';
import { Channel, Mixer, Sound } from '../src/audio';

/** AudioContext mínimo: solo lleva la cuenta de las fuentes que están sonando. */
function installFakeAudio() {
  const playing = new Set<object>();
  const node = () => ({ connect: (next: unknown) => next, disconnect: vi.fn(), gain: { value: 1, cancelScheduledValues: vi.fn() } });
  class FakeContext {
    state = 'running';
    destination = {};
    createGain = node;
    createBufferSource() {
      const source = {
        ...node(),
        buffer: null,
        loop: false,
        onended: null as (() => void) | null,
        start: () => playing.add(source),
        stop: () => playing.delete(source),
      };
      return source;
    }
  }
  vi.stubGlobal('window', { AudioContext: FakeContext });
  return playing;
}

afterEach(() => vi.unstubAllGlobals());

describe('Mixer.stopAll', () => {
  it('silencia canales persistentes y sonidos de un solo uso', () => {
    const playing = installFakeAudio();
    const mixer = new Mixer();
    const sound = new Sound(mixer, {} as AudioBuffer);

    const music = new Channel(mixer);
    music.play(sound, -1);
    sound.play(); // paso, grito, gruñido...
    sound.play(-1); // zumbido de la espada
    expect(playing.size).toBe(3);

    mixer.stopAll();
    expect(playing.size).toBe(0);
    expect(music.getBusy()).toBe(false);
  });

  it('un canal de un solo uso detenido se olvida', () => {
    const playing = installFakeAudio();
    const mixer = new Mixer();
    const channel = new Sound(mixer, {} as AudioBuffer).play();
    channel.stop();
    mixer.stopAll();
    expect(playing.size).toBe(0);
  });
});
