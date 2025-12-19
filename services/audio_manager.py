"""Sistema de gestión de audio del dungeon (música, efectos de sonido, subtítulos)."""
import pygame
import random
import threading
import time


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
        self._load_music_file('viento', "sound/viento.ogg")
        
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
        
        # Sistema de pensamientos con threading (soporta sonido, subtítulos e imágenes)
        self.thought_active = False
        self.thought_blocks_movement = False
        self.thought_thread = None
        self._thought_lock = threading.Lock()
        
        # Sistema de imágenes para pensamientos
        self.showing_image = False
        self.image_surface = None
        self.image_start_time = 0
        self.image_duration = 0
        
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
        # Si hay un pensamiento activo, update_thoughts() maneja los subtítulos
        if self.thought_active:
            return
            
        if self.showing_subtitles:
            elapsed = pygame.time.get_ticks() - self.subtitle_start_time
            if elapsed >= self.subtitle_duration:
                self.showing_subtitles = False
                self.subtitle_text = ""
    
    def _thought_worker(self, sounds, images, subtitles):
        """Thread worker que ejecuta un pensamiento completo.
        
        Args:
            sounds: Lista de tuplas (sound_obj, duración_ms) donde duración 0 = duración del audio
            images: Lista de tuplas (image_surface, duración_ms) donde duración 0 = duración del sonido
            subtitles: Lista de tuplas (texto, duración_ms)
        """
        components = []
        if sounds: components.append(f"{len(sounds)} sonidos")
        if images: components.append(f"{len(images)} imágenes")
        if subtitles: components.append(f"{len(subtitles)} subtítulos")
        print(f"[DEBUG] Thread iniciado con: {', '.join(components) if components else 'nada'}")
        
        # Calcular la duración máxima entre todos los elementos
        max_duration = 0
        
        # Procesar sonidos primero para obtener su duración total
        sound_timeline = []
        sound_total_duration = 0
        current_time = 0
        if sounds:
            for sound_obj, duration_ms in sounds:
                if sound_obj:
                    if duration_ms == 0:
                        # Obtener duración real del sonido
                        actual_duration = int(sound_obj.get_length() * 1000)
                        sound_timeline.append((current_time, sound_obj, actual_duration))
                        current_time += actual_duration
                    else:
                        sound_timeline.append((current_time, sound_obj, duration_ms))
                        current_time += duration_ms
            sound_total_duration = current_time
            max_duration = max(max_duration, sound_total_duration)
        
        # Procesar imágenes (duración 0 = duración del sonido)
        image_timeline = []
        current_time = 0
        if images:
            for image_obj, duration_ms in images:
                if image_obj:
                    # Si duración es 0, usar la duración del sonido
                    actual_duration = sound_total_duration if duration_ms == 0 else duration_ms
                    if actual_duration <= 0:
                        print("[ERROR] Duración de imagen debe ser > 0 (o usar 0 con sonido)")
                        continue
                    image_timeline.append((current_time, image_obj, actual_duration))
                    current_time += actual_duration
            max_duration = max(max_duration, current_time)
        
        # Procesar subtítulos
        subtitle_timeline = []
        current_time = 0
        if subtitles:
            for text, duration_ms in subtitles:
                if text:
                    if duration_ms <= 0:
                        print("[ERROR] Duración de subtítulo debe ser > 0")
                        continue
                    subtitle_timeline.append((current_time, text, duration_ms))
                    current_time += duration_ms
            max_duration = max(max_duration, current_time)
        
        print(f"[DEBUG] Duración total del pensamiento: {max_duration}ms")
        
        # Reproducir todos los sonidos al inicio de su tiempo
        for start_time, sound_obj, duration_ms in sound_timeline:
            if start_time == 0:
                sound_obj.play()
                print(f"[DEBUG] Reproduciendo sonido (duración: {duration_ms if duration_ms > 0 else 'auto'}ms)")
        
        # Ejecutar la línea de tiempo
        start_ticks = pygame.time.get_ticks()
        current_subtitle_index = 0
        current_image_index = 0
        current_sound_index = 1  # Ya reprodujimos el primero
        
        while True:
            elapsed = pygame.time.get_ticks() - start_ticks
            
            # Activar sonidos según su timeline
            while current_sound_index < len(sound_timeline):
                sound_start, sound_obj, _ = sound_timeline[current_sound_index]
                if elapsed >= sound_start:
                    sound_obj.play()
                    print(f"[DEBUG] Reproduciendo sonido {current_sound_index + 1}/{len(sound_timeline)}")
                    current_sound_index += 1
                else:
                    break
            
            # Actualizar subtítulos según su timeline
            if current_subtitle_index < len(subtitle_timeline):
                sub_start, sub_text, sub_duration = subtitle_timeline[current_subtitle_index]
                if elapsed >= sub_start:
                    with self._thought_lock:
                        self.showing_subtitles = True
                        self.subtitle_text = sub_text
                        self.subtitle_duration = sub_duration
                        self.subtitle_start_time = pygame.time.get_ticks()
                    print(f"[DEBUG] Subtítulo {current_subtitle_index + 1}/{len(subtitle_timeline)}: '{sub_text[:30]}...' por {sub_duration}ms")
                    current_subtitle_index += 1
                elif current_subtitle_index > 0:
                    # Verificar si el subtítulo actual expiró
                    prev_start, prev_text, prev_duration = subtitle_timeline[current_subtitle_index - 1]
                    if elapsed >= prev_start + prev_duration:
                        with self._thought_lock:
                            self.showing_subtitles = False
                            self.subtitle_text = ""
            
            # Actualizar imágenes según su timeline
            if current_image_index < len(image_timeline):
                img_start, img_surface, img_duration = image_timeline[current_image_index]
                if elapsed >= img_start:
                    with self._thought_lock:
                        self.showing_image = True
                        self.image_surface = img_surface
                        self.image_duration = img_duration
                        self.image_start_time = pygame.time.get_ticks()
                    print(f"[DEBUG] Imagen {current_image_index + 1}/{len(image_timeline)} por {img_duration}ms")
                    current_image_index += 1
                elif current_image_index > 0:
                    # Verificar si la imagen actual expiró
                    prev_start, prev_surface, prev_duration = image_timeline[current_image_index - 1]
                    if elapsed >= prev_start + prev_duration:
                        with self._thought_lock:
                            self.showing_image = False
                            self.image_surface = None
            
            # Terminar cuando se alcanza la duración máxima
            if elapsed >= max_duration:
                break
            
            # Pequeña pausa para no saturar el CPU
            time.sleep(0.01)
        
        print("[DEBUG] Thread finalizando, limpiando")
        # Limpiar al finalizar
        with self._thought_lock:
            self.showing_subtitles = False
            self.subtitle_text = ""
            self.showing_image = False
            self.image_surface = None
            self.thought_active = False
            self.thought_blocks_movement = False
    
    def trigger_thought(self, sounds=None, images=None, subtitles=None, blocks_movement=False):
        """Activa un pensamiento con arrays de sonidos, imágenes y subtítulos.
        
        Args:
            sounds: Lista de tuplas (sound_obj, duración_ms) donde duración 0 = duración del audio
            images: Lista de tuplas (image_surface, duración_ms) donde duración 0 = duración del sonido
            subtitles: Lista de tuplas (texto, duración_ms)
            blocks_movement: Si bloquea el movimiento del jugador
            
        Ejemplos:
            # Solo sonido que se reproduce completo
            trigger_thought(sounds=[(sound1, 0)])
            
            # Dos sonidos secuenciales
            trigger_thought(sounds=[(sound1, 0), (sound2, 0)])
            
            # Sonido + subtítulos sincronizados
            trigger_thought(
                sounds=[(intro_sound, 0)],
                subtitles=[("Texto 1", 4000), ("Texto 2", 6000)]
            )
            
            # Sonido + imagen (imagen dura lo que el sonido)
            trigger_thought(
                sounds=[(blood_sound, 0)],
                images=[(blood_img, 0)]  # Duración automática = duración del sonido
            )
            
            # Imagen con duración específica + subtítulo
            trigger_thought(
                images=[(exit_img, 10000)],
                subtitles=[("Has encontrado la salida", 8000)]
            )
        """
        components = []
        if sounds: components.append(f"{len(sounds)} sonidos")
        if images: components.append(f"{len(images)} imágenes")
        if subtitles: components.append(f"{len(subtitles)} subtítulos")
        print(f"[DEBUG] trigger_thought: {', '.join(components) if components else 'vacío'}, blocks={blocks_movement}, active={self.thought_active}")
        
        # No iniciar un nuevo pensamiento si ya hay uno activo
        if self.thought_active:
            print("[DEBUG] Ya hay un pensamiento activo, ignorando")
            return
        
        # Validar duraciones (0 es válido para imágenes si hay sonido)
        if images:
            for img, duration in images:
                if duration < 0:
                    print("[ERROR] Las imágenes requieren duración >= 0")
                    return
                if duration == 0 and not sounds:
                    print("[ERROR] Imagen con duración 0 requiere un sonido")
                    return
        
        if subtitles:
            for text, duration in subtitles:
                if duration <= 0:
                    print("[ERROR] Los subtítulos requieren duración > 0")
                    return
        
        with self._thought_lock:
            self.thought_active = True
            self.thought_blocks_movement = blocks_movement
        
        # Crear y lanzar el thread
        self.thought_thread = threading.Thread(
            target=self._thought_worker,
            args=(sounds, images, subtitles),
            daemon=True
        )
        self.thought_thread.start()
        print("[DEBUG] Thread lanzado")
    
    def update_thoughts(self):
        """Actualiza el estado de los pensamientos (ahora manejado por threads)."""
        # El thread maneja todo automáticamente, solo verificamos si terminó
        if self.thought_thread and not self.thought_thread.is_alive():
            with self._thought_lock:
                if not self.thought_active:
                    self.thought_thread = None
    
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
