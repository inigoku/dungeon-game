"""Sistema de gestión de audio del dungeon (música, efectos de sonido, subtítulos)."""
import pygame
import random


class AudioManager:
    """Gestiona toda la reproducción de audio del juego: música, efectos y subtítulos."""
    
    def __init__(self):
        """Inicializa el sistema de audio."""
        # Canal dedicado para música
        self.music_channel = pygame.mixer.Channel(0)
        self.music_channel.set_volume(0.5)
        
        # Cargar archivos de música
        self.music_sounds = {}
        self._load_music_file('intro', "sound/intro.ogg")
        self._load_music_file('adagio', "sound/adagio.ogg")
        self._load_music_file('cthulhu', "sound/cthulhu.ogg")
        
        # Estado de la música
        self.current_music = None
        self.intro_sound = None
        self.cthulhu_played = False
        self.music_volume = 0.5
        
        # Sistema de fade
        self.fading_out = False
        self.fading_in = False
        self.fade_start_time = 0
        self.fade_duration = 1000  # 1 segundo
        self.fade_from_volume = 0.5
        self.fade_to_volume = 0.0
        self.pending_music_load = None
        
        # Sistema de subtítulos
        self.showing_subtitles = False
        self.subtitle_text = ""
        self.subtitle_start_time = 0
        self.subtitle_duration = 0
        
        # Sistema de pensamientos
        self.thought_active = False
        self.thought_blocks_movement = False
        self.thought_sound = None
        self.thought_subtitles = []
        self.thought_current_subtitle_index = 0
        self.thought_subtitle_start_time = 0
        
        # Sonidos de efectos
        self.blood_sound = None
        self._load_effect('blood', "sound/sangre.ogg", 0.7)
        
        self.footstep_sounds = []
        self._load_footstep("sound/paso1.ogg", 0.4)
        self._load_footstep("sound/paso2.ogg", 0.4)
        self.last_footstep_index = 0
        
        # Ambient sounds
        self.last_ambient_sound_time = pygame.time.get_ticks()
        self.next_ambient_sound_delay = random.randint(3000, 20000)
        
        # Guardar intro como pensamiento inicial
        if 'intro' in self.music_sounds:
            self.intro_sound = self.music_sounds['intro']
    
    def _load_music_file(self, key, path):
        """Carga un archivo de música."""
        try:
            self.music_sounds[key] = pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"No se pudo cargar {path}: {e}")
    
    def _load_effect(self, attr_name, path, volume):
        """Carga un efecto de sonido."""
        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(volume)
            setattr(self, f"{attr_name}_sound", sound)
        except pygame.error as e:
            print(f"No se pudo cargar {path}: {e}")
    
    def _load_footstep(self, path, volume):
        """Carga un sonido de paso."""
        try:
            step = pygame.mixer.Sound(path)
            step.set_volume(volume)
            self.footstep_sounds.append(step)
        except pygame.error as e:
            print(f"No se pudo cargar {path}: {e}")
    
    def play_music(self, music_key, loops=-1):
        """Reproduce música en loop.
        
        Args:
            music_key: Clave de la música ('intro', 'adagio', 'cthulhu')
            loops: Número de repeticiones (-1 = infinito)
        """
        if music_key in self.music_sounds:
            self.current_music = music_key
            self.music_channel.play(self.music_sounds[music_key], loops=loops)
            self.music_channel.set_volume(self.music_volume)
    
    def stop_music(self):
        """Detiene la música actual."""
        self.music_channel.stop()
        self.current_music = None
    
    def start_fade_out(self, duration=1000, next_music=None):
        """Inicia un fade out de la música.
        
        Args:
            duration: Duración del fade en ms
            next_music: Música a reproducir después del fade (opcional)
        """
        self.fading_out = True
        self.fading_in = False
        self.fade_start_time = pygame.time.get_ticks()
        self.fade_duration = duration
        self.fade_from_volume = self.music_volume
        self.fade_to_volume = 0.0
        self.pending_music_load = next_music
    
    def start_fade_in(self, duration=1000, target_volume=0.5):
        """Inicia un fade in de la música.
        
        Args:
            duration: Duración del fade en ms
            target_volume: Volumen objetivo
        """
        self.fading_in = True
        self.fading_out = False
        self.fade_start_time = pygame.time.get_ticks()
        self.fade_duration = duration
        self.fade_from_volume = 0.0
        self.fade_to_volume = target_volume
        self.music_volume = 0.0
        self.music_channel.set_volume(0.0)
    
    def update_fades(self):
        """Actualiza el estado de los fades de música."""
        current_time = pygame.time.get_ticks()
        
        if self.fading_out:
            elapsed = current_time - self.fade_start_time
            if elapsed >= self.fade_duration:
                # Fade completado
                self.fading_out = False
                self.music_volume = self.fade_to_volume
                self.music_channel.set_volume(self.music_volume)
                self.music_channel.stop()
                
                # Cargar música pendiente si hay
                if self.pending_music_load:
                    self.play_music(self.pending_music_load)
                    self.pending_music_load = None
                    self.start_fade_in(self.fade_duration, 0.5)
            else:
                # Interpolar volumen
                progress = elapsed / self.fade_duration
                self.music_volume = self.fade_from_volume + (self.fade_to_volume - self.fade_from_volume) * progress
                self.music_channel.set_volume(self.music_volume)
        
        elif self.fading_in:
            elapsed = current_time - self.fade_start_time
            if elapsed >= self.fade_duration:
                # Fade completado
                self.fading_in = False
                self.music_volume = self.fade_to_volume
                self.music_channel.set_volume(self.music_volume)
            else:
                # Interpolar volumen
                progress = elapsed / self.fade_duration
                self.music_volume = self.fade_from_volume + (self.fade_to_volume - self.fade_from_volume) * progress
                self.music_channel.set_volume(self.music_volume)
    
    def show_subtitle(self, text, duration):
        """Muestra un subtítulo.
        
        Args:
            text: Texto a mostrar
            duration: Duración en ms
        """
        self.showing_subtitles = True
        self.subtitle_text = text
        self.subtitle_start_time = pygame.time.get_ticks()
        self.subtitle_duration = duration
    
    def update_subtitles(self):
        """Actualiza el estado de los subtítulos."""
        if self.showing_subtitles:
            elapsed = pygame.time.get_ticks() - self.subtitle_start_time
            if elapsed >= self.subtitle_duration:
                self.showing_subtitles = False
                self.subtitle_text = ""
    
    def trigger_thought(self, sound_obj, subtitles, blocks_movement=False):
        """Activa un pensamiento con sonido y subtítulos.
        
        Args:
            sound_obj: Objeto Sound de pygame
            subtitles: Lista de tuplas (texto, duración_ms)
            blocks_movement: Si bloquea el movimiento del jugador
        """
        self.thought_active = True
        self.thought_sound = sound_obj
        self.thought_subtitles = subtitles
        self.thought_current_subtitle_index = 0
        self.thought_blocks_movement = blocks_movement
        
        # Reproducir sonido
        if sound_obj:
            sound_obj.play()
        
        # Mostrar primer subtítulo
        if subtitles:
            text, duration = subtitles[0]
            self.show_subtitle(text, duration)
            self.thought_subtitle_start_time = pygame.time.get_ticks()
    
    def update_thoughts(self):
        """Actualiza el estado de los pensamientos."""
        if not self.thought_active:
            return
        
        # Verificar si el sonido terminó
        if self.thought_sound and not pygame.mixer.get_busy():
            # Solo si el canal del pensamiento no está activo
            # (asumiendo que los pensamientos no usan el canal de música)
            pass
        
        # Actualizar subtítulos del pensamiento
        if self.thought_current_subtitle_index < len(self.thought_subtitles):
            text, duration = self.thought_subtitles[self.thought_current_subtitle_index]
            elapsed = pygame.time.get_ticks() - self.thought_subtitle_start_time
            
            if elapsed >= duration:
                # Pasar al siguiente subtítulo
                self.thought_current_subtitle_index += 1
                if self.thought_current_subtitle_index < len(self.thought_subtitles):
                    text, duration = self.thought_subtitles[self.thought_current_subtitle_index]
                    self.show_subtitle(text, duration)
                    self.thought_subtitle_start_time = pygame.time.get_ticks()
                else:
                    # Todos los subtítulos mostrados
                    self.thought_active = False
                    self.thought_blocks_movement = False
    
    def play_footstep(self):
        """Reproduce un sonido de paso alternando entre paso1 y paso2."""
        if self.footstep_sounds:
            footstep = self.footstep_sounds[self.last_footstep_index % len(self.footstep_sounds)]
            footstep.play()
            self.last_footstep_index += 1
    
    def play_blood_sound(self):
        """Reproduce el sonido de sangre."""
        if self.blood_sound:
            self.blood_sound.play()
    
    def update(self):
        """Actualiza todos los sistemas de audio."""
        self.update_fades()
        self.update_subtitles()
        self.update_thoughts()
