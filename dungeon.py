import pygame
import random
import math
import sys
import os
import asyncio
from enum import Enum
from dataclasses import dataclass

# Importar módulos refactorizados
try:
    from services.lighting_system import LightingSystem
    from services.audio_manager import AudioManager
    from rendering.decorations import DecorationRenderer
    from rendering.effects import EffectsRenderer
    REFACTORED_MODULES = True
except ImportError:
    REFACTORED_MODULES = False
    print("Usando versión sin refactorizar")

class CellType(Enum):
    EMPTY = 0
    INICIO = 1
    PASILLO = 2
    HABITACION = 3
    SALIDA = 4

class Direction(Enum):
    N = "N"
    E = "E"
    S = "S"
    O = "O"

@dataclass
class Cell:
    cell_type: CellType
    exits: set = None
    
    def __post_init__(self):
        if self.exits is None:
            self.exits = set()

# Constantes de configuración
DEFAULT_BOARD_SIZE = 101
DEFAULT_VIEW_SIZE = 7
DEFAULT_CELL_SIZE = 90

class DungeonBoard:
    def __init__(self, size=DEFAULT_BOARD_SIZE, view_size=DEFAULT_VIEW_SIZE, cell_size=DEFAULT_CELL_SIZE):
        self.size = size
        self.initial_view_size = view_size  # Vista inicial de 7x7
        self.view_size = view_size
        self.base_cell_size = cell_size  # Tamaño base de celda
        self.cell_size = cell_size
        
        # Sistema de zoom: 5 niveles de 7x7 hasta el tamaño completo del tablero
        self.zoom_levels = [7, 11, 21, 51, size]  # 5 niveles de zoom
        self.current_zoom_index = 0  # Empieza en el más cercano (7x7)
        
        # Tamaño fijo de ventana
        self.fixed_window_size = view_size * cell_size  # 630x630 pixels
        
        self.board = [[Cell(CellType.EMPTY) for _ in range(size)] for _ in range(size)]
        
        # Set central cell as INICIO
        center = size // 2
        self.board[center][center] = Cell(CellType.INICIO , {Direction.N, Direction.E, Direction.S, Direction.O})
        # Guardar centro y estado de interacción
        self.current_position = (center, center)
        self.start_position = (center, center)  # Posición inicial para calcular distancia
        
        # Generar posición de salida aleatoria y calcular camino principal
        # Reintentar hasta conseguir conectividad
        print("Generando mapa...")
        max_generation_attempts = 10
        generation_attempt = 0
        connectivity_verified = False
        
        while not connectivity_verified and generation_attempt < max_generation_attempts:
            generation_attempt += 1
            if generation_attempt > 1:
                print(f"Intento {generation_attempt}: Regenerando mapa...")
            
            # Limpiar el tablero excepto la celda de inicio
            for row in range(self.size):
                for col in range(self.size):
                    if (row, col) != (center, center):
                        self.board[row][col] = Cell(CellType.EMPTY, set())
            
            # Generar nueva posición de salida
            self.exit_position = self.generate_exit_position(center)
            
            # Calcular camino principal
            self.main_path = self.calculate_main_path((center, center), self.exit_position)
            
            # Generar todas las celdas del camino principal
            self.generate_main_path_cells()
            
            # Verificar conectividad
            connectivity_verified = self.check_connectivity((center, center), self.exit_position)
        
        if not connectivity_verified:
            print("Advertencia: No se pudo generar un mapa con conectividad garantizada después de 10 intentos")
        else:
            print("Mapa generado exitosamente")
        
        # Sistema de niebla de guerra: rastrear celdas visitadas
        self.visited_cells = set()
        self.visited_cells.add((center, center))  # La celda inicial está visitada
        
        # Scroll suave: cámara flotante que se interpola hacia la posición del jugador
        self.camera_offset_row = float(center - view_size // 2)
        self.camera_offset_col = float(center - view_size // 2)
        self.camera_speed = 0.03  # Factor de interpolación (0-1), mayor = más rápido
        
        pygame.init()
        pygame.mixer.init()
        self.width = self.fixed_window_size
        self.height = self.fixed_window_size
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Dungeon 2D")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        # Canal dedicado para música (compatible con web)
        self.music_channel = pygame.mixer.Channel(0)
        self.music_channel.set_volume(0.5)
        
        # Obtener directorio del script para rutas relativas
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Cargar archivos de música como Sound objects
        self.music_sounds = {}
        try:
            self.music_sounds['intro'] = pygame.mixer.Sound(os.path.join(script_dir, "sound/intro.ogg"))
        except pygame.error as e:
            print(f"No se pudo cargar sound/intro.ogg: {e}")
        try:
            self.music_sounds['adagio'] = pygame.mixer.Sound(os.path.join(script_dir, "sound/adagio.ogg"))
        except pygame.error as e:
            print(f"No se pudo cargar sound/adagio.ogg: {e}")
        try:
            self.music_sounds['cthulhu'] = pygame.mixer.Sound(os.path.join(script_dir, "sound/cthulhu.ogg"))
        except pygame.error as e:
            print(f"No se pudo cargar sound/cthulhu.ogg: {e}")
        try:
            self.music_sounds['viento'] = pygame.mixer.Sound(os.path.join(script_dir, "sound/viento.ogg"))
        except pygame.error as e:
            print(f"No se pudo cargar sound/viento.ogg: {e}")
        
        # Sistema de música: adagio desde el principio, cthulhu en la salida
        self.current_music = None
        self.intro_sound = None  # intro.ogg se usará como pensamiento
        self.cthulhu_played = False
        self.music_volume = 0.5
        
        # Sistema de fade de música
        self.fading_out = False
        self.fading_in = False
        self.fade_start_time = 0
        self.fade_duration = 1000  # 1 segundo de fade
        self.fade_from_volume = 0.5
        self.fade_to_volume = 0.0
        self.pending_music_load = None  # Música a cargar después del fade out
        
        # Sistema de subtítulos
        self.showing_subtitles = False
        self.subtitle_text = ""
        self.subtitle_start_time = 0
        self.subtitle_duration = 0
        
        # Sistema de pensamientos (sonido + subtítulos)
        self.thought_active = False
        self.thought_blocks_movement = False  # Si el pensamiento actual bloquea movimiento
        self.thought_sound = None
        self.thought_subtitles = []  # Lista de (texto, duración)
        self.thought_current_subtitle_index = 0
        self.thought_subtitle_start_time = 0
        
        # Sistema de iluminación y renderizado (refactorizado)
        if REFACTORED_MODULES:
            self.lighting = LightingSystem()
            self.decorations = DecorationRenderer(self.screen, self.cell_size)
            self.effects = EffectsRenderer(self.screen, self.cell_size)
            self.audio = AudioManager()
        else:
            # Toggle para oscurecimiento de líneas (F5) - versión legacy
            self.lines_darkening_enabled = True
        
        # Guardar intro.ogg como pensamiento inicial
        if 'intro' in self.music_sounds:
            self.intro_sound = self.music_sounds['intro']
        
        # Reproducir adagio desde el principio en loop
        if 'adagio' in self.music_sounds:
            self.current_music = 'adagio'
            self.music_channel.play(self.music_sounds['adagio'], loops=-1)
            self.music_channel.set_volume(self.music_volume)
            self.current_music = 'adagio'
            self.music_channel.play(self.music_sounds['adagio'], loops=-1)
            self.music_channel.set_volume(self.music_volume)
            self.intro_played = True
        
        # Paleta y parámetros para el sprite del jugador (guerrero)
        self.player_palette = {
            "armor": (90, 90, 90),
            "trim": (140, 140, 140),
            "skin": (200, 170, 140),
            "shield": (70, 70, 70),
            "shield_trim": (140, 120, 80),
            "sword_handle": (180, 140, 80),
            "sword_blade": (200, 200, 200),
        }
        # Velocidad de animación (ciclos por milisegundo aproximado)
        self.player_anim_speed = 0.004
        # Amplitud del movimiento de piernas/brazos
        self.player_anim_amp = 1.0
        # Estado de movimiento: animación de interpolación entre celdas
        self.player_walk_duration = 450  # ms (aumentado para animación más larga)
        self.player_walk_until = 0  # timestamp en ms hasta el que se considera "caminando"
        # Animación de posición: el muñeco se mueve suavemente de una celda a otra
        self.player_animating = False
        self.player_anim_start_time = 0
        self.player_anim_from_pos = self.current_position  # (row, col) de origen
        self.player_anim_to_pos = self.current_position    # (row, col) de destino
        self.player_anim_duration = 450  # ms para movimiento suave
        
        # Pantalla de título
        self.showing_title = True
        self.title_image = None
        try:
            self.title_image = pygame.image.load(os.path.join(script_dir, "images/titulo.png")).convert()
            # Escalar la imagen al tamaño de la ventana con alta calidad si es necesario
            if self.title_image.get_size() != (self.width, self.height):
                self.title_image = pygame.transform.smoothscale(self.title_image, (self.width, self.height))
        except pygame.error as e:
            print(f"No se pudo cargar images/titulo.png: {e}")
            self.showing_title = False
        
        # Confirmación de salida y menú principal
        self.asking_exit_confirmation = False
        self.asking_main_menu_confirmation = False
        
        # Animación de inicio
        self.intro_anim_active = False  # Se activará después de la pantalla de título
        self.intro_anim_start_time = 0
        self.intro_anim_stage = 0  # 0=caída, 1=mirar izquierda, 2=mirar derecha, 3=sacar armas, 4=completo
        self.intro_show_weapons = False  # Las armas aparecen al final
        
        # Efectos de sonido ambientales (con probabilidades ponderadas)
        self.ambient_sounds = {}
        try:
            drip_sound = pygame.mixer.Sound(os.path.join(script_dir, "sound/gota.ogg"))
            drip_sound.set_volume(0.5)
            self.ambient_sounds['gota'] = drip_sound
        except pygame.error as e:
            print(f"No se pudo cargar sound/gota.ogg: {e}")
        
        try:
            two_drips_sound = pygame.mixer.Sound(os.path.join(script_dir, "sound/dos-gotas.ogg"))
            two_drips_sound.set_volume(0.5)
            self.ambient_sounds['dos-gotas'] = two_drips_sound
        except pygame.error as e:
            print(f"No se pudo cargar sound/dos-gotas.ogg: {e}")
        
        try:
            bat_sound = pygame.mixer.Sound(os.path.join(script_dir, "sound/murcielago.ogg"))
            bat_sound.set_volume(0.6)
            self.ambient_sounds['murcielago'] = bat_sound
        except pygame.error as e:
            print(f"No se pudo cargar sound/murcielago.ogg: {e}")
        
        # Probabilidades para cada sonido (deben sumar 1.0)
        # 40% gota, 40% dos-gotas, 20% murciélago
        self.ambient_sound_weights = {
            'gota': 0.40,
            'dos-gotas': 0.40,
            'murcielago': 0.20
        }
        
        # Sonido de antorchas (usado para pensamientos)
        self.torch_sound = None
        try:
            self.torch_sound = pygame.mixer.Sound(os.path.join(script_dir, "sound/antorchas.ogg"))
            self.torch_sound.set_volume(0.7)
        except pygame.error as e:
            print(f"No se pudo cargar sound/antorchas.ogg: {e}")
        
        self.torch_thought_triggered = False  # Flag para el pensamiento de antorchas
        self.intro_thought_triggered = False  # Flag para el pensamiento de intro
        self.intro_thought_finished = False  # Flag para cuando termina el pensamiento de intro
        
        # Sonido de sangre (usado para pensamientos)
        self.blood_sound = None
        try:
            self.blood_sound = pygame.mixer.Sound(os.path.join(script_dir, "sound/sangre.ogg"))
            self.blood_sound.set_volume(0.7)
        except pygame.error as e:
            print(f"No se pudo cargar sound/sangre.ogg: {e}")
        
        self.blood_thought_triggered = False  # Flag para el pensamiento de sangre
        
        # Sonido de ráfaga (para cuando se apagan las antorchas)
        self.rafaga_sound = None
        try:
            self.rafaga_sound = pygame.mixer.Sound(os.path.join(script_dir, "sound/rafaga.ogg"))
            self.rafaga_sound.set_volume(0.9)
        except pygame.error as e:
            print(f"No se pudo cargar sound/rafaga.ogg: {e}")
        
        self.rafaga_thought_triggered = False  # Flag para el pensamiento de ráfaga
        self.torches_flickering = False  # Flag para el parpadeo de antorchas
        self.flicker_start_time = 0  # Tiempo de inicio del parpadeo
        self.flicker_duration = 0  # Duración del parpadeo (se establece dinámicamente)
        self.wind_fade_start_time = 0  # Tiempo de inicio del fade-in del viento
        self.wind_fading_in = False  # Flag para el fade-in del viento
        
        # Sonidos de pasos
        self.footstep_sounds = []
        try:
            step1 = pygame.mixer.Sound(os.path.join(script_dir, "sound/paso1.ogg"))
            step1.set_volume(0.4)
            self.footstep_sounds.append(step1)
        except pygame.error as e:
            print(f"No se pudo cargar sound/paso1.ogg: {e}")
        
        try:
            step2 = pygame.mixer.Sound(os.path.join(script_dir, "sound/paso2.ogg"))
            step2.set_volume(0.4)
            self.footstep_sounds.append(step2)
        except pygame.error as e:
            print(f"No se pudo cargar sound/paso2.ogg: {e}")
        
        self.last_footstep_index = 0  # Para alternar entre paso1 y paso2
        
        self.last_ambient_sound_time = pygame.time.get_ticks()
        self.next_ambient_sound_delay = random.randint(3000, 20000)  # 3-20 segundos (más aleatorio)
        
        # Sistema de final del juego con imagen de losa
        self.exit_image_shown = False
        self.exit_image_start_time = 0
        self.exit_image = None
        self.torch_image = None
        self.blood_image = None
        self.thought_image = None  # Imagen actual del pensamiento (separada de exit_image)
        self.thought_image_shown = False
        self.thought_image_start_time = 0
        self.torches_extinguished = False  # Flag para apagar antorchas después de la losa
        
        # Cargar imagen de losa (salida)
        try:
            original_image = pygame.image.load(os.path.join(script_dir, "images/losa.png"))
            # Escalar manteniendo la proporción para que quepa en la pantalla
            original_width = original_image.get_width()
            original_height = original_image.get_height()
            
            # Calcular escala para que quepa en la pantalla dejando espacio para subtítulos
            max_width = self.width * 0.9
            # Reservar 120px en la parte inferior para subtítulos
            max_height = (self.height - 120) * 0.9
            
            scale_width = max_width / original_width
            scale_height = max_height / original_height
            scale = min(scale_width, scale_height)  # Usar la escala menor para mantener proporción
            
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            
            self.exit_image = pygame.transform.smoothscale(original_image, (new_width, new_height))
            print(f"[DEBUG] Imagen de losa cargada: {new_width}x{new_height}")
        except pygame.error as e:
            print(f"No se pudo cargar images/losa.png: {e}")
        
        # Cargar imagen de antorcha
        try:
            torch_img = pygame.image.load(os.path.join(script_dir, "images/antorcha.png"))
            # Escalar a un tamaño apropiado
            max_size = min(self.width, self.height) * 0.6
            scale = max_size / max(torch_img.get_width(), torch_img.get_height())
            new_w = int(torch_img.get_width() * scale)
            new_h = int(torch_img.get_height() * scale)
            self.torch_image = pygame.transform.smoothscale(torch_img, (new_w, new_h))
        except pygame.error as e:
            print(f"No se pudo cargar images/antorcha.png: {e}")
        
        # Cargar imagen de sangre
        try:
            blood_img = pygame.image.load(os.path.join(script_dir, "images/sangre.png"))
            # Escalar a un tamaño apropiado
            max_size = min(self.width, self.height) * 0.6
            scale = max_size / max(blood_img.get_width(), blood_img.get_height())
            new_w = int(blood_img.get_width() * scale)
            new_h = int(blood_img.get_height() * scale)
            self.blood_image = pygame.transform.smoothscale(blood_img, (new_w, new_h))
        except pygame.error as e:
            print(f"No se pudo cargar images/sangre.png: {e}")
        
        # Debug mode
        self.debug_mode = False
        self.show_path = False  # F4 para mostrar el camino completo
        self.auto_reveal_mode = False  # F2 para activar/desactivar revelación automática
    
    def get_view_offset(self):
        """Interpola la cámara hacia la posición del jugador y retorna el offset redondeado."""
        player_row, player_col = self.current_position
        
        # Posición objetivo: centrar al jugador en la vista
        target_offset_row = max(0, min(player_row - self.view_size // 2, self.size - self.view_size))
        target_offset_col = max(0, min(player_col - self.view_size // 2, self.size - self.view_size))
        
        # Interpolación suave (lerp)
        self.camera_offset_row += (target_offset_row - self.camera_offset_row) * self.camera_speed
        self.camera_offset_col += (target_offset_col - self.camera_offset_col) * self.camera_speed
        
        # Asegurar que no sobrepasa los límites
        self.camera_offset_row = max(0, min(self.camera_offset_row, self.size - self.view_size))
        self.camera_offset_col = max(0, min(self.camera_offset_col, self.size - self.view_size))
        
        # Retornar valores flotantes para scroll suave en píxeles
        return self.camera_offset_row, self.camera_offset_col
    
    def check_connectivity(self, start, end):
        """Verifica si hay un camino posible entre start y end usando BFS.
        Verifica que las celdas adyacentes tengan salidas enfrentadas.
        Retorna True si hay conectividad, False si no."""
        from collections import deque
        
        queue = deque([start])
        visited = {start}
        
        # Mapeo de direcciones a deltas y direcciones opuestas
        direction_deltas = {
            Direction.N: (-1, 0),
            Direction.S: (1, 0),
            Direction.E: (0, 1),
            Direction.O: (0, -1),
        }
        
        opposite_directions = {
            Direction.N: Direction.S,
            Direction.S: Direction.N,
            Direction.E: Direction.O,
            Direction.O: Direction.E,
        }
        
        while queue:
            curr_row, curr_col = queue.popleft()
            
            if (curr_row, curr_col) == end:
                return True
            
            # Obtener la celda actual
            curr_cell = self.board[curr_row][curr_col]
            
            # Explorar vecinos solo si hay salida hacia ellos
            for direction, (dr, dc) in direction_deltas.items():
                # Verificar si la celda actual tiene salida en esta dirección
                if direction not in curr_cell.exits:
                    continue
                
                next_row = curr_row + dr
                next_col = curr_col + dc
                next_pos = (next_row, next_col)
                
                # Verificar límites y si ya fue visitada
                if not (0 <= next_row < self.size and 0 <= next_col < self.size):
                    continue
                if next_pos in visited:
                    continue
                
                # Obtener la celda vecina
                next_cell = self.board[next_row][next_col]
                
                # Verificar que la celda vecina no sea EMPTY
                if next_cell.cell_type == CellType.EMPTY:
                    continue
                
                # Verificar que la celda vecina tenga la salida complementaria
                opposite = opposite_directions[direction]
                if opposite not in next_cell.exits:
                    continue
                
                # Si todo está bien, agregar a la cola
                visited.add(next_pos)
                queue.append(next_pos)
        
        return False
    
    def generate_exit_position(self, center):
        """Genera una posición aleatoria para la celda de salida, alejada del centro."""
        # Calcular distancia máxima desde el centro hasta el borde del tablero
        max_distance_to_edge = center - 5  # Restamos margen de seguridad
        
        # Distancia entre 75% y 100% de la distancia al borde
        min_distance = int(max_distance_to_edge * 0.75)
        max_distance = max_distance_to_edge
        
        # Generar posiciones candidatas
        attempts = 0
        while attempts < 100:
            # Ángulo aleatorio
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(min_distance, max_distance)
            
            row = center + int(distance * math.cos(angle))
            col = center + int(distance * math.sin(angle))
            
            # Verificar que está dentro del tablero con margen
            if 5 <= row < self.size - 5 and 5 <= col < self.size - 5:
                return (row, col)
            attempts += 1
        
        # Fallback: buscar una posición válida reduciendo gradualmente la distancia
        for fallback_distance in range(max_distance, min_distance - 1, -5):
            for fallback_angle in [0, math.pi/4, math.pi/2, 3*math.pi/4, math.pi, 5*math.pi/4, 3*math.pi/2, 7*math.pi/4]:
                row = center + int(fallback_distance * math.cos(fallback_angle))
                col = center + int(fallback_distance * math.sin(fallback_angle))
                
                # Asegurar que está dentro del tablero
                row = max(5, min(self.size - 6, row))
                col = max(5, min(self.size - 6, col))
                
                if 5 <= row < self.size - 5 and 5 <= col < self.size - 5:
                    return (row, col)
        
        # Último fallback: posición segura garantizada dentro del tablero
        safe_distance = min(min_distance, (self.size - center - 10) // 2)
        return (center + safe_distance, center + safe_distance)
    
    def calculate_main_path(self, start, end):
        """Calcula un camino tortuoso sin lazos desde start hasta end.
        Usa random walk con preferencia hacia el objetivo pero permitiendo desviaciones.
        Retorna un conjunto de tuplas (row, col) que forman el camino principal."""
        path = [start]
        current = start
        visited = {start}
        
        max_attempts = 10000  # Evitar loops infinitos
        attempts = 0
        
        while current != end and attempts < max_attempts:
            attempts += 1
            current_row, current_col = current
            end_row, end_col = end
            
            # Calcular direcciones posibles
            directions = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                next_row = current_row + dr
                next_col = current_col + dc
                next_pos = (next_row, next_col)
                
                # Verificar límites y que no hayamos visitado
                if (0 <= next_row < self.size and 0 <= next_col < self.size 
                    and next_pos not in visited):
                    # Calcular distancia al objetivo
                    dist = abs(end_row - next_row) + abs(end_col - next_col)
                    directions.append((next_pos, dist, dr, dc))
            
            if not directions:
                # Si no hay opciones, retroceder
                if len(path) > 1:
                    path.pop()
                    current = path[-1]
                else:
                    break
                continue
            
            # 70% de probabilidad de ir hacia el objetivo, 30% aleatorio (más tortuoso)
            if random.random() < 0.70:
                # Elegir la dirección que más se acerque al objetivo
                directions.sort(key=lambda x: x[1])
                next_pos = directions[0][0]
            else:
                # Movimiento aleatorio para hacer el camino más tortuoso
                next_pos = random.choice(directions)[0]
            
            visited.add(next_pos)
            path.append(next_pos)
            current = next_pos
        
        # Si no llegamos al final, usar BFS como fallback
        if current != end:
            from collections import deque
            queue = deque([(start, [start])])
            visited_bfs = {start}
            
            while queue:
                (curr_row, curr_col), bfs_path = queue.popleft()
                if (curr_row, curr_col) == end:
                    return set(bfs_path)
                
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    next_row = curr_row + dr
                    next_col = curr_col + dc
                    next_pos = (next_row, next_col)
                    
                    if (0 <= next_row < self.size and 0 <= next_col < self.size 
                        and next_pos not in visited_bfs):
                        visited_bfs.add(next_pos)
                        queue.append((next_pos, bfs_path + [next_pos]))
        
        return set(path)
    
    def generate_main_path_cells(self):
        """Genera todas las celdas del camino principal desde el inicio hasta la salida."""
        if not self.main_path:
            return
        
        # Reconstruir el camino ordenado desde inicio hasta salida
        start = self.current_position
        path_ordered = [start]
        current = start
        visited = {start}
        
        # Seguir el camino encontrando vecinos adyacentes
        while current != self.exit_position and len(visited) < len(self.main_path):
            row, col = current
            found_next = False
            
            # Buscar el siguiente vecino en el camino
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (row + dr, col + dc)
                if neighbor in self.main_path and neighbor not in visited:
                    path_ordered.append(neighbor)
                    visited.add(neighbor)
                    current = neighbor
                    found_next = True
                    break
            
            if not found_next:
                break
        
        # Generar cada celda del camino
        for i in range(len(path_ordered)):
            pos = path_ordered[i]
            row, col = pos
            
            # Saltar la celda inicial (ya existe)
            if pos == start:
                # Actualizar las salidas de la celda inicial para conectar con vecinos del camino
                exits = self.board[row][col].exits.copy()
                for dr, dc, direction in [(-1, 0, Direction.N), (1, 0, Direction.S), 
                                          (0, 1, Direction.E), (0, -1, Direction.O)]:
                    neighbor = (row + dr, col + dc)
                    if neighbor in self.main_path:
                        exits.add(direction)
                self.board[row][col] = Cell(self.board[row][col].cell_type, exits)
                continue
            
            # Crear el conjunto de salidas conectando con TODOS los vecinos del camino
            exits = set()
            
            # Verificar cada dirección para conectar con vecinos del camino
            for dr, dc, direction in [(-1, 0, Direction.N), (1, 0, Direction.S), 
                                      (0, 1, Direction.E), (0, -1, Direction.O)]:
                neighbor = (row + dr, col + dc)
                if neighbor in self.main_path:
                    exits.add(direction)
            
            # Si es la salida, solo tiene las conexiones con el camino
            if pos == self.exit_position:
                self.board[row][col] = Cell(CellType.SALIDA, exits)
            else:
                
                # Determinar tipo de celda: 75% PASILLO, 25% HABITACION
                cell_type = CellType.PASILLO if random.random() < 0.75 else CellType.HABITACION
                
                # Posibilidad de agregar salidas adicionales (menos probable para mantener camino claro)
                all_directions = {Direction.N, Direction.E, Direction.S, Direction.O}
                remaining = list(all_directions - exits)
                
                if cell_type == CellType.PASILLO:
                    # 20% de probabilidad de agregar 1 salida extra
                    if remaining and random.random() < 0.20:
                        exits.add(random.choice(remaining))
                else:  # HABITACION
                    # 10% de probabilidad de agregar 1 salida extra
                    if remaining and random.random() < 0.10:
                        exits.add(random.choice(remaining))
                
                self.board[row][col] = Cell(cell_type, exits)
        
        # Post-procesamiento: asegurar que todas las conexiones entre celdas del camino sean bidireccionales
        for pos in self.main_path:
            row, col = pos
            current_cell = self.board[row][col]
            
            # Para cada dirección, verificar si el vecino está en el camino
            for dr, dc, direction in [(-1, 0, Direction.N), (1, 0, Direction.S), 
                                      (0, 1, Direction.E), (0, -1, Direction.O)]:
                neighbor = (row + dr, col + dc)
                if neighbor in self.main_path:
                    # Si el vecino está en el camino, ambas celdas deben tener salidas mutuas
                    neighbor_cell = self.board[neighbor[0]][neighbor[1]]
                    opposite_dir = self.get_opposite_direction(direction)
                    
                    # Si esta celda tiene salida hacia el vecino, el vecino debe tener salida de vuelta
                    if direction in current_cell.exits and opposite_dir not in neighbor_cell.exits:
                        # Añadir la salida faltante al vecino
                        neighbor_exits = neighbor_cell.exits.copy()
                        neighbor_exits.add(opposite_dir)
                        self.board[neighbor[0]][neighbor[1]] = Cell(neighbor_cell.cell_type, neighbor_exits)
                    
                    # Si el vecino tiene salida hacia esta celda, esta debe tener salida de vuelta
                    if opposite_dir in neighbor_cell.exits and direction not in current_cell.exits:
                        # Añadir la salida faltante a esta celda
                        current_exits = current_cell.exits.copy()
                        current_exits.add(direction)
                        self.board[row][col] = Cell(current_cell.cell_type, current_exits)
                        current_cell = self.board[row][col]  # Actualizar referencia
    
    def get_direction_between(self, from_pos, to_pos):
        """Retorna la dirección desde from_pos hacia to_pos."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        if to_row < from_row:
            return Direction.N
        elif to_row > from_row:
            return Direction.S
        elif to_col > from_col:
            return Direction.E
        elif to_col < from_col:
            return Direction.O
        return None
    
    def center_camera_instantly(self, target_row, target_col):
        """Centra la cámara instantáneamente en la posición objetivo (sin interpolación)."""
        target_offset_row = max(0, min(target_row - self.view_size // 2, self.size - self.view_size))
        target_offset_col = max(0, min(target_col - self.view_size // 2, self.size - self.view_size))
        
        self.camera_offset_row = float(target_offset_row)
        self.camera_offset_col = float(target_offset_col)
    
    def draw(self):
        # Si estamos mostrando la pantalla de título
        if self.showing_title:
            if self.title_image:
                self.screen.blit(self.title_image, (0, 0))
            else:
                # Si no se pudo cargar la imagen, mostrar texto
                self.screen.fill((0, 0, 0))
                title_font = pygame.font.Font(None, 72)
                subtitle_font = pygame.font.Font(None, 36)
                title_text = title_font.render("DUNGEON GAME", True, (255, 215, 0))
                subtitle_text = subtitle_font.render("Press any key to start", True, (200, 200, 200))
                self.screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, self.height // 2 - 50))
                self.screen.blit(subtitle_text, (self.width // 2 - subtitle_text.get_width() // 2, self.height // 2 + 30))
            pygame.display.flip()
            return
        
        # Rellenar fondo negro (para que coincida con celdas EMPTY/no visitadas)
        self.screen.fill((0, 0, 0))
        
        # Primero: actualizar el viewport (mueve la cámara)
        offset_row_float, offset_col_float = self.get_view_offset()
        
        # Calcular offset de píxeles para scroll suave
        offset_row_int = int(offset_row_float)
        offset_col_int = int(offset_col_float)
        pixel_offset_y = int((offset_row_float - offset_row_int) * self.cell_size)
        pixel_offset_x = int((offset_col_float - offset_col_int) * self.cell_size)
        
        # Dibujar una celda extra en cada dirección para scroll suave
        for row in range(-1, self.view_size + 1):
            for col in range(-1, self.view_size + 1):
                board_row = offset_row_int + row
                board_col = offset_col_int + col
                if 0 <= board_row < self.size and 0 <= board_col < self.size:
                    # Ajustar la posición de dibujo con el offset de píxeles
                    view_row = row
                    view_col = col
                    self.draw_cell(board_row, board_col, view_row, view_col, pixel_offset_x, pixel_offset_y)

        # Dibujar aberturas (pasajes) conectadas en negro entre celdas.
        # Se hace después de dibujar todas las celdas para sobreescribir bordes.
        self.draw_openings(offset_row_int, offset_col_int, pixel_offset_x, pixel_offset_y)

        # Tercero: dibujar monigote en la posición actual (después del viewport)
        self.draw_player(offset_row_float, offset_col_float)
        
        # Debug: mostrar información de navegación solo si está activado
        if self.debug_mode:
            self.draw_debug_info()
        
        # Dibujar subtítulos si están activos
        self.draw_subtitles()
        
        # Dibujar imagen del pensamiento activo (si hay una)
        if self.thought_image_shown and self.thought_image:
            # Centrar la imagen en la pantalla
            image_x = (self.width - self.thought_image.get_width()) // 2
            image_y = (self.height - self.thought_image.get_height()) // 2
            self.screen.blit(self.thought_image, (image_x, image_y))
            
            # Si es la imagen de salida (losa), verificar si expiró para activar ráfaga
            if self.thought_image == self.exit_image:
                current_time = pygame.time.get_ticks()
                if current_time - self.thought_image_start_time >= 12000:
                    # Activar pensamiento de ráfaga que apagará las antorchas
                    if not self.rafaga_thought_triggered and self.rafaga_sound:
                        # Parar la música de Cthulhu
                        self.music_channel.stop()
                        
                        # Activar pensamiento de ráfaga (bloquea movimiento)
                        self.trigger_thought(
                            sounds=[(self.rafaga_sound, 0)],  # Duración automática
                            blocks_movement=True
                        )
                        self.rafaga_thought_triggered = True
                        self.torches_flickering = True
                        self.flicker_start_time = current_time
                        # Obtener la duración real del sonido de ráfaga y dividir por 2
                        self.flicker_duration = int(self.rafaga_sound.get_length() * 1000 / 2)  # Mitad de la duración en ms
                        print(f"[DEBUG] Ráfaga activada - antorchas parpadeando por {self.flicker_duration}ms")
                        
                        # Iniciar fade-in del viento
                        self.wind_fade_start_time = pygame.time.get_ticks()
                        self.wind_fading_in = True
        
        # Mostrar diálogo de confirmación de salida si está activo (siempre encima de todo)
        if self.asking_exit_confirmation:
            self.draw_exit_confirmation()
        
        # Mostrar diálogo de confirmación de menú principal si está activo
        if self.asking_main_menu_confirmation:
            self.draw_main_menu_confirmation()
        
        pygame.display.flip()
    
    def draw_player(self, offset_row_float, offset_col_float):
        """Dibuja un monigote en la posición actual del jugador (con interpolación si está animando)."""
        # Si está animando, interpolar entre from_pos y to_pos
        if self.player_animating:
            t_now = pygame.time.get_ticks()
            elapsed = t_now - self.player_anim_start_time
            t = min(1.0, elapsed / self.player_anim_duration)
            
            # Interpolación lineal
            from_row, from_col = self.player_anim_from_pos
            to_row, to_col = self.player_anim_to_pos
            player_row = from_row + (to_row - from_row) * t
            player_col = from_col + (to_col - from_col) * t
            
            # Si terminó la animación, fijar posición y desactivar
            if t >= 1.0:
                self.player_animating = False
                player_row, player_col = self.current_position
        else:
            player_row, player_col = self.current_position
        
        # Coordenadas relativas a la vista (con scroll suave)
        view_row = player_row - offset_row_float
        view_col = player_col - offset_col_float
        
        # Dibujar siempre (incluso si está entre celdas durante la animación)
        x = view_col * self.cell_size
        y = view_row * self.cell_size

        center_x = x + self.cell_size // 2
        center_y = y + self.cell_size // 2

        # Dibujar un sprite de guerrero procedimental escalable
        sprite_size = int(self.cell_size * 0.6)
        self.draw_warrior_sprite(center_x, center_y, sprite_size)
    
    def draw_debug_info(self):
        """Muestra información de debug para ayudar a encontrar la salida."""
        current_row, current_col = self.current_position
        exit_row, exit_col = self.exit_position
        
        # Calcular distancia Manhattan
        distance = abs(exit_row - current_row) + abs(exit_col - current_col)
        
        # Calcular dirección aproximada
        delta_row = exit_row - current_row
        delta_col = exit_col - current_col
        
        direction_text = ""
        if abs(delta_row) > abs(delta_col):
            direction_text = "Sur" if delta_row > 0 else "Norte"
        else:
            direction_text = "Este" if delta_col > 0 else "Oeste"
        
        # Verificar si estás en el camino principal
        on_path = self.current_position in self.main_path
        
        # Crear textos
        texts = [
            f"Posición: ({current_row}, {current_col})",
            f"Salida: ({exit_row}, {exit_col})",
            f"Distancia: {distance} celdas",
            f"Dirección: {direction_text}",
            f"En camino: {'SÍ' if on_path else 'NO'}"
        ]
        
        # Dibujar fondo semi-transparente
        info_height = len(texts) * 25 + 20
        info_surface = pygame.Surface((250, info_height))
        info_surface.set_alpha(200)
        info_surface.fill((0, 0, 0))
        self.screen.blit(info_surface, (10, 10))
        
        # Dibujar textos
        y_offset = 20
        for text in texts:
            color = (0, 255, 0) if "En camino: SÍ" in text else (255, 255, 255)
            text_surface = self.font.render(text, True, color)
            self.screen.blit(text_surface, (20, y_offset))
            y_offset += 25
    
    def update_fade(self):
        """Actualiza el fade de música si está activo."""
        if REFACTORED_MODULES:
            self.audio.update_fades()
            return
        
        # Versión legacy
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.fade_start_time
        
        if self.fading_out:
            if elapsed >= self.fade_duration:
                # Fade out completado
                self.music_channel.set_volume(0.0)
                self.fading_out = False
                
                # Cargar la siguiente música si hay una pendiente
                if self.pending_music_load:
                    music_name, loop = self.pending_music_load
                    if music_name in self.music_sounds:
                        self.music_channel.stop()
                        self.current_music = music_name
                        self.music_channel.play(self.music_sounds[music_name], loops=-1 if loop else 0)
                        self.start_fade_in(self.music_volume)
                    self.pending_music_load = None
            else:
                # Interpolar volumen
                t = elapsed / self.fade_duration
                volume = self.fade_from_volume + (self.fade_to_volume - self.fade_from_volume) * t
                self.music_channel.set_volume(volume)
        
        elif self.fading_in:
            if elapsed >= self.fade_duration:
                # Fade in completado
                self.music_channel.set_volume(self.fade_to_volume)
                self.fading_in = False
            else:
                # Interpolar volumen
                t = elapsed / self.fade_duration
                volume = self.fade_from_volume + (self.fade_to_volume - self.fade_from_volume) * t
                self.music_channel.set_volume(volume)
    
    def start_fade_out(self, next_music_name=None, loop=False):
        """Inicia un fade out de la música actual."""
        self.fading_out = True
        self.fade_start_time = pygame.time.get_ticks()
        self.fade_from_volume = self.music_channel.get_volume()
        self.fade_to_volume = 0.0
        self.pending_music_load = (next_music_name, loop)
    
    def start_fade_in(self, target_volume=0.5):
        """Inicia un fade in de la música actual."""
        self.fading_in = True
        self.fade_start_time = pygame.time.get_ticks()
        self.fade_from_volume = 0.0
        self.fade_to_volume = target_volume
        self.music_channel.set_volume(0.0)
    
    def draw_subtitles(self):
        """Dibuja los subtítulos en la parte inferior de la pantalla."""
        if not self.showing_subtitles:
            return
        
        # Los threads manejan automáticamente la expiración de subtítulos
        # Solo dibujamos lo que el AudioManager nos indica
        
        # Dividir el texto en líneas que quepan en el ancho del juego
        font = pygame.font.Font(None, 32)
        max_width = self.width - 40  # Margen de 20px a cada lado
        words = self.subtitle_text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = font.render(test_line, True, (255, 255, 255))
            
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calcular altura necesaria para todas las líneas
        line_height = 36
        subtitle_height = max(80, len(lines) * line_height + 20)
        
        # Crear fondo semi-transparente para los subtítulos
        subtitle_bg = pygame.Surface((self.width, subtitle_height))
        subtitle_bg.set_alpha(160)
        subtitle_bg.fill((0, 0, 0))
        self.screen.blit(subtitle_bg, (0, self.height - subtitle_height))
        
        # Renderizar cada línea centrada
        start_y = self.height - subtitle_height + 10
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(self.width // 2, start_y + i * line_height + line_height // 2))
            self.screen.blit(text_surface, text_rect)
    
    def trigger_thought(self, sounds=None, images=None, subtitles=None, blocks_movement=True):
        """Inicia un pensamiento con arrays de sonidos, imágenes y subtítulos.
        
        Args:
            sounds: Lista de tuplas (sound_obj, duración_ms) donde 0 = duración auto del audio
            images: Lista de tuplas (image_surface, duración_ms)
            subtitles: Lista de tuplas (texto, duración_ms)
            blocks_movement: Si True, bloquea el movimiento durante el pensamiento
        """
        if REFACTORED_MODULES:
            # Delegar al AudioManager que usa threading
            self.audio.trigger_thought(
                sounds=sounds,
                images=images,
                subtitles=subtitles,
                blocks_movement=blocks_movement
            )
            return
        
        # Versión legacy
        # Si hay un pensamiento activo, detenerlo antes de comenzar el nuevo
        if self.thought_active:
            # Detener el sonido anterior si existe
            if self.thought_sound:
                self.thought_sound.stop()
            
            # Limpiar el estado anterior (pero mantener thought_active si blocks_movement)
            self.thought_sound = None
            self.thought_subtitles = []
            self.thought_current_subtitle_index = 0
            self.showing_subtitles = False
        
        # Iniciar el nuevo pensamiento
        self.thought_active = True
        self.thought_blocks_movement = blocks_movement  # Guardar si este pensamiento bloquea movimiento
        self.thought_sound = sound
        self.thought_subtitles = subtitles
        self.thought_current_subtitle_index = 0
        self.thought_subtitle_start_time = pygame.time.get_ticks()
        
        # Reproducir el sonido
        if sound:
            sound.play()
        
        # Activar el primer subtítulo
        if subtitles:
            self.showing_subtitles = True
            self.subtitle_text = subtitles[0][0]
            self.subtitle_start_time = pygame.time.get_ticks()
            self.subtitle_duration = subtitles[0][1]
    
    def update_thought(self):
        """Actualiza el estado del pensamiento activo."""
        if REFACTORED_MODULES:
            # Guardar estado anterior de thought_active
            was_active = self.thought_active
            
            self.audio.update_thoughts()
            # Sincronizar estado de subtítulos e imágenes (el thread maneja el timing)
            self.showing_subtitles = self.audio.showing_subtitles
            self.subtitle_text = self.audio.subtitle_text
            self.thought_active = self.audio.thought_active
            self.thought_blocks_movement = self.audio.thought_blocks_movement
            # Sincronizar imagen del pensamiento (sin sobrescribir exit_image)
            self.thought_image_shown = self.audio.showing_image
            if self.audio.showing_image:
                self.thought_image = self.audio.image_surface
                self.thought_image_start_time = self.audio.image_start_time
            else:
                self.thought_image = None
            
            # Si el pensamiento de intro acaba de terminar, marcar flag
            if was_active and not self.thought_active and self.intro_thought_triggered and not self.intro_thought_finished:
                self.intro_thought_finished = True
                print("[DEBUG] Pensamiento de intro terminado - antorchas ahora disponibles")
            
            return
        
        # Versión legacy (sin cambios)
        if not self.thought_active:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Verificar si el subtítulo actual ha terminado
        if current_time - self.subtitle_start_time > self.subtitle_duration:
            self.thought_current_subtitle_index += 1
            
            # Verificar si hay más subtítulos
            if self.thought_current_subtitle_index < len(self.thought_subtitles):
                # Activar el siguiente subtítulo inmediatamente
                subtitle_data = self.thought_subtitles[self.thought_current_subtitle_index]
                self.showing_subtitles = True
                self.subtitle_text = subtitle_data[0]
                self.subtitle_start_time = current_time
                self.subtitle_duration = subtitle_data[1]
            else:
                # No hay más subtítulos, terminar el pensamiento
                self.showing_subtitles = False
                self.thought_active = False
                self.thought_blocks_movement = False
                self.thought_sound = None
                self.thought_subtitles = []
                self.thought_current_subtitle_index = 0
    
    def draw_exit_confirmation(self):
        """Dibuja el diálogo de confirmación de salida."""
        # Fondo oscuro semi-transparente
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Caja de diálogo
        dialog_width = 400
        dialog_height = 150
        dialog_x = (self.width - dialog_width) // 2
        dialog_y = (self.height - dialog_height) // 2
        
        # Fondo de la caja
        pygame.draw.rect(self.screen, (40, 40, 40), (dialog_x, dialog_y, dialog_width, dialog_height))
        # Borde
        pygame.draw.rect(self.screen, (200, 200, 200), (dialog_x, dialog_y, dialog_width, dialog_height), 3)
        
        # Texto
        title_font = pygame.font.Font(None, 48)
        subtitle_font = pygame.font.Font(None, 32)
        
        title_text = title_font.render("¿Salir del juego?", True, (255, 255, 255))
        subtitle_text = subtitle_font.render("S = Sí  /  N = No", True, (200, 200, 200))
        
        title_x = dialog_x + (dialog_width - title_text.get_width()) // 2
        title_y = dialog_y + 30
        subtitle_x = dialog_x + (dialog_width - subtitle_text.get_width()) // 2
        subtitle_y = dialog_y + 90
        
        self.screen.blit(title_text, (title_x, title_y))
        self.screen.blit(subtitle_text, (subtitle_x, subtitle_y))

    def draw_main_menu_confirmation(self):
        """Dibuja el diálogo de confirmación para volver al menú principal."""
        # Fondo oscuro semi-transparente
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Caja de diálogo
        dialog_width = 450
        dialog_height = 150
        dialog_x = (self.width - dialog_width) // 2
        dialog_y = (self.height - dialog_height) // 2
        
        # Fondo de la caja
        pygame.draw.rect(self.screen, (40, 40, 40), (dialog_x, dialog_y, dialog_width, dialog_height))
        # Borde
        pygame.draw.rect(self.screen, (200, 200, 200), (dialog_x, dialog_y, dialog_width, dialog_height), 3)
        
        # Texto
        title_font = pygame.font.Font(None, 40)
        subtitle_font = pygame.font.Font(None, 32)
        
        title_text = title_font.render("¿Volver al menú principal?", True, (255, 255, 255))
        subtitle_text = subtitle_font.render("S = Sí  /  N = No", True, (200, 200, 200))
        
        title_x = dialog_x + (dialog_width - title_text.get_width()) // 2
        title_y = dialog_y + 30
        subtitle_x = dialog_x + (dialog_width - subtitle_text.get_width()) // 2
        subtitle_y = dialog_y + 90
        
        self.screen.blit(title_text, (title_x, title_y))
        self.screen.blit(subtitle_text, (subtitle_x, subtitle_y))

    def draw_warrior_sprite(self, cx: int, cy: int, size: int):
        """Dibuja un sprite de guerrero sencillo (procedimental) centrado en (cx, cy).

        El sprite es vectorial (formas) y escala con `size`.
        """
        # Sizing
        s = max(8, int(size))
        head_r = max(4, s // 6)
        body_h = max(8, s // 2)
        body_w = max(6, s // 3)

        # Colores desde la paleta configurable
        armor_col = self.player_palette.get("armor", (90, 90, 90))
        trim_col = self.player_palette.get("trim", (140, 140, 140))
        skin_col = self.player_palette.get("skin", (200, 170, 140))
        shield_col = self.player_palette.get("shield", (70, 70, 70))
        shield_trim = self.player_palette.get("shield_trim", (140, 120, 80))
        sword_handle_col = self.player_palette.get("sword_handle", (180, 140, 80))
        sword_blade_col = self.player_palette.get("sword_blade", (200, 200, 200))

        # Animación de introducción
        intro_offset_y = 0
        head_turn_offset = 0
        
        if self.intro_anim_active:
            t_now = pygame.time.get_ticks()
            elapsed = t_now - self.intro_anim_start_time
            
            # Stage 0: Caída (0-800ms)
            if elapsed < 800:
                fall_progress = elapsed / 800.0
                intro_offset_y = int(-self.cell_size * (1.0 - fall_progress))
            # Stage 1: Mirar izquierda (800-2800ms) - 2 segundos
            elif elapsed < 2800:
                head_turn_offset = -head_r // 2
            # Stage 2: Mirar derecha (2800-4800ms) - 2 segundos
            elif elapsed < 4800:
                head_turn_offset = head_r // 2
            # Stage 3: Sacar armas (4800-5300ms)
            elif elapsed < 5300:
                self.intro_show_weapons = True
            # Stage 4: Completo
            else:
                self.intro_anim_active = False
                self.intro_show_weapons = True
                
                # Activar pensamiento de intro cuando el personaje entra en el calabozo
                if not self.intro_thought_triggered and self.intro_sound:
                    # Duración de intro.ogg: 0 = auto (duración del audio)
                    self.trigger_thought(
                        sounds=[(self.intro_sound, 0)],
                        subtitles=[("Usa A, W, S y D para moverte.", 4000),
                         ("Haz zoom con Z y X.", 4000),
                         ("Explora la mazmorra... encuentra la salida...", 6000),
                         ("Ten cuidado con lo que acecha en las sombras.", 6000),
                         ("¡Buena suerte, valiente guerrero!", 14000),  # Resto del audio
                         ],
                        blocks_movement=False  # La intro no bloquea el movimiento
                    )
                    self.intro_thought_triggered = True
        
        cy += intro_offset_y
        
        # Sombras / base
        shadow_w = int(body_w * 1.2)
        pygame.draw.ellipse(self.screen, (10, 10, 10), (cx - shadow_w//2, cy + body_h//2, shadow_w, max(4, s//6)))

        # Animación simple basada en tiempo (oscilación seno) — solo cuando se está moviendo
        t = pygame.time.get_ticks()
        walking = t < self.player_walk_until
        if walking:
            phase = math.sin(t * self.player_anim_speed * 2 * math.pi) * self.player_anim_amp
        else:
            phase = 0.0

        # Piernas (oscilan)
        leg_h = max(6, s // 6)
        left_leg_offset = int(phase * leg_h * 0.5)
        right_leg_offset = int(-phase * leg_h * 0.5)
        lx = cx - body_w//4
        rx = cx + body_w//4
        leg_y0 = cy + body_h//2
        pygame.draw.line(self.screen, (60, 60, 60), (lx, leg_y0), (lx, leg_y0 + leg_h + left_leg_offset), 3)
        pygame.draw.line(self.screen, (60, 60, 60), (rx, leg_y0), (rx, leg_y0 + leg_h + right_leg_offset), 3)

        # Cuerpo (armadura)
        body_rect = pygame.Rect(cx - body_w//2, cy - body_h//4, body_w, body_h)
        pygame.draw.rect(self.screen, armor_col, body_rect)
        pygame.draw.rect(self.screen, trim_col, body_rect, 2)

        # Brazos/guanteletes (se mueven ligeramente)
        arm_w = max(4, s // 10)
        arm_y = cy - body_h//8 + int(-phase * (body_h//8))
        pygame.draw.rect(self.screen, armor_col, (cx - body_w//2 - arm_w, arm_y, arm_w, body_h//3))
        pygame.draw.rect(self.screen, armor_col, (cx + body_w//2, arm_y, arm_w, body_h//3))
        pygame.draw.rect(self.screen, trim_col, (cx - body_w//2 - arm_w, arm_y, arm_w, body_h//3), 1)
        pygame.draw.rect(self.screen, trim_col, (cx + body_w//2, arm_y, arm_w, body_h//3), 1)

        # Escudo y espada solo se muestran después de la intro
        if self.intro_show_weapons:
            # Escudo (izquierda) - se desplaza ligeramente con la fase
            shield_r = max(8, s // 6)
            shield_x = cx - body_w//2 - arm_w - shield_r//2 + int(-phase * 3)
            shield_y = cy + int(phase * 2)
            pygame.draw.circle(self.screen, shield_col, (shield_x, shield_y), shield_r)
            pygame.draw.circle(self.screen, shield_trim, (shield_x, shield_y), shield_r, 2)

            # Espada (derecha) - mango y hoja simple, se balancea con la fase
            sword_h = max(12, s // 3)
            sword_w = max(3, s // 30)
            sword_x = cx + body_w//2 + arm_w + 2 + int(phase * 2)
            sword_y1 = cy - body_h//8 + int(-phase * 2)
            sword_y2 = sword_y1 - sword_h + int(phase * 4)
            pygame.draw.line(self.screen, sword_handle_col, (sword_x, sword_y1), (sword_x, sword_y1 + 6), sword_w + 2)
            pygame.draw.line(self.screen, sword_blade_col, (sword_x, sword_y1), (sword_x, sword_y2), sword_w)

        # Cabeza y casco
        head_x = cx + head_turn_offset
        head_y = cy - body_h//2 + head_r
        # Cara
        pygame.draw.circle(self.screen, skin_col, (head_x, head_y), head_r)
        # Casco
        helmet_h = max(6, head_r + 2)
        helmet_rect = pygame.Rect(head_x - head_r - 2, head_y - helmet_h, head_r*2 + 4, helmet_h)
        pygame.draw.rect(self.screen, trim_col, helmet_rect)
        pygame.draw.rect(self.screen, (160, 160, 160), helmet_rect, 1)
        # Visor (línea)
        pygame.draw.line(self.screen, (30, 30, 30), (head_x - head_r//1, head_y - 1), (head_x + head_r//1, head_y - 1), 2)
        # Ojos
        eye_y = head_y - 1
        pygame.draw.circle(self.screen, (10, 10, 10), (head_x - head_r//2, eye_y), max(1, head_r//4))
        pygame.draw.circle(self.screen, (10, 10, 10), (head_x + head_r//2, eye_y), max(1, head_r//4))
    
    def draw_cell(self, board_row, board_col, view_row, view_col, pixel_offset_x=0, pixel_offset_y=0):
        """Dibuja una celda del tablero en las coordenadas de la vista."""
        cell = self.board[board_row][board_col]
        x = view_col * self.cell_size - pixel_offset_x
        y = view_row * self.cell_size - pixel_offset_y
        
        # Verificar si esta celda debe ser revelada por show_path
        should_reveal_for_path = False
        if self.show_path and (board_row, board_col) in self.main_path:
            should_reveal_for_path = True
        elif self.show_path:
            # Verificar si es adyacente a alguna celda del camino
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                adj_row, adj_col = board_row + dr, board_col + dc
                if (adj_row, adj_col) in self.main_path:
                    # Verificar si hay una salida desde la celda del camino hacia esta celda
                    adj_cell = self.board[adj_row][adj_col]
                    # Determinar la dirección desde la celda adyacente hacia esta celda
                    if dr == -1:  # vecino arriba mira hacia abajo (S)
                        if Direction.S in adj_cell.exits:
                            should_reveal_for_path = True
                            break
                    elif dr == 1:  # vecino abajo mira hacia arriba (N)
                        if Direction.N in adj_cell.exits:
                            should_reveal_for_path = True
                            break
                    elif dc == -1:  # vecino izquierda mira hacia derecha (E)
                        if Direction.E in adj_cell.exits:
                            should_reveal_for_path = True
                            break
                    elif dc == 1:  # vecino derecha mira hacia izquierda (O)
                        if Direction.O in adj_cell.exits:
                            should_reveal_for_path = True
                            break
        
        # Si la celda no ha sido visitada, dibujar niebla negra
        # EXCEPCIÓN: Si show_path está activo y debe revelarse, mostrarla
        if (board_row, board_col) not in self.visited_cells:
            if should_reveal_for_path:
                # Mostrar celda revelada por el camino
                pass  # Continuar con el renderizado normal pero con overlay
            else:
                pygame.draw.rect(self.screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size))
                return
        
        # Color / textura based on type
        if cell.cell_type == CellType.EMPTY:
            # Pared negra (EMPTY debe verse negra)
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size))
            # Borde visible en gris para las celdas vacías
            pygame.draw.rect(self.screen, (90, 90, 90), (x, y, self.cell_size, self.cell_size), 3)
        elif cell.cell_type == CellType.INICIO:
            # Calcular número de antorchas para iluminación
            torch_count = self.count_torches(board_row, board_col, cell)
            
            # En el inicio, el brillo base es bajo (oscuro) independientemente de la distancia
            base_brightness = 10
            torch_brightness = min(130, torch_count * 31)
            brightness = max(0, base_brightness + torch_brightness)
            floor_color = (brightness, brightness, brightness)
            
            # Calcular factor de brillo para aplicar a todos los elementos (0.0 a 1.0)
            # En inicio siempre es el mismo valor base
            brightness_factor = brightness / 255.0
            
            # Inicio es como una habitación: fondo con iluminación
            pygame.draw.rect(self.screen, floor_color, (x, y, self.cell_size, self.cell_size))
            # Marco del inicio en gris oscurecido
            marco_color = tuple(int(120 * brightness_factor) for _ in range(3))
            pygame.draw.rect(self.screen, marco_color, (x, y, self.cell_size, self.cell_size), 3)
            # Dibujar textura de piedra en las paredes
            self.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor)
        elif cell.cell_type == CellType.PASILLO:
            # Calcular número de antorchas para iluminación
            torch_count = self.count_torches(board_row, board_col, cell)
            
            # Calcular oscurecimiento basado en distancia desde la entrada
            start_row, start_col = self.start_position
            exit_row, exit_col = self.exit_position
            distance_from_start = abs(start_row - board_row) + abs(start_col - board_col)
            total_distance = abs(exit_row - start_row) + abs(exit_col - start_col)
            
            if total_distance > 0:
                # progress: 0.0 en entrada, 1.0 en salida
                progress = distance_from_start / total_distance
            else:
                progress = 0.5
            
            # Base de luz: 20 en entrada, 0 en salida
            base_brightness = int(20 * (1.0 - progress))
            torch_brightness = min(130, torch_count * 31)
            brightness = max(0, base_brightness + torch_brightness)
            floor_color = (brightness, brightness, brightness)
            
            # Calcular factor de brillo para aplicar a elementos (0.0 a 1.0)
            brightness_factor = brightness / 255.0
            
            # Suelo del pasillo: el área entre las líneas y el centro con iluminación
            pygame.draw.rect(self.screen, floor_color, (x, y, self.cell_size, self.cell_size))
            # Marco del pasillo ligeramente grueso oscurecido
            marco_color = tuple(int(120 * brightness_factor) for _ in range(3))
            pygame.draw.rect(self.screen, marco_color, (x, y, self.cell_size, self.cell_size), 3)
            # Dibujar textura de piedra solo en las 'paredes' dentro de la celda
            self.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor)
            # Las líneas se dibujan más adelante (después de las piedras, antes de la sangre)
        elif cell.cell_type == CellType.HABITACION:
            # Calcular número de antorchas para iluminación
            torch_count = self.count_torches(board_row, board_col, cell)
            
            # Calcular oscurecimiento basado en distancia desde la entrada
            start_row, start_col = self.start_position
            exit_row, exit_col = self.exit_position
            distance_from_start = abs(start_row - board_row) + abs(start_col - board_col)
            total_distance = abs(exit_row - start_row) + abs(exit_col - start_col)
            
            if total_distance > 0:
                # progress: 0.0 en entrada, 1.0 en salida
                progress = distance_from_start / total_distance
            else:
                progress = 0.5
            
            # Base de luz: 20 en entrada, 0 en salida
            base_brightness = int(20 * (1.0 - progress))
            torch_brightness = min(130, torch_count * 31)
            brightness = max(0, base_brightness + torch_brightness)
            floor_color = (brightness, brightness, brightness)
            
            # Calcular factor de brillo para aplicar a todos los elementos (0.0 a 1.0)
            brightness_factor = brightness / 255.0
            
            # Habitación como mazmorra: fondo con iluminación
            pygame.draw.rect(self.screen, floor_color, (x, y, self.cell_size, self.cell_size))
            # Marco de la habitación en gris oscurecido
            marco_color = tuple(int(120 * brightness_factor) for _ in range(3))
            pygame.draw.rect(self.screen, marco_color, (x, y, self.cell_size, self.cell_size), 3)
            # Dibujar textura de piedra en las paredes
            self.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor)
            # Las líneas se dibujan más adelante (después de las piedras, antes de la sangre)
        elif cell.cell_type == CellType.SALIDA:
            # Celda de salida: se dibuja como habitación normal
            torch_count = self.count_torches(board_row, board_col, cell)
            
            # En la salida, sin antorchas sería completamente oscuro (pitch black)
            # brightness base = 0 (negro total)
            base_brightness = 0
            torch_brightness = min(130, torch_count * 31)
            brightness = max(0, base_brightness + torch_brightness)
            room_color = (brightness, brightness, brightness)
            
            # Calcular factor de brillo para aplicar a todos los elementos (0.0 a 1.0)
            brightness_factor = brightness / 255.0
            
            pygame.draw.rect(self.screen, room_color, (x, y, self.cell_size, self.cell_size))
            # Dibujar piedras en las paredes
            self.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor)
        
        # Marcar celdas del camino principal si show_path está activo
        if self.show_path and (board_row, board_col) in self.main_path:
            # Overlay azul semitransparente sobre la celda
            overlay = pygame.Surface((self.cell_size, self.cell_size))
            overlay.set_alpha(80)
            overlay.fill((0, 100, 255))
            self.screen.blit(overlay, (x, y))
        
        # Calcular brightness_factor para las líneas de túneles y salidas
        # (se aplica con 50% de intensidad respecto al resto)
        lines_brightness_factor = 1.0
        if cell.cell_type in [CellType.PASILLO, CellType.HABITACION, CellType.SALIDA]:
            # Calcular oscurecimiento basado en distancia desde la entrada
            start_row, start_col = self.start_position
            exit_row, exit_col = self.exit_position
            distance_from_start = abs(start_row - board_row) + abs(start_col - board_col)
            total_distance = abs(exit_row - start_row) + abs(exit_col - start_col)
            
            if total_distance > 0:
                progress = distance_from_start / total_distance
            else:
                progress = 0.5
            
            # Calcular brillo base sin antorchas
            base_brightness = int(50 * (1.0 - progress))
            # Para las líneas, aplicar 100% del oscurecimiento si está activado, o 0% si está desactivado
            if self.lines_darkening_enabled:
                lines_brightness_factor = base_brightness / 255.0
            else:
                lines_brightness_factor = 1.0  # Sin oscurecimiento
        elif cell.cell_type == CellType.INICIO:
            # En inicio, usar el mismo brillo base que tendría si estuviera en el camino (50)
            # porque está en la posición más alejada de la salida
            if self.lines_darkening_enabled:
                base_brightness = 50
                lines_brightness_factor = base_brightness / 255.0
            else:
                lines_brightness_factor = 1.0  # Sin oscurecimiento
        
        # Para pasillos, habitaciones, inicio y salida: dibujar camino desde el centro hacia las salidas
        if cell.cell_type in [CellType.PASILLO, CellType.HABITACION, CellType.INICIO, CellType.SALIDA]:
            # Para habitaciones e inicio, la zona central es mucho más ancha
            if cell.cell_type in [CellType.HABITACION, CellType.INICIO]:
                center_x_L = x + 0.15*self.cell_size
                center_x_R = x + 0.85*self.cell_size
                center_y_D = y + 0.15*self.cell_size
                center_y_U = y + 0.85*self.cell_size
                mid_x_L = x + 0.15*self.cell_size
                mid_x_R = x + 0.85*self.cell_size
                mid_y_D = y + 0.15*self.cell_size
                mid_y_U = y + 0.85*self.cell_size
            else:  # PASILLO
                center_x_L = x + 0.8*self.cell_size // 2
                center_x_R = x + 1.2*self.cell_size // 2
                center_y_D = y + 0.8*self.cell_size // 2
                center_y_U = y + 1.2*self.cell_size // 2
                mid_x_L = x + 0.8*self.cell_size // 2
                mid_x_R = x + 1.2*self.cell_size // 2
                mid_y_D = y + 0.8*self.cell_size // 2
                mid_y_U = y + 1.2*self.cell_size // 2
            
            # Las líneas internas oscurecidas con 50% de intensidad
            base_line_color = 150
            darkened_value = int(base_line_color * lines_brightness_factor)
            inner_color = (darkened_value, darkened_value, darkened_value)
            
            # North
            if Direction.N in cell.exits:
                if self.lines_darkening_enabled:
                    self.draw_broken_line(inner_color, (mid_x_L, center_y_D), (mid_x_L, y + 0.1*self.cell_size), 3, board_row, board_col, 1)
                    self.draw_broken_line(inner_color, (mid_x_R, center_y_D), (mid_x_R, y + 0.1*self.cell_size), 3, board_row, board_col, 2)
                else:
                    pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_D), (mid_x_L, y + 0.1*self.cell_size), 3)
                    pygame.draw.line(self.screen, inner_color, (mid_x_R, center_y_D), (mid_x_R, y + 0.1*self.cell_size), 3)
            else:
                # Cerrar el norte si no hay salida (siempre gris oscuro)
                if self.lines_darkening_enabled:
                    self.draw_broken_line(inner_color, (mid_x_L, center_y_D), (mid_x_R, center_y_D), 3, board_row, board_col, 3)
                else:
                    pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_D), (mid_x_R, center_y_D), 3)
            
            # South
            if Direction.S in cell.exits:
                if self.lines_darkening_enabled:
                    self.draw_broken_line(inner_color, (mid_x_L, center_y_U), (mid_x_L, y + 0.9*self.cell_size), 3, board_row, board_col, 4)
                    self.draw_broken_line(inner_color, (mid_x_R, center_y_U), (mid_x_R, y + 0.9*self.cell_size), 3, board_row, board_col, 5)
                else:
                    pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_U), (mid_x_L, y + 0.9*self.cell_size), 3)
                    pygame.draw.line(self.screen, inner_color, (mid_x_R, center_y_U), (mid_x_R, y + 0.9*self.cell_size), 3)
            else:
                # Cerrar el sur si no hay salida (siempre gris oscuro)
                if self.lines_darkening_enabled:
                    self.draw_broken_line(inner_color, (mid_x_L, center_y_U), (mid_x_R, center_y_U), 3, board_row, board_col, 6)
                else:
                    pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_U), (mid_x_R, center_y_U), 3)
            
            # East
            if Direction.E in cell.exits:
                if self.lines_darkening_enabled:
                    self.draw_broken_line(inner_color, (center_x_R, mid_y_D), (x + 0.9*self.cell_size, mid_y_D), 3, board_row, board_col, 7)
                    self.draw_broken_line(inner_color, (center_x_R, mid_y_U), (x + 0.9*self.cell_size, mid_y_U), 3, board_row, board_col, 8)
                else:
                    pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_D), (x + 0.9*self.cell_size, mid_y_D), 3)
                    pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_U), (x + 0.9*self.cell_size, mid_y_U), 3)
            else:
                # Cerrar el este si no hay salida (siempre gris oscuro)
                if self.lines_darkening_enabled:
                    self.draw_broken_line(inner_color, (center_x_R, mid_y_D), (center_x_R, mid_y_U), 3, board_row, board_col, 9)
                else:
                    pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_D), (center_x_R, mid_y_U), 3)
            
            # West
            if Direction.O in cell.exits:
                if self.lines_darkening_enabled:
                    self.draw_broken_line(inner_color, (center_x_L, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 3, board_row, board_col, 10)
                    self.draw_broken_line(inner_color, (center_x_L, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 3, board_row, board_col, 11)
                else:
                    pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 3)
                    pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 3)
            else:
                # Cerrar el oeste si no hay salida (siempre gris oscuro)
                if self.lines_darkening_enabled:
                    self.draw_broken_line(inner_color, (center_x_L, mid_y_D), (center_x_L, mid_y_U), 3, board_row, board_col, 12)
                else:
                    pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_D), (center_x_L, mid_y_U), 3)
        
        # Draw exits
        if cell.cell_type != CellType.EMPTY:
            self.draw_exits(board_row, board_col, x, y, cell.exits, cell.cell_type, lines_brightness_factor)
        
        # Dibujar manchas de sangre después de las líneas
        if cell.cell_type in [CellType.PASILLO, CellType.HABITACION]:
            if REFACTORED_MODULES:
                self.decorations.draw_blood_stains(board_row, board_col, x, y, brightness_factor, self.exit_position)
            else:
                self.draw_blood_stains(board_row, board_col, x, y, brightness_factor)
        elif cell.cell_type == CellType.SALIDA:
            if REFACTORED_MODULES:
                self.decorations.draw_blood_stains(board_row, board_col, x, y, brightness_factor, self.exit_position)
            else:
                self.draw_blood_stains(board_row, board_col, x, y, brightness_factor)
        
        # Dibujar fuente y escaleras después de la sangre
        if cell.cell_type == CellType.INICIO:
            if REFACTORED_MODULES:
                self.decorations.draw_fountain(x, y)
            else:
                self.draw_fountain(x, y)
        elif cell.cell_type == CellType.SALIDA:
            if REFACTORED_MODULES:
                self.decorations.draw_spiral_stairs(x, y)
            else:
                self.draw_spiral_stairs(x, y)
        
        # Dibujar antorchas al final (encima de todo)
        if cell.cell_type in [CellType.INICIO, CellType.PASILLO, CellType.HABITACION, CellType.SALIDA]:
            if REFACTORED_MODULES:
                num_torches = self.count_torches(board_row, board_col, cell)
                self.decorations.draw_torches(board_row, board_col, x, y, cell, num_torches)
            else:
                self.draw_torches(board_row, board_col, x, y, cell)
    
    def draw_exits(self, row, col, x, y, exits, cell_type, brightness_factor: float = 1.0):
        """Dibuja las salidas de una celda.
        
        Args:
            brightness_factor: Factor de brillo (0.0 a 1.0) para oscurecer las líneas de salida
        """
        exit_size = 5
        # Las coordenadas son iguales para PASILLO, HABITACION e INICIO
        mid_x_L = x + 0.8*self.cell_size // 2
        mid_x_R = x + 1.2*self.cell_size // 2
        mid_y_D = y + 0.8*self.cell_size // 2
        mid_y_U = y + 1.2*self.cell_size // 2
        
        # Calcular color de las salidas oscurecido con el factor de brillo
        base_exit_color = 150
        darkened_value = int(base_exit_color * brightness_factor)
        exit_color = (darkened_value, darkened_value, darkened_value)

        # Map directions to deltas for neighbor checking
        delta = {
            Direction.N: (-1, 0),
            Direction.S: (1, 0),
            Direction.E: (0, 1),
            Direction.O: (0, -1),
        }

        def neighbor_coords(dir_: Direction):
            dr, dc = delta[dir_]
            return row + dr, col + dc

        def is_at_edge(dir_: Direction) -> bool:
            """Retorna True si la salida está hacia el borde del tablero."""
            nr, nc = neighbor_coords(dir_)
            return not (0 <= nr < self.size and 0 <= nc < self.size)

        def should_draw_cross(dir_: Direction) -> bool:
            """Retorna True si se debe dibujar una cruz en esta salida."""
            nr, nc = neighbor_coords(dir_)
            if not (0 <= nr < self.size and 0 <= nc < self.size):
                return False
            neighbor = self.board[nr][nc]
            if neighbor.cell_type == CellType.EMPTY:
                return False
            opposite = self.get_opposite_direction(dir_)
            # Dibujar cruz si la vecina tiene la salida complementaria pero yo no tengo la salida hacia ella
            return opposite in neighbor.exits and dir_ not in exits

        # North
        if Direction.N in exits:
            nr, nc = neighbor_coords(Direction.N)
            connected = False
            neighbor_empty = False
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                opposite = self.get_opposite_direction(Direction.N)
                neighbor_empty = (neighbor.cell_type == CellType.EMPTY)
                if neighbor.cell_type != CellType.EMPTY and opposite in neighbor.exits:
                    connected = True

            if self.lines_darkening_enabled:
                self.draw_broken_line(exit_color, (mid_x_L, y), (mid_x_L, y + 0.1*self.cell_size), 4, row, col, 20)
                self.draw_broken_line(exit_color, (mid_x_R, y), (mid_x_R, y + 0.1*self.cell_size), 4, row, col, 21)
            else:
                pygame.draw.line(self.screen, exit_color, (mid_x_L, y), (mid_x_L, y + 0.1*self.cell_size), 4)
                pygame.draw.line(self.screen, exit_color, (mid_x_R, y), (mid_x_R, y + 0.1*self.cell_size), 4)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar la salida en negro
            if is_at_edge(Direction.N) or (not connected and not neighbor_empty):
                if self.lines_darkening_enabled:
                    self.draw_broken_line((0, 0, 0), (mid_x_L, y + 0.05*self.cell_size), (mid_x_R, y + 0.05*self.cell_size), 4, row, col, 22)
                else:
                    pygame.draw.line(self.screen, (0, 0, 0), (mid_x_L, y + 0.05*self.cell_size), (mid_x_R, y + 0.05*self.cell_size), 4)

        # North (complementaria): si la vecina tiene N pero yo no, dibujar cruz en la vecina
        if Direction.N not in exits:
            nr, nc = neighbor_coords(Direction.N)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.N)
                    if opposite in neighbor.exits:
                        # Dibujar cruz en la abertura N de la vecina (que es S desde la perspectiva de la vecina)
                        # La vecina está al norte, así que su abertura S está al sur de su celda
                        neighbor_y = nr * self.cell_size
                        neighbor_mid_x_L = nc * self.cell_size + 0.8*self.cell_size // 2
                        neighbor_mid_x_R = nc * self.cell_size + 1.2*self.cell_size // 2
                        pygame.draw.line(self.screen, (0, 0, 0), (neighbor_mid_x_L, neighbor_y + self.cell_size - 0.05*self.cell_size), (neighbor_mid_x_R, neighbor_y + self.cell_size - 0.05*self.cell_size), 2)

        # South
        if Direction.S in exits:
            nr, nc = neighbor_coords(Direction.S)
            connected = False
            neighbor_empty = False
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                opposite = self.get_opposite_direction(Direction.S)
                neighbor_empty = (neighbor.cell_type == CellType.EMPTY)
                if neighbor.cell_type != CellType.EMPTY and opposite in neighbor.exits:
                    connected = True

            if self.lines_darkening_enabled:
                self.draw_broken_line(exit_color, (mid_x_L, y + self.cell_size), (mid_x_L, y + 0.8*self.cell_size), 4, row, col, 30)
                self.draw_broken_line(exit_color, (mid_x_R, y + self.cell_size), (mid_x_R, y + 0.8*self.cell_size), 4, row, col, 31)
            else:
                pygame.draw.line(self.screen, exit_color, (mid_x_L, y + self.cell_size), (mid_x_L, y + 0.8*self.cell_size), 4)
                pygame.draw.line(self.screen, exit_color, (mid_x_R, y + self.cell_size), (mid_x_R, y + 0.8*self.cell_size), 4)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.S) or (not connected and not neighbor_empty):
                if self.lines_darkening_enabled:
                    self.draw_broken_line((0, 0, 0), (mid_x_L, y + self.cell_size - 0.05*self.cell_size), (mid_x_R, y + self.cell_size - 0.05*self.cell_size), 4, row, col, 32)
                else:
                    pygame.draw.line(self.screen, (0, 0, 0), (mid_x_L, y + self.cell_size - 0.05*self.cell_size), (mid_x_R, y + self.cell_size - 0.05*self.cell_size), 4)

        # South (complementaria)
        if Direction.S not in exits:
            nr, nc = neighbor_coords(Direction.S)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.S)
                    if opposite in neighbor.exits:
                        neighbor_y = nr * self.cell_size
                        neighbor_mid_x_L = nc * self.cell_size + 0.8*self.cell_size // 2
                        neighbor_mid_x_R = nc * self.cell_size + 1.2*self.cell_size // 2
                        pygame.draw.line(self.screen, (0, 0, 0), (neighbor_mid_x_L, neighbor_y + 0.05*self.cell_size), (neighbor_mid_x_R, neighbor_y + 0.05*self.cell_size), 2)

        # East
        if Direction.E in exits:
            nr, nc = neighbor_coords(Direction.E)
            connected = False
            neighbor_empty = False
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                opposite = self.get_opposite_direction(Direction.E)
                neighbor_empty = (neighbor.cell_type == CellType.EMPTY)
                if neighbor.cell_type != CellType.EMPTY and opposite in neighbor.exits:
                    connected = True

            if self.lines_darkening_enabled:
                self.draw_broken_line(exit_color, (x + self.cell_size, mid_y_D), (x + 0.8*self.cell_size, mid_y_D), 4, row, col, 40)
                self.draw_broken_line(exit_color, (x + self.cell_size, mid_y_U), (x + 0.8*self.cell_size, mid_y_U), 4, row, col, 41)
            else:
                pygame.draw.line(self.screen, exit_color, (x + self.cell_size, mid_y_D), (x + 0.8*self.cell_size, mid_y_D), 4)
                pygame.draw.line(self.screen, exit_color, (x + self.cell_size, mid_y_U), (x + 0.8*self.cell_size, mid_y_U), 4)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.E) or (not connected and not neighbor_empty):
                if self.lines_darkening_enabled:
                    self.draw_broken_line((0, 0, 0), (x + self.cell_size - 0.05*self.cell_size, mid_y_D), (x + self.cell_size - 0.05*self.cell_size, mid_y_U), 4, row, col, 42)
                else:
                    pygame.draw.line(self.screen, (0, 0, 0), (x + self.cell_size - 0.05*self.cell_size, mid_y_D), (x + self.cell_size - 0.05*self.cell_size, mid_y_U), 4)

        # East (complementaria)
        if Direction.E not in exits:
            nr, nc = neighbor_coords(Direction.E)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.E)
                    if opposite in neighbor.exits:
                        neighbor_x = nc * self.cell_size
                        neighbor_mid_y_D = nr * self.cell_size + 0.8*self.cell_size // 2
                        neighbor_mid_y_U = nr * self.cell_size + 1.2*self.cell_size // 2
                        pygame.draw.line(self.screen, (0, 0, 0), (neighbor_x + 0.05*self.cell_size, neighbor_mid_y_D), (neighbor_x + 0.05*self.cell_size, neighbor_mid_y_U), 2)

        # West
        if Direction.O in exits:
            nr, nc = neighbor_coords(Direction.O)
            connected = False
            neighbor_empty = False
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                opposite = self.get_opposite_direction(Direction.O)
                neighbor_empty = (neighbor.cell_type == CellType.EMPTY)
                if neighbor.cell_type != CellType.EMPTY and opposite in neighbor.exits:
                    connected = True

            if self.lines_darkening_enabled:
                self.draw_broken_line(exit_color, (x, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 4, row, col, 50)
                self.draw_broken_line(exit_color, (x, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 4, row, col, 51)
            else:
                pygame.draw.line(self.screen, exit_color, (x, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 4)
                pygame.draw.line(self.screen, exit_color, (x, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 4)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.O) or (not connected and not neighbor_empty):
                if self.lines_darkening_enabled:
                    self.draw_broken_line((0, 0, 0), (x + 0.05*self.cell_size, mid_y_D), (x + 0.05*self.cell_size, mid_y_U), 4, row, col, 52)
                else:
                    pygame.draw.line(self.screen, (0, 0, 0), (x + 0.05*self.cell_size, mid_y_D), (x + 0.05*self.cell_size, mid_y_U), 4)

        # West (complementaria)
        if Direction.O not in exits:
            nr, nc = neighbor_coords(Direction.O)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.O)
                    if opposite in neighbor.exits:
                        neighbor_x = nc * self.cell_size
                        neighbor_mid_y_D = nr * self.cell_size + 0.8*self.cell_size // 2
                        neighbor_mid_y_U = nr * self.cell_size + 1.2*self.cell_size // 2
                        pygame.draw.line(self.screen, (0, 0, 0), (neighbor_x + self.cell_size - 0.05*self.cell_size, neighbor_mid_y_D), (neighbor_x + self.cell_size - 0.05*self.cell_size, neighbor_mid_y_U), 2)

    def draw_openings(self, offset_row: int, offset_col: int, pixel_offset_x: int = 0, pixel_offset_y: int = 0):
        """Dibuja las aberturas negras entre celdas conectadas (sobre los bordes).

        Se limita el área de la apertura entre las dos 'líneas' de la salida,
        más ancha y más corta para no solapa las líneas de salida.
        """
        for view_r in range(-1, self.view_size + 1):
            for view_c in range(-1, self.view_size + 1):
                board_r = offset_row + view_r
                board_c = offset_col + view_c
                if not (0 <= board_r < self.size and 0 <= board_c < self.size):
                    continue
                cell = self.board[board_r][board_c]
                if cell.cell_type == CellType.EMPTY:
                    continue

                x = view_c * self.cell_size - pixel_offset_x
                y = view_r * self.cell_size - pixel_offset_y

                # Posiciones de las dos líneas de la salida (consistentes con draw_cell)
                mid_x_L = x + 0.8*self.cell_size // 2
                mid_x_R = x + 1.2*self.cell_size // 2
                mid_y_D = y + 0.8*self.cell_size // 2
                mid_y_U = y + 1.2*self.cell_size // 2

                # Grosor de la apertura en píxeles (más ancho para conectar con pasillo)
                open_thickness = max(12, int(self.cell_size * 0.20))
                # Largo más corto para no solapa las líneas de salida
                open_length = max(4, int(self.cell_size * 0.10))

                # Para cada salida, si la vecina existe y tiene la salida complementaria,
                # dibujar un rect negro entre las dos líneas para 'abrir' la pared.
                delta = {
                    Direction.N: (-1, 0),
                    Direction.S: (1, 0),
                    Direction.E: (0, 1),
                    Direction.O: (0, -1),
                }

                for dir_ in [Direction.N, Direction.S, Direction.E, Direction.O]:
                    if dir_ not in cell.exits:
                        continue
                    dr, dc = delta[dir_]
                    nr, nc = board_r + dr, board_c + dc
                    if not (0 <= nr < self.size and 0 <= nc < self.size):
                        continue
                    neighbor = self.board[nr][nc]
                    opposite = self.get_opposite_direction(dir_)
                    if neighbor.cell_type == CellType.EMPTY:
                        # vecina es EMPTY: la salida aparece como abierta hacia vacío — no borrar borde
                        continue
                    if opposite not in neighbor.exits:
                        # no conectada
                        continue
                    
                    # Solo dibujar la apertura si ambas celdas han sido visitadas
                    if (board_r, board_c) not in self.visited_cells or (nr, nc) not in self.visited_cells:
                        continue

                    # Conectada: dibujar apertura con promedio de luminosidad de ambas celdas
                    # Calcular el brillo promedio entre esta celda y la vecina
                    brightness_current = self.get_cell_brightness(board_r, board_c)
                    brightness_neighbor = self.get_cell_brightness(nr, nc)
                    avg_brightness = (brightness_current + brightness_neighbor) // 2
                    opening_color = (avg_brightness, avg_brightness, avg_brightness)
                    
                    # Los rects deben respetar las líneas perpendiculares para que sea invisible la transición
                    if dir_ == Direction.N:
                        # Norte: rect horizontal entre mid_x_L y mid_x_R, pero respetando las líneas verticales
                        rx = int(mid_x_L) + 2
                        ry = int(y - open_thickness // 2)
                        rw = int(mid_x_R - mid_x_L) - 4
                        rh = int(open_thickness)
                        pygame.draw.rect(self.screen, opening_color, (rx, ry, rw, rh))
                    elif dir_ == Direction.S:
                        # Sur: rect horizontal entre mid_x_L y mid_x_R, respetando líneas verticales
                        rx = int(mid_x_L) + 2
                        ry = int(y + self.cell_size - open_thickness // 2)
                        rw = int(mid_x_R - mid_x_L) - 4
                        rh = int(open_thickness)
                        pygame.draw.rect(self.screen, opening_color, (rx, ry, rw, rh))
                    elif dir_ == Direction.E:
                        # Este: rect vertical entre mid_y_D y mid_y_U, respetando líneas horizontales
                        rx = int(x + self.cell_size - open_thickness // 2)
                        ry = int(mid_y_D) + 2
                        rw = int(open_thickness)
                        rh = int(mid_y_U - mid_y_D) - 4
                        pygame.draw.rect(self.screen, opening_color, (rx, ry, rw, rh))
                    elif dir_ == Direction.O:
                        # Oeste: rect vertical entre mid_y_D y mid_y_U, respetando líneas horizontales
                        rx = int(x - open_thickness // 2)
                        ry = int(mid_y_D) + 2
                        rw = int(open_thickness)
                        rh = int(mid_y_U - mid_y_D) - 4
                        pygame.draw.rect(self.screen, opening_color, (rx, ry, rw, rh))

    def get_cell_brightness(self, board_row: int, board_col: int) -> int:
        """Calcula el brillo de una celda basándose en su número de antorchas."""
        cell = self.board[board_row][board_col]
        if cell.cell_type == CellType.EMPTY:
            return 0
        else:
            # INICIO, PASILLO, HABITACION, SALIDA: todas usan el mismo sistema de iluminación
            torch_count = self.count_torches(board_row, board_col, cell)
            return 10 + min(130, torch_count * 31)
    
    def get_opposite_direction(self, direction: Direction) -> Direction:
        """Retorna la dirección opuesta."""
        opposites = {
            Direction.N: Direction.S,
            Direction.S: Direction.N,
            Direction.E: Direction.O,
            Direction.O: Direction.E,
        }
        return opposites.get(direction, direction)

    def draw_stone_texture(self, board_row: int, board_col: int, x: int, y: int):
        """Dibuja una textura de piedra en la celda dada usando un patrón determinista por celda.

        Esto crea pequeñas 'piedras' con tonos grisáceos y bordes sutiles para dar sensación de muro.
        """
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed)

        base_color = (90, 90, 90)
        pygame.draw.rect(self.screen, base_color, (x, y, self.cell_size, self.cell_size))

        # Dibujar piedras (óvalos) distribuidos aleatoriamente pero deterministas
        # Más relleno: más piedras y más grietas
        num_stones = rnd.randint(36, 70)
        for _ in range(num_stones):
            w = rnd.randint(max(4, int(self.cell_size * 0.06)), max(6, int(self.cell_size * 0.30)))
            h = rnd.randint(max(3, int(self.cell_size * 0.05)), max(6, int(self.cell_size * 0.22)))
            sx = x + rnd.randint(0, max(0, self.cell_size - w))
            sy = y + rnd.randint(0, max(0, self.cell_size - h))

            shade = rnd.randint(-30, 50)
            base_stone = (120, 120, 120)
            stone_color = tuple(max(0, min(255, base_stone[i] + shade)) for i in range(3))

            # Dibujar la piedra
            pygame.draw.ellipse(self.screen, stone_color, (sx, sy, w, h))

            # Borde más oscuro para dar volumen
            if rnd.random() < 0.85:
                border = tuple(max(0, c - 50) for c in stone_color)
                try:
                    pygame.draw.ellipse(self.screen, border, (sx, sy, w, h), 1)
                except Exception:
                    pass

        # Añadir grietas/mortero más visibles
        for _ in range(rnd.randint(6, 12)):
            x1 = x + rnd.randint(0, self.cell_size)
            y1 = y + rnd.randint(0, self.cell_size)
            x2 = x + rnd.randint(0, self.cell_size)
            y2 = y + rnd.randint(0, self.cell_size)
            mortar_color = (30, 30, 30)
            pygame.draw.line(self.screen, mortar_color, (x1, y1), (x2, y2), 2)

    def draw_stone_in_walls(self, board_row: int, board_col: int, x: int, y: int, cell: Cell, brightness_factor: float = 1.0):
        """Dibuja textura de piedra únicamente en las zonas de pared dentro
        de una celda de tipo PASILLO (entre el suelo/centro y los bordes).

        Se respeta la presencia de salidas: si existe una salida N/S/E/O, se deja
        un hueco en la pared correspondiente para el pasaje.
        
        Args:
            brightness_factor: Factor de brillo (0.0 a 1.0) para oscurecer todos los colores
        """
        if REFACTORED_MODULES:
            self.effects.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor, self.count_torches)
            return
        
        # Versión legacy
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed + 7)

        # Calcular brillo base según número de antorchas, pero aplicando el factor de oscuridad
        torch_count = self.count_torches(board_row, board_col, cell)
        wall_brightness = 20 + min(120, torch_count * 30)  # Base 20, aumenta 30 por antorcha
        wall_brightness = int(wall_brightness * brightness_factor)  # Aplicar factor de oscuridad

        size = self.cell_size
        wall_thickness = max(6, int(size * 0.28))
        gap_w = max(8, int(size * 0.36))
        gap_h = max(8, int(size * 0.36))

        # Rects: top, bottom, left, right (cada uno representando la pared dentro de la celda)
        # Top
        top_rects = []
        if Direction.N in cell.exits:
            # dejar hueco central
            left_w = (size - gap_w) // 2
            top_rects.append((x, y, left_w, wall_thickness))
            top_rects.append((x + left_w + gap_w, y, left_w, wall_thickness))
        else:
            top_rects.append((x, y, size, wall_thickness))

        # Bottom
        bottom_rects = []
        if Direction.S in cell.exits:
            left_w = (size - gap_w) // 2
            bottom_rects.append((x, y + size - wall_thickness, left_w, wall_thickness))
            bottom_rects.append((x + left_w + gap_w, y + size - wall_thickness, left_w, wall_thickness))
        else:
            bottom_rects.append((x, y + size - wall_thickness, size, wall_thickness))

        # Left
        left_rects = []
        if Direction.O in cell.exits:
            top_h = (size - gap_h) // 2
            left_rects.append((x, y, wall_thickness, top_h))
            left_rects.append((x, y + top_h + gap_h, wall_thickness, top_h))
        else:
            left_rects.append((x, y, wall_thickness, size))

        # Right
        right_rects = []
        if Direction.E in cell.exits:
            top_h = (size - gap_h) // 2
            right_rects.append((x + size - wall_thickness, y, wall_thickness, top_h))
            right_rects.append((x + size - wall_thickness, y + top_h + gap_h, wall_thickness, top_h))
        else:
            right_rects.append((x + size - wall_thickness, y, wall_thickness, size))

        all_rects = top_rects + bottom_rects + left_rects + right_rects

        base_stone = (wall_brightness, wall_brightness, wall_brightness)
        for (rx, ry, rw, rh) in all_rects:
            # rellenar esa rect con piedras pequeñas — más denso
            area = max(1, rw * rh)
            num = rnd.randint(max(12, area // 80), max(24, area // 40))
            for _ in range(num):
                # usar piedras más pequeñas y más numerosas
                w = rnd.randint(max(2, int(rw * 0.08)), max(4, int(rw * 0.5)))
                h = rnd.randint(max(2, int(rh * 0.06)), max(4, int(rh * 0.45)))
                sx = rx + rnd.randint(0, max(0, rw - w))
                sy = ry + rnd.randint(0, max(0, rh - h))
                shade = rnd.randint(-40, 60)
                stone_color = tuple(max(0, min(255, base_stone[i] + shade)) for i in range(3))
                pygame.draw.ellipse(self.screen, stone_color, (sx, sy, w, h))
                if rnd.random() < 0.9:
                    border = tuple(max(0, c - 55) for c in stone_color)
                    try:
                        pygame.draw.ellipse(self.screen, border, (sx, sy, w, h), 1)
                    except Exception:
                        pass

        # Añadir algunas grietas en las paredes — más visibles y más numerosas
        for _ in range(rnd.randint(6, 14)):
            (rx, ry, rw, rh) = rnd.choice(all_rects)
            x1 = rx + rnd.randint(0, max(0, rw - 1))
            y1 = ry + rnd.randint(0, max(0, rh - 1))
            x2 = rx + rnd.randint(0, max(0, rw - 1))
            y2 = ry + rnd.randint(0, max(0, rh - 1))
            mortar_color = (25, 25, 25)
            pygame.draw.line(self.screen, mortar_color, (x1, y1), (x2, y2), 2)
    
    def generate_random_exits(self, exclude_direction: Direction, cell_type: CellType, current_pos: tuple) -> set:
        """Genera salidas aleatorias según el tipo de celda, excepto la dirección de entrada.
        Respeta el camino principal: si la celda está en el camino, asegura que tenga
        salida hacia la siguiente celda del camino.
        
        PASILLO: 1 salida 10%, 2 salidas 30%, 3 salidas 40%, 4 salidas 20%
        HABITACION: 1 salida 50%, 2 salidas 30%, 3 salidas 15%, 4 salidas 5%
        """
        exits = set()
        # La dirección opuesta a la de entrada siempre está (es por donde se llegó)
        opposite = self.get_opposite_direction(exclude_direction)
        exits.add(opposite)
        
        # Verificar si esta celda está en el camino principal
        required_direction = None
        if current_pos in self.main_path:
            # Encontrar la siguiente celda en el camino principal
            current_row, current_col = current_pos
            for dr, dc, direction in [(-1, 0, Direction.N), (1, 0, Direction.S), 
                                       (0, -1, Direction.O), (0, 1, Direction.E)]:
                next_pos = (current_row + dr, current_col + dc)
                if next_pos in self.main_path and next_pos != current_pos:
                    # Verificar si es la dirección hacia adelante en el camino
                    # (no la dirección de entrada)
                    if direction != opposite:
                        required_direction = direction
                        exits.add(required_direction)
                        break
        
        # Verificar celdas adyacentes: no generar salidas hacia celdas que existen pero no tienen la salida complementaria
        current_row, current_col = current_pos
        forbidden_directions = set()
        delta = {
            Direction.N: (-1, 0),
            Direction.S: (1, 0),
            Direction.E: (0, 1),
            Direction.O: (0, -1),
        }
        
        for direction in [Direction.N, Direction.E, Direction.S, Direction.O]:
            if direction == exclude_direction or direction == opposite or direction == required_direction:
                continue
            dr, dc = delta[direction]
            neighbor_row = current_row + dr
            neighbor_col = current_col + dc
            
            if 0 <= neighbor_row < self.size and 0 <= neighbor_col < self.size:
                neighbor = self.board[neighbor_row][neighbor_col]
                # Si la celda vecina existe y NO tiene la salida complementaria, no generar salida hacia ella
                if neighbor.cell_type != CellType.EMPTY:
                    opposite_dir = self.get_opposite_direction(direction)
                    if opposite_dir not in neighbor.exits:
                        forbidden_directions.add(direction)
        
        # Las otras direcciones (excluyendo entrada, salida opuesta, dirección requerida y direcciones prohibidas)
        all_directions = {Direction.N, Direction.E, Direction.S, Direction.O}
        excluded = {exclude_direction, opposite}
        if required_direction:
            excluded.add(required_direction)
        excluded.update(forbidden_directions)
        other_directions = list(all_directions - excluded)
        
        if cell_type == CellType.PASILLO:
            # Para pasillo: decidir cuántas salidas adicionales (1-3) basado en probabilidades
            # 1 salida (solo opuesta): 10%
            # 2 salidas (opuesta + 1): 30%
            # 3 salidas (opuesta + 2): 40%
            # 4 salidas (opuesta + 3): 20%
            rand = random.random()
            if rand < 0.10:
                num_additional = 0  # Total 1
            elif rand < 0.40:
                num_additional = 1  # Total 2 (10% + 30% = 40%)
            elif rand < 0.80:
                num_additional = 2  # Total 3 (40% + 40% = 80%)
            else:
                num_additional = 3  # Total 4
            
            # Seleccionar aleatoriamente cuáles de las 3 direcciones restantes incluir
            selected = random.sample(other_directions, min(num_additional, len(other_directions)))
            exits.update(selected)
            
        else:  # HABITACION
            # Para habitación: decidir cuántas salidas adicionales (1-3)
            # 1 salida (solo opuesta): 50%
            # 2 salidas (opuesta + 1): 30%
            # 3 salidas (opuesta + 2): 15%
            # 4 salidas (opuesta + 3): 5%
            rand = random.random()
            if rand < 0.50:
                num_additional = 0  # Total 1
            elif rand < 0.80:
                num_additional = 1  # Total 2
            elif rand < 0.95:
                num_additional = 2  # Total 3
            else:
                num_additional = 3  # Total 4
            
            # Seleccionar aleatoriamente cuáles de las 3 direcciones restantes incluir
            selected = random.sample(other_directions, min(num_additional, len(other_directions)))
            exits.update(selected)
        
        return exits

    def toggle_lines_darkening(self):
        """Toggle del oscurecimiento de líneas (F5)."""
        if REFACTORED_MODULES:
            self.lighting.toggle_lines_darkening()
        else:
            self.lines_darkening_enabled = not self.lines_darkening_enabled
            status = "activado" if self.lines_darkening_enabled else "desactivado"
            print(f"Oscurecimiento de líneas: {status}")
    
    @property
    def lines_darkening_enabled(self):
        """Propiedad para acceder al estado del oscurecimiento."""
        if REFACTORED_MODULES:
            return self.lighting.lines_darkening_enabled
        else:
            return getattr(self, '_lines_darkening_enabled', True)
    
    @lines_darkening_enabled.setter
    def lines_darkening_enabled(self, value):
        """Setter para el oscurecimiento de líneas."""
        if REFACTORED_MODULES:
            self.lighting.lines_darkening_enabled = value
        else:
            self._lines_darkening_enabled = value


    def place_cell_in_direction(self, direction: Direction):
        """Coloca en la celda en la dirección `direction` desde la posición actual
        una celda aleatoria de tipo PASILLO o HABITACION (50/50) con salidas
        aleatorias (25% cada una) excepto la salida por la que se llegó.
        Si la celda ya existe (no es EMPTY), no la modifica.
        Si la celda destino está fuera del tablero o no existe salida en la celda
        actual, no hace nada.
        """
        # Bloquear movimiento durante pensamientos que bloquean movimiento
        if self.thought_active and self.thought_blocks_movement:
            return
        
        # Bloquear movimiento mientras se muestra la imagen de la losa
        if self.exit_image_shown:
            current_time = pygame.time.get_ticks()
            if current_time - self.exit_image_start_time < 10000:  # Durante los 10 segundos
                return
        
        # No bloquear movimiento (permitir continuar después de la imagen)
        
        current_row, current_col = self.current_position
        current_cell = self.board[current_row][current_col]
        
        # Verificar que existe salida en la dirección solicitada
        if direction not in current_cell.exits:
            return
        
        delta = {
            Direction.N: (-1, 0),
            Direction.S: (1, 0),
            Direction.E: (0, 1),
            Direction.O: (0, -1),
        }

        dr, dc = delta.get(direction, (0, 0))
        target_row = current_row + dr
        target_col = current_col + dc

        # Comprobar límites
        if not (0 <= target_row < self.size and 0 <= target_col < self.size):
            return

        target_cell = self.board[target_row][target_col]
        opposite = self.get_opposite_direction(direction)

        # Si la celda ya existe (no es EMPTY): solo moverse si tiene la salida complementaria
        if target_cell.cell_type != CellType.EMPTY:
            if opposite in target_cell.exits:
                # Reproducir sonido de paso alternando entre paso1 y paso2
                if self.footstep_sounds:
                    footstep = self.footstep_sounds[self.last_footstep_index % len(self.footstep_sounds)]
                    footstep.play()
                    self.last_footstep_index += 1
                
                # Iniciar animación suave del muñeco desde posición antigua a nueva
                self.player_anim_from_pos = self.current_position
                self.player_anim_to_pos = (target_row, target_col)
                self.player_animating = True
                self.player_anim_start_time = pygame.time.get_ticks()
                self.player_walk_until = pygame.time.get_ticks() + self.player_walk_duration
                
                # Actualizar posición lógica (la cámara se moverá suavemente hacia esta posición)
                self.current_position = (target_row, target_col)
                # Marcar la celda como visitada
                self.visited_cells.add((target_row, target_col))
                # Revelar celdas adyacentes con salidas
                self.reveal_adjacent_cells(target_row, target_col)
                
                # Verificar si entró en la celda final
                if (target_row, target_col) == self.exit_position and not self.exit_image_shown:
                    self.exit_image_shown = True
                    self.exit_image_start_time = pygame.time.get_ticks()
                
                # Activar pensamiento de sangre si ve manchas por primera vez
                if not self.blood_thought_triggered and self.blood_sound:
                    # Verificar si hay manchas de sangre en esta celda
                    if self.has_blood_stains(target_row, target_col):
                        # Bloquear movimiento inmediatamente
                        self.thought_active = True
                        self.thought_blocks_movement = True
                        self.blood_thought_triggered = True
                        
                        # Activar pensamiento después de 1 segundo
                        import asyncio
                        async def delayed_blood_thought():
                            await asyncio.sleep(1.0)
                            # Solo activar si aún no hay otro pensamiento activo
                            if self.thought_active:
                                self.trigger_thought(
                                    sounds=[(self.blood_sound, 0)],
                                    images=[(self.blood_image, 0)] if self.blood_image else None,
                                    subtitles=[("¿Es eso... sangre?!?", 10000)],
                                    blocks_movement=True
                                )
                        asyncio.create_task(delayed_blood_thought())
                
                # Activar pensamiento de antorchas si es la primera vez que entra en una celda con antorchas
                if not self.torch_thought_triggered and self.torch_sound:
                    current_cell = self.board[target_row][target_col]
                    torch_count = self.count_torches(target_row, target_col, current_cell)
                    if torch_count > 0:
                        # Bloquear movimiento inmediatamente
                        self.thought_active = True
                        self.thought_blocks_movement = True
                        self.torch_thought_triggered = True
                        
                        # Activar pensamiento después de 1 segundo
                        import asyncio
                        async def delayed_torch_thought():
                            await asyncio.sleep(1.0)
                            # Solo activar si aún no hay otro pensamiento activo
                            if self.thought_active:
                                self.trigger_thought(
                                    sounds=[(self.torch_sound, 0)],
                                    images=[(self.torch_image, 0)] if self.torch_image else None,
                                    subtitles=[("Una antorcha encendida... ¡Interesante!", 6000)],
                                    blocks_movement=True
                                )
                        asyncio.create_task(delayed_torch_thought())
            # si existe pero no tiene la salida complementaria, no se puede mover
            return

        # Si la celda es EMPTY, crearla
        # Verificar si es la posición de salida
        if (target_row, target_col) == self.exit_position:
            # Crear celda SALIDA con solo la salida de entrada
            exits = {opposite}
            self.board[target_row][target_col] = Cell(CellType.SALIDA, exits)
        else:
            # 75% PASILLO, 25% HABITACION
            cell_type = CellType.PASILLO if random.random() < 0.75 else CellType.HABITACION
            exits = self.generate_random_exits(direction, cell_type, (target_row, target_col))
        
            # Comprobar celdas adyacentes: si existe una vecina con salida hacia aquí, mantener esa salida
            delta = {
                Direction.N: (-1, 0),
                Direction.S: (1, 0),
                Direction.E: (0, 1),
                Direction.O: (0, -1),
            }
            
            for dir_ in [Direction.N, Direction.E, Direction.S, Direction.O]:
                dr, dc = delta[dir_]
                neighbor_row = target_row + dr
                neighbor_col = target_col + dc
                
                if 0 <= neighbor_row < self.size and 0 <= neighbor_col < self.size:
                    neighbor = self.board[neighbor_row][neighbor_col]
                    if neighbor.cell_type != CellType.EMPTY:
                        opposite_dir = self.get_opposite_direction(dir_)
                        # Si la vecina tiene salida hacia aquí, mantener esa salida en la nueva celda
                        if opposite_dir in neighbor.exits:
                            exits.add(dir_)
            
            self.board[target_row][target_col] = Cell(cell_type, exits)
        
        # Reproducir sonido de paso alternando entre paso1 y paso2
        if self.footstep_sounds:
            footstep = self.footstep_sounds[self.last_footstep_index % len(self.footstep_sounds)]
            footstep.play()
            self.last_footstep_index += 1
        
        # Iniciar animación suave del muñeco desde posición antigua a nueva
        self.player_anim_from_pos = self.current_position
        self.player_anim_to_pos = (target_row, target_col)
        self.player_animating = True
        self.player_anim_start_time = pygame.time.get_ticks()
        self.player_walk_until = pygame.time.get_ticks() + self.player_walk_duration
        
        # Actualizar posición lógica (la cámara se moverá suavemente hacia esta posición)
        self.current_position = (target_row, target_col)
        # Marcar la celda como visitada
        self.visited_cells.add((target_row, target_col))
        # Revelar celdas adyacentes con salidas
        self.reveal_adjacent_cells(target_row, target_col)
    
    def reveal_adjacent_cells(self, row, col):
        """Revela las celdas adyacentes que tienen salidas conectadas desde la celda actual.
        Solo funciona si auto_reveal_mode está activo."""
        if not self.auto_reveal_mode:
            return
        
        current_cell = self.board[row][col]
        
        # Para cada dirección, si hay una salida, revelar la celda adyacente
        direction_deltas = {
            Direction.N: (-1, 0),
            Direction.S: (1, 0),
            Direction.E: (0, 1),
            Direction.O: (0, -1)
        }
        
        for direction, (dr, dc) in direction_deltas.items():
            if direction in current_cell.exits:
                adj_row, adj_col = row + dr, col + dc
                if 0 <= adj_row < self.size and 0 <= adj_col < self.size:
                    # Revelar todas las celdas con salidas conectadas
                    self.visited_cells.add((adj_row, adj_col))
    
    def count_torches(self, board_row, board_col, cell):
        """Cuenta cuántas antorchas se dibujarán realmente en esta celda.
        Solo aparecen en celdas del camino principal.
        La probabilidad aumenta conforme se acerca a la salida."""
        # Si las antorchas están apagadas, no hay antorchas
        if self.torches_extinguished:
            return 0
        
        # Si las antorchas están parpadeando, aplicar efecto de parpadeo
        if self.torches_flickering:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.flicker_start_time
            
            # Si ya pasó la duración del parpadeo, apagar definitivamente
            if elapsed >= self.flicker_duration:
                self.torches_flickering = False
                self.torches_extinguished = True
                print("[DEBUG] Antorchas apagadas definitivamente")
                return 0
            
            # Parpadeo: alternar entre visible/invisible cada vez más rápido
            # Primero parpadeos lentos (500ms), luego medios (250ms), luego rápidos (100ms)
            if elapsed < 3000:  # Primeros 3 segundos: parpadeo lento
                flicker_interval = 500
            elif elapsed < 6000:  # Segundos 3-6: parpadeo medio
                flicker_interval = 250
            else:  # Últimos 2 segundos: parpadeo rápido
                flicker_interval = 100
            
            # Alternar entre visible/invisible
            if (elapsed // flicker_interval) % 2 == 0:
                return 0  # Invisible (antorchas apagadas en este frame)
            # Si es impar, continuar con la lógica normal (antorchas visibles)
        
        # Durante la introducción, no hay antorchas
        if self.intro_anim_active:
            return 0
        
        # Si el pensamiento de intro no ha terminado, no hay antorchas
        if not self.intro_thought_finished:
            return 0
        
        # Si no está en el camino principal, no hay antorchas
        if (board_row, board_col) not in self.main_path:
            return 0
        
        # Calcular distancia a la salida
        exit_row, exit_col = self.exit_position
        distance_to_exit = abs(exit_row - board_row) + abs(exit_col - board_col)
        
        # Contar cuántas paredes sin salida hay disponibles
        available_walls = 0
        if Direction.N not in cell.exits:
            available_walls += 1
        if Direction.S not in cell.exits:
            available_walls += 1
        if Direction.E not in cell.exits:
            available_walls += 1
        if Direction.O not in cell.exits:
            available_walls += 1
        
        # En la salida, garantizar al menos una antorcha
        if (board_row, board_col) == self.exit_position:
            if available_walls == 0:
                return 0
            return max(1, available_walls)  # Al menos 1, máximo todas las paredes
        
        # Calcular distancia total del camino (aproximada)
        start_row, start_col = self.start_position
        total_distance = abs(exit_row - start_row) + abs(exit_col - start_col)
        
        # Calcular probabilidad base que DISMINUYE al acercarse a la salida
        # En el inicio: ~40%, en la salida: ~10%
        if total_distance > 0:
            progress = 1.0 - (distance_to_exit / total_distance)  # 0 en inicio, 1 en salida
        else:
            progress = 0.5
        
        base_probability = 0.4 - (progress * 0.3)  # 40% a 10%
        
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed)
        
        # Generar entre 0 y 4 antorchas con probabilidad variable
        desired_torches = 0
        for _ in range(4):
            if rnd.random() < base_probability:
                desired_torches += 1
        
        # Retornar el mínimo entre antorchas deseadas y paredes disponibles
        return min(desired_torches, available_walls)
    
    def draw_broken_line(self, color, start_pos, end_pos, width, board_row, board_col, line_id):
        """Dibuja una línea quebrada (con segmentos irregulares).
        
        Args:
            color: Color de la línea
            start_pos: Tupla (x, y) de inicio
            end_pos: Tupla (x, y) de fin
            width: Ancho de la línea
            board_row: Fila en el tablero (para semilla)
            board_col: Columna en el tablero (para semilla)
            line_id: ID único de la línea (para semilla)
        """
        if REFACTORED_MODULES:
            self.effects.draw_broken_line(color, start_pos, end_pos, width, board_row, board_col, line_id)
            return
        
        # Versión legacy
        # Asegurar que el color tiene valores enteros
        color = tuple(int(c) for c in color)
        
        # Usar posición + line_id como semilla para reproducibilidad
        seed = board_row * 100000 + board_col * 100 + line_id
        rnd = random.Random(seed)
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calcular longitud de la línea
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        if length < 5:
            # Línea muy corta, dibujar directamente
            pygame.draw.line(self.screen, color, start_pos, end_pos, width)
            return
        
        # Número de segmentos (más segmentos = más quebrada)
        num_segments = max(3, int(length / 10))
        
        # Generar puntos intermedios con desplazamiento aleatorio
        points = [start_pos]
        for i in range(1, num_segments):
            t = i / num_segments
            # Punto en la línea recta
            px = x1 + t * (x2 - x1)
            py = y1 + t * (y2 - y1)
            
            # Desplazamiento perpendicular aleatorio
            # Vector perpendicular
            dx = x2 - x1
            dy = y2 - y1
            perp_x = -dy
            perp_y = dx
            # Normalizar
            perp_len = (perp_x ** 2 + perp_y ** 2) ** 0.5
            if perp_len > 0:
                perp_x /= perp_len
                perp_y /= perp_len
            
            # Desplazamiento aleatorio (hasta 3 píxeles)
            offset = rnd.uniform(-3, 3)
            px += perp_x * offset
            py += perp_y * offset
            
            points.append((int(px), int(py)))
        
        points.append(end_pos)
        
        # Dibujar segmentos
        for i in range(len(points) - 1):
            pygame.draw.line(self.screen, color, points[i], points[i + 1], width)
    
    def has_blood_stains(self, board_row, board_col):
        """Verifica si una celda tiene manchas de sangre."""
        exit_row, exit_col = self.exit_position
        distance = abs(exit_row - board_row) + abs(exit_col - board_col)
        
        # Solo puede haber manchas en celdas a distancia 1-10 de la salida
        if distance < 1 or distance > 10:
            return False
        
        # Usar posición como semilla para reproducibilidad
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed)
        
        # Probabilidad de manchas aumenta al acercarse (30% a dist 10, 100% a dist 1)
        probability = 1.0 - ((distance - 1) / 9.0) * 0.7
        return rnd.random() <= probability
    
    def draw_blood_stains(self, board_row, board_col, x, y, brightness_factor: float = 1.0):
        """Dibuja manchas de sangre en celdas cercanas a la salida.
        Las manchas de sangre se oscurecen con el 50% del gradiente de distancia.
        
        Args:
            brightness_factor: Factor de brillo (0.0 a 1.0) para oscurecer todos los colores
        """
        # Aplicar 50% del oscurecimiento a la sangre
        blood_brightness_factor = 1.0 - 0.5 * (1.0 - brightness_factor)
        
        exit_row, exit_col = self.exit_position
        distance = abs(exit_row - board_row) + abs(exit_col - board_col)
        
        # Solo dibujar manchas en celdas a distancia 1-10 de la salida
        if distance < 1 or distance > 10:
            return
        
        # Usar posición como semilla para reproducibilidad
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed)
        
        # Probabilidad de manchas aumenta al acercarse (30% a dist 10, 100% a dist 1)
        probability = 1.0 - ((distance - 1) / 9.0) * 0.7
        if rnd.random() > probability:
            return
        
        # Color de sangre oscura, aplicando el 50% del factor de oscuridad
        blood_colors = [
            tuple(int(c * blood_brightness_factor) for c in (80, 0, 0)),    # Rojo muy oscuro
            tuple(int(c * blood_brightness_factor) for c in (100, 10, 10)), # Rojo oscuro
            tuple(int(c * blood_brightness_factor) for c in (70, 5, 5)),    # Casi negro rojizo
        ]
        
        # Generar 2-5 manchas por celda
        num_stains = rnd.randint(2, 5)
        for i in range(num_stains):
            # Posición aleatoria en el suelo (evitar bordes)
            stain_x = x + int(rnd.uniform(0.2, 0.8) * self.cell_size)
            stain_y = y + int(rnd.uniform(0.2, 0.8) * self.cell_size)
            
            # Tamaño aleatorio
            size = rnd.randint(4, 12)
            
            # Color aleatorio de sangre
            color = rnd.choice(blood_colors)
            
            # Dibujar mancha irregular (varios círculos superpuestos)
            num_circles = rnd.randint(2, 4)
            for j in range(num_circles):
                offset_x = rnd.randint(-size//2, size//2)
                offset_y = rnd.randint(-size//2, size//2)
                circle_size = rnd.randint(size//2, size)
                pygame.draw.circle(self.screen, color, 
                                 (stain_x + offset_x, stain_y + offset_y), 
                                 circle_size)
    
    def draw_torches(self, board_row, board_col, x, y, cell):
        """Dibuja antorchas animadas. Las antorchas se posicionan en las paredes sin salida,
        pero su cantidad es independiente del número de salidas.
        Las antorchas NO se oscurecen con el gradiente de distancia.
        """
        # Usar seed para posiciones deterministas
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed)
        
        # Animación de la llama (parpadeo)
        t = pygame.time.get_ticks()
        flicker = abs(math.sin(t * 0.003 + seed)) * 0.3 + 0.7  # Oscila entre 0.7 y 1.0
        
        # Tamaño de la antorcha
        torch_size = max(8, int(self.cell_size * 0.15))
        
        wall_thickness = int(self.cell_size * 0.28)
        
        # Obtener el número de antorchas que debe tener esta celda
        num_torches = self.count_torches(board_row, board_col, cell)
        
        # Crear lista de posibles ubicaciones (paredes sin salidas)
        possible_positions = []
        
        if Direction.N not in cell.exits:
            possible_positions.append(('N', x + self.cell_size // 2 + rnd.randint(-20, 20), y + wall_thickness // 2))
        if Direction.S not in cell.exits:
            possible_positions.append(('S', x + self.cell_size // 2 + rnd.randint(-20, 20), y + self.cell_size - wall_thickness // 2))
        if Direction.E not in cell.exits:
            possible_positions.append(('E', x + self.cell_size - wall_thickness // 2, y + self.cell_size // 2 + rnd.randint(-20, 20)))
        if Direction.O not in cell.exits:
            possible_positions.append(('O', x + wall_thickness // 2, y + self.cell_size // 2 + rnd.randint(-20, 20)))
        
        # Dibujar antorchas en las primeras N posiciones disponibles
        for i in range(min(num_torches, len(possible_positions))):
            _, torch_x, torch_y = possible_positions[i]
            self.draw_single_torch(torch_x, torch_y, torch_size, flicker)
    
    def draw_single_torch(self, x, y, size, flicker):
        """Dibuja una antorcha individual con llama animada.
        Las antorchas NO se oscurecen con el gradiente de distancia.
        """
        # Soporte de madera (marrón oscuro)
        stick_width = max(2, size // 4)
        stick_height = size
        pygame.draw.rect(self.screen, (101, 67, 33), 
                        (x - stick_width // 2, y, stick_width, stick_height))
        
        # Llama (naranja/amarillo con parpadeo)
        flame_radius = int(size * 0.6 * flicker)
        flame_y = y - size // 3
        
        # Llama exterior (naranja)
        pygame.draw.circle(self.screen, (255, 140, 0), (x, flame_y), flame_radius)
        # Llama interior (amarillo brillante)
        inner_radius = max(2, int(flame_radius * 0.6))
        pygame.draw.circle(self.screen, (255, 220, 100), (x, flame_y), inner_radius)
        
        # Resplandor sutil (opcional - círculo semi-transparente)
        glow_surface = pygame.Surface((flame_radius * 3, flame_radius * 3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 180, 50, 40), 
                          (flame_radius * 1.5, flame_radius * 1.5), flame_radius * 1.5)
        self.screen.blit(glow_surface, (x - flame_radius * 1.5, flame_y - flame_radius * 1.5))
    
    def draw_spiral_stairs(self, x: int, y: int):
        """Dibuja una escalera de caracol en una esquina de la celda.
        La escalera NO se oscurece con el gradiente de distancia.
        """
        # Posición en la esquina superior derecha
        corner_x = x + int(self.cell_size * 0.75)
        corner_y = y + int(self.cell_size * 0.25)
        
        # Radio de la escalera de caracol
        radius = int(self.cell_size * 0.15)
        
        # Círculo central (poste)
        pygame.draw.circle(self.screen, (100, 80, 60), (corner_x, corner_y), radius // 3)
        
        # Dibujar escalones en espiral (6 escalones)
        num_steps = 6
        for i in range(num_steps):
            angle = (i * 360 / num_steps) * (math.pi / 180)
            # Radio del escalón (crece ligeramente hacia arriba)
            step_radius = radius * (0.6 + 0.4 * (i / num_steps))
            
            # Punto inicial y final del escalón
            x1 = corner_x + int(step_radius * 0.3 * math.cos(angle))
            y1 = corner_y + int(step_radius * 0.3 * math.sin(angle))
            x2 = corner_x + int(step_radius * math.cos(angle))
            y2 = corner_y + int(step_radius * math.sin(angle))
            
            # Color más claro para escalones superiores
            brightness = 120 + int(30 * (i / num_steps))
            step_color = (brightness, brightness - 20, brightness - 40)
            
            # Dibujar el escalón como línea gruesa
            pygame.draw.line(self.screen, step_color, (x1, y1), (x2, y2), max(2, int(self.cell_size * 0.04)))
        
        # Círculo exterior (sombra/borde)
        pygame.draw.circle(self.screen, (80, 60, 40), (corner_x, corner_y), radius, 2)
    
    def draw_fountain(self, x: int, y: int):
        """Dibuja una fuente en la esquina superior izquierda de una celda.
        La fuente NO se oscurece con el gradiente de distancia.
        """
        # Base de la fuente (cuadrado)
        fountain_size = int(self.cell_size * 0.22)
        fountain_x = x + int(self.cell_size * 0.08)
        fountain_y = y + int(self.cell_size * 0.08)
        
        # Base gris piedra
        pygame.draw.rect(self.screen, (100, 100, 100), (fountain_x, fountain_y, fountain_size, fountain_size))
        pygame.draw.rect(self.screen, (150, 150, 150), (fountain_x, fountain_y, fountain_size, fountain_size), 2)
        
        # Centro (agua) - círculo azul claro
        center_x = fountain_x + fountain_size // 2
        center_y = fountain_y + fountain_size // 2
        water_radius = max(3, fountain_size // 2)
        pygame.draw.circle(self.screen, (100, 180, 255), (center_x, center_y), water_radius)
        
        # Borde del agua
        pygame.draw.circle(self.screen, (150, 200, 255), (center_x, center_y), water_radius, 2)
    
    def update_music_volume_by_distance(self):
        """Actualizar volumen de música según distancia al inicio y al final"""
        # Calcular distancias
        start_row, start_col = self.start_position
        exit_row, exit_col = self.exit_position
        curr_row, curr_col = self.current_position
        distance_from_start = ((curr_row - start_row)**2 + (curr_col - start_col)**2)**0.5
        distance_to_exit = ((curr_row - exit_row)**2 + (curr_col - exit_col)**2)**0.5
        
        if self.current_music == 'adagio' and not self.cthulhu_played:  # Solo para adagio
            # Volumen de adagio disminuye con la distancia al inicio
            # Volumen máximo (0.5) en el inicio, mínimo (0.05) a distancia 5 o más
            max_volume = 0.5
            min_volume = 0.05
            max_distance = 5.0
            
            # Interpolación lineal desde el inicio
            volume = max_volume - (distance_from_start / max_distance) * (max_volume - min_volume)
            volume = max(min_volume, min(max_volume, volume))  # Clamp entre min y max
            
            self.music_channel.set_volume(volume)
            
            # Si estamos cerca de la salida, cambiar a cthulhu
            if distance_to_exit <= 5.0 and not self.cthulhu_played and 'cthulhu' in self.music_sounds:
                self.music_channel.stop()
                self.current_music = 'cthulhu'
                self.music_channel.play(self.music_sounds['cthulhu'], loops=-1)
                self.music_channel.set_volume(min_volume)  # Empezar con volumen bajo
                self.cthulhu_played = True
        
        elif self.cthulhu_played:  # Volumen de cthulhu aumenta al acercarse a la salida
            # Si estamos en la celda de salida, volumen máximo (1.0) y mostrar subtítulo
            if (curr_row, curr_col) == self.exit_position:
                # Solo configurar volumen de Cthulhu si el viento aún no está sonando
                if not self.wind_fading_in and self.current_music == 'cthulhu':
                    self.music_channel.set_volume(1.0)
                
                # Mostrar subtítulos e imagen de Cthulhu solo una vez al llegar a la salida
                if not self.showing_subtitles and not hasattr(self, 'cthulhu_subtitle_shown'):
                    # Usar trigger_thought para el pensamiento completo de Cthulhu
                    # La imagen dura más que el subtítulo para dar un efecto dramático
                    self.trigger_thought(
                        images=[(self.exit_image, 12000)] if self.exit_image else None,  # Imagen por 12 segundos
                        subtitles=[("PH'NGLUI MGLW'NAFH CTHULHU R'LYEH WGAH'NAGL FHTAGN", 8000)],
                        blocks_movement=False
                    )
                    self.cthulhu_subtitle_shown = True
            # Si volvemos cerca del inicio, regresar a adagio
            elif distance_from_start <= 5.0 and 'adagio' in self.music_sounds:
                self.music_channel.stop()
                self.current_music = 'adagio'
                self.music_channel.play(self.music_sounds['adagio'], loops=-1)
                # Volumen según distancia al inicio
                max_volume = 0.5
                min_volume = 0.05
                max_distance = 5.0
                volume = max_volume - (distance_from_start / max_distance) * (max_volume - min_volume)
                volume = max(min_volume, min(max_volume, volume))
                self.music_channel.set_volume(volume)
                self.cthulhu_played = False
            else:
                # Volumen de cthulhu aumenta al acercarse a la salida
                # Volumen mínimo (0.05) a distancia 5, máximo (1.0) en la salida
                max_volume = 1.0
                min_volume = 0.05
                max_distance = 5.0
                
                # Interpolación lineal inversa (aumenta al acercarse)
                volume = max_volume - (distance_to_exit / max_distance) * (max_volume - min_volume)
                volume = max(min_volume, min(max_volume, volume))  # Clamp entre min y max
                
                self.music_channel.set_volume(volume)
    
    def zoom_in(self):
        """Aumenta el zoom (reduce view_size) - acerca la vista."""
        if self.current_zoom_index > 0:
            self.current_zoom_index -= 1
            self.view_size = self.zoom_levels[self.current_zoom_index]
            # Ajustar el tamaño de las celdas para mantener ventana fija
            self.cell_size = self.fixed_window_size // self.view_size
            # Recentrar la cámara en la posición actual
            self.update_camera_target()
    
    def zoom_out(self):
        """Reduce el zoom (aumenta view_size) - aleja la vista."""
        if self.current_zoom_index < len(self.zoom_levels) - 1:
            self.current_zoom_index += 1
            self.view_size = self.zoom_levels[self.current_zoom_index]
            # Ajustar el tamaño de las celdas para mantener ventana fija
            self.cell_size = self.fixed_window_size // self.view_size
            # Recentrar la cámara en la posición actual
            self.update_camera_target()
    
    def update_camera_target(self):
        """Actualiza el objetivo de la cámara después de cambiar el zoom, centrando en el personaje."""
        player_row, player_col = self.current_position
        
        # Calcular el offset para centrar al jugador en la nueva vista
        # Asegurar que no se sale de los límites del tablero
        if self.view_size >= self.size:
            # Si la vista es más grande que el tablero, centrar el tablero
            target_offset_row = 0
            target_offset_col = 0
        else:
            # Centrar en el jugador
            target_offset_row = player_row - self.view_size // 2
            target_offset_col = player_col - self.view_size // 2
            
            # Asegurar que no sobrepasa los límites
            target_offset_row = max(0, min(target_offset_row, self.size - self.view_size))
            target_offset_col = max(0, min(target_offset_col, self.size - self.view_size))
        
        # Actualizar inmediatamente sin interpolación para que el zoom sea instantáneo
        self.camera_offset_row = float(target_offset_row)
        self.camera_offset_col = float(target_offset_col)
    
    async def run(self):
        running = True
        while running:
            # Actualizar fade de música si está activo
            self.update_fade()
            
            # Actualizar fade-in del viento
            if self.wind_fading_in:
                current_time = pygame.time.get_ticks()
                elapsed = current_time - self.wind_fade_start_time
                
                # Iniciar viento cuando termina la ráfaga (si no está sonando ya)
                if elapsed >= 8000 and self.current_music != 'viento':  # ~8s duración de ráfaga
                    if 'viento' in self.music_sounds:
                        self.current_music = 'viento'
                        self.music_channel.play(self.music_sounds['viento'], loops=-1)
                        self.music_channel.set_volume(0.0)  # Empezar desde silencio
                        print("[DEBUG] Música de viento iniciada")
                
                # Fade-in durante 20 segundos después de que empieza el viento
                if self.current_music == 'viento':
                    fade_elapsed = elapsed - 8000  # Tiempo desde que empezó el viento
                    if fade_elapsed < 20000:  # 20 segundos de fade-in
                        volume = (fade_elapsed / 20000.0)  # 0.0 a 1.0
                        self.music_channel.set_volume(volume)
                    else:
                        # Fade completo, volumen máximo
                        self.music_channel.set_volume(1.0)
                        self.wind_fading_in = False
                        print("[DEBUG] Fade-in de viento completado")
            
            # Actualizar sistema de pensamientos
            self.update_thought()
            
            # Actualizar volumen de música según distancia (solo durante el juego, no durante fade)
            if not self.showing_title and not self.intro_anim_active and not self.fading_out and not self.fading_in:
                self.update_music_volume_by_distance()
            
            # Reproducir sonidos ambientales aleatorios (solo durante el juego, no en pantalla de título)
            if not self.showing_title and self.ambient_sounds:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_ambient_sound_time > self.next_ambient_sound_delay:
                    # Seleccionar un sonido según probabilidades ponderadas
                    rand = random.random()
                    cumulative = 0
                    selected_sound = None
                    
                    for sound_name, weight in self.ambient_sound_weights.items():
                        cumulative += weight
                        if rand <= cumulative and sound_name in self.ambient_sounds:
                            selected_sound = self.ambient_sounds[sound_name]
                            break
                    
                    if selected_sound:
                        selected_sound.play()
                    
                    self.last_ambient_sound_time = current_time
                    # Próximo sonido en 5-15 segundos
                    self.next_ambient_sound_delay = random.randint(5000, 15000)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    # Si estamos pidiendo confirmación de salida del juego
                    if self.asking_exit_confirmation:
                        if event.key == pygame.K_s:  # Sí, salir
                            running = False
                        elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:  # No, cancelar
                            self.asking_exit_confirmation = False
                        continue
                    
                    # Si estamos pidiendo confirmación para volver al menú principal
                    if self.asking_main_menu_confirmation:
                        if event.key == pygame.K_s:  # Sí, volver al menú
                            # Resetear el juego al menú principal
                            self.showing_title = True
                            self.asking_main_menu_confirmation = False
                            # Detener música
                            if REFACTORED_MODULES:
                                self.audio.stop_music()
                            else:
                                self.music_channel.stop()
                            # Cancelar cualquier pensamiento activo
                            if REFACTORED_MODULES and self.audio.thought_active:
                                self.audio.cancel_thought()
                        elif event.key == pygame.K_n or event.key == pygame.K_ESCAPE:  # No, cancelar
                            self.asking_main_menu_confirmation = False
                        continue
                    
                    # Si estamos en la pantalla de título, cualquier tecla excepto ESC inicia el juego
                    if self.showing_title:
                        if event.key == pygame.K_ESCAPE:
                            # ESC en pantalla principal sale del juego
                            running = False
                        else:
                            # Cualquier otra tecla inicia el juego
                            self.showing_title = False
                            self.intro_anim_active = True
                            self.intro_anim_start_time = pygame.time.get_ticks()
                        continue
                    
                    # Tecla ESC durante el juego
                    if event.key == pygame.K_ESCAPE:
                        # Si hay un pensamiento activo, cancelarlo
                        if REFACTORED_MODULES and self.audio.thought_active:
                            self.audio.cancel_thought()
                        # Si no hay pensamiento, preguntar si volver al menú principal
                        elif not (REFACTORED_MODULES and self.audio.thought_active):
                            self.asking_main_menu_confirmation = True
                        continue
                    
                    # Toggle auto reveal mode con F2
                    if event.key == pygame.K_F2:
                        self.auto_reveal_mode = not self.auto_reveal_mode
                    # Toggle debug mode con F3
                    elif event.key == pygame.K_F3:
                        self.debug_mode = not self.debug_mode
                    # Toggle mostrar camino con F4
                    elif event.key == pygame.K_F4:
                        self.show_path = not self.show_path
                    # Toggle oscurecimiento de líneas con F5
                    elif event.key == pygame.K_F5:
                        self.toggle_lines_darkening()
                    # Zoom in con Z
                    elif event.key == pygame.K_z:
                        self.zoom_in()
                    # Zoom out con X
                    elif event.key == pygame.K_x:
                        self.zoom_out()
                    else:
                        # Bloquear movimiento durante la animación de introducción
                        if self.intro_anim_active:
                            continue
                        
                        # Expect an arrow key to move in that direction
                        dir_map = {
                            pygame.K_UP: Direction.N,
                            pygame.K_DOWN: Direction.S,
                            pygame.K_RIGHT: Direction.E,
                            pygame.K_LEFT: Direction.O,
                            pygame.K_w: Direction.N,
                            pygame.K_s: Direction.S,
                            pygame.K_d: Direction.E,
                            pygame.K_a: Direction.O,
                        }

                        if event.key in dir_map:
                            self.place_cell_in_direction(dir_map[event.key])
            self.draw()
            self.clock.tick(60)
            await asyncio.sleep(0)  # Yield control to browser
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    import asyncio
    dungeon = DungeonBoard()
    asyncio.run(dungeon.run())