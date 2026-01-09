import pygame
import random
import math
import sys
import os
import asyncio
from enum import Enum
from dataclasses import dataclass

# Importar módulos refactorizados
from services.lighting_system import LightingSystem
from services.audio_manager import AudioManager
from rendering.decorations import DecorationRenderer
from rendering.effects import EffectsRenderer

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
    def __init__(self, *args, **kwargs):
        print("=== INICIO DungeonBoard ===")
        # ...existing code...
        # El resto del constructor sigue igual
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
        # Diccionario para guardar el número de antorchas adyacentes conectadas por dirección al entrar por primera vez
        self.adjacent_torch_counts_by_dir = {}
        
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
        
        # Obtener directorio del script para rutas relativas
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Sistema de iluminación y renderizado
        self.lighting = LightingSystem()
        self.decorations = DecorationRenderer(self.screen, self.cell_size)
        self.effects = EffectsRenderer(self.screen, self.cell_size)
        self.audio = AudioManager()

        self.was_active = False
                    
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
        self.zoom_out_count = 0  # Contador de zoom outs realizados
        self.zoom_out_triggered = False  # Flag para evitar múltiples zoom outs
        self.wind_fade_start_time = 0  # Tiempo de inicio del fade-in del viento
        self.wind_fading_in = False  # Flag para el fade-in del viento
        
        # Sonido de abominacion (para el pensamiento de la salida)
        self.abominacion_sound = None
        try:
            self.abominacion_sound = pygame.mixer.Sound(os.path.join(script_dir, "sound/abominacion.ogg"))
            self.abominacion_sound.set_volume(0.8)
        except pygame.error as e:
            print(f"No se pudo cargar sound/abominacion.ogg: {e}")
        
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
        self.exit_thought_active = False  # Flag para saber si estamos en el pensamiento de salida
        self.exit_image = None
        self.torch_image = None
        self.blood_image = None
        self.audio.thought_image = None  # Imagen actual del pensamiento (separada de exit_image)
        self.audio.thought_image_shown = False
        self.audio.thought_image_start_time = 0
        self.torches_extinguished = False  # Flag para apagar antorchas después de la losa
        
        # Cargar imagen de losa (salida)
        try:
            original_image = pygame.image.load(os.path.join(script_dir, "images/losa.png"))
            # Escalar manteniendo la proporción para que quepa en la pantalla
            max_width = self.width * 0.9
            # Reservar 120px en la parte inferior para subtítulos
            max_height = (self.height - 120) * 0.9
            
            scale_width = max_width / original_image.get_width()
            scale_height = max_height / original_image.get_height()
            scale = min(scale_width, scale_height)  # Usar la escala menor para mantener proporción
            
            new_width = int(original_image.get_width() * scale)
            new_height = int(original_image.get_height() * scale)
            
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
        
        # Detección de entorno web y limpieza de eventos iniciales
        self.is_web = hasattr(sys, 'platform') and 'emscripten' in sys.platform.lower()
        
        # Limpiar cualquier tecla presionada durante la carga (antes del título)
        if self.is_web:
            pygame.event.clear()
            print("[DEBUG] Modo web detectado - eventos iniciales limpiados")
    
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
        if self.audio.showing_image and self.audio.image_surface:
            # Centrar la imagen en la pantalla
            image_x = (self.width - self.audio.image_surface.get_width()) // 2
            image_y = (self.height - self.audio.image_surface.get_height()) // 2
            self.screen.blit(self.audio.image_surface, (image_x, image_y))
        
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
    
    def draw_subtitles(self):
        """Dibuja los subtítulos en la parte inferior de la pantalla."""
        if not self.audio.showing_subtitles:
            return
        
        # Los threads manejan automáticamente la expiración de subtítulos
        # Solo dibujamos lo que el AudioManager nos indica
        
        # Dividir el texto en líneas que quepan en el ancho del juego
        font = pygame.font.Font(None, 32)
        max_width = self.width - 40  # Margen de 20px a cada lado
        words = self.audio.subtitle_text.split(' ')
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
            
            # Debug en web
            if self.is_web and elapsed % 1000 < 50:  # Log cada segundo aproximadamente
                print(f"[DEBUG WEB] Intro anim - elapsed: {elapsed}ms")
            
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
                if self.is_web:
                    print("[DEBUG WEB] Intro anim completada")
                
                # Activar pensamiento de intro cuando el personaje entra en el calabozo
                if not self.intro_thought_triggered and self.audio.intro_sound:
                    # Duración de intro.ogg: 0 = auto (duración del audio)
                    self.audio.trigger_thought(
                        sounds=[(self.audio.intro_sound, 0)],
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
        should_light = False
        if self.show_path and (board_row, board_col) in self.main_path:
            should_reveal_for_path = True
        else:
            # Verificar si es adyacente a alguna celda del camino
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                adj_row, adj_col = board_row + dr, board_col + dc
                if (adj_row, adj_col) in self.main_path and (adj_row, adj_col) in self.visited_cells:
                    # Verificar si hay una salida desde la celda del camino hacia esta celda
                    adj_cell = self.board[adj_row][adj_col]
                    # Determinar la dirección desde la celda adyacente hacia esta celda
                    if dr == -1:  # vecino arriba mira hacia abajo (S)
                        if Direction.S in adj_cell.exits:
                            should_light = True
                            break
                    elif dr == 1:  # vecino abajo mira hacia arriba (N)
                        if Direction.N in adj_cell.exits:
                            should_light = True
                            break
                    elif dc == -1:  # vecino izquierda mira hacia derecha (E)
                        if Direction.E in adj_cell.exits:
                            should_light = True
                            break
                    elif dc == 1:  # vecino derecha mira hacia izquierda (O)
                        if Direction.O in adj_cell.exits:
                            should_light = True
                            break
        
        # Si la celda no ha sido visitada, dibujar niebla negra
        # EXCEPCIÓN: Si show_path está activo y debe revelarse, mostrarla
        if (board_row, board_col) not in self.visited_cells:
            if should_reveal_for_path:
                pass  # Continuar con el renderizado normal pero con overlay
            elif should_light:
                # Calcular número de antorchas para iluminación
                torch_count = self.count_torches(board_row, board_col, cell)
                base_brightness = 10
                torch_brightness = min(130, torch_count * 31)
                brightness = max(0, base_brightness + torch_brightness) // 2
                color = (brightness, brightness, brightness)
                # Detectar dirección de la luz
                for dr, dc, direction in [(-1, 0, Direction.N), (1, 0, Direction.S), (0, 1, Direction.E), (0, -1, Direction.O)]:
                    adj_row, adj_col = board_row + dr, board_col + dc
                    if (adj_row, adj_col) in self.main_path and (adj_row, adj_col) in self.visited_cells:
                        adj_cell = self.board[adj_row][adj_col]
                        if (direction == Direction.N and Direction.S in adj_cell.exits) or \
                           (direction == Direction.S and Direction.N in adj_cell.exits) or \
                           (direction == Direction.E and Direction.O in adj_cell.exits) or \
                           (direction == Direction.O and Direction.E in adj_cell.exits):
                            # Crear gradiente en la dirección correspondiente
                            overlay = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
                            for i in range(self.cell_size):
                                # Interpolación lineal del color
                                t = i / self.cell_size
                                grad_color = (
                                    int(color[0] * (1-t)),
                                    int(color[1] * (1-t)),
                                    int(color[2] * (1-t)),
                                    255
                                )
                                if direction == Direction.N:
                                    pygame.draw.line(overlay, grad_color, (0, i), (self.cell_size, i))
                                elif direction == Direction.S:
                                    pygame.draw.line(overlay, grad_color, (0, self.cell_size-1-i), (self.cell_size, self.cell_size-1-i))
                                elif direction == Direction.E:
                                    pygame.draw.line(overlay, grad_color, (self.cell_size-1-i, 0), (self.cell_size-1-i, self.cell_size))
                                elif direction == Direction.O:
                                    pygame.draw.line(overlay, grad_color, (i, 0), (i, self.cell_size))
                            self.screen.blit(overlay, (x, y))
                            break
                return
            else:
                pygame.draw.rect(self.screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size))
                return
        
        # Color / textura based on type
        torch_by_dir = getattr(cell, 'adjacent_torch_counts_by_dir', {})
        if cell.cell_type == CellType.EMPTY:
            # Pared negra (EMPTY debe verse negra)
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size))
            # Borde visible en gris para las celdas vacías
            pygame.draw.rect(self.screen, (90, 90, 90), (x, y, self.cell_size, self.cell_size), 3)
            # Iluminación por borde según antorchas adyacentes conectadas (depuración)
            for dir, count in torch_by_dir.items():
                if count > 0:
                    if dir == Direction.N:
                        color = (255, 0, 0)
                    elif dir == Direction.S:
                        color = (0, 255, 0)
                    elif dir == Direction.E:
                        color = (0, 0, 255)
                    elif dir == Direction.O:
                        color = (255, 255, 0)
                    else:
                        color = (255, 255, 255)
                    pygame.draw.rect(self.screen, color, (
                        x if dir != Direction.E else x + self.cell_size - self.cell_size // 5,
                        y if dir != Direction.S else y + self.cell_size - self.cell_size // 5,
                        self.cell_size if dir in [Direction.N, Direction.S] else self.cell_size // 5,
                        self.cell_size // 5 if dir in [Direction.N, Direction.S] else self.cell_size
                    ))
        elif cell.cell_type == CellType.INICIO:
            # Calcular número de antorchas para iluminación
            torch_count = self.count_torches(board_row, board_col, cell)
            # En el inicio, el brillo base es bajo (oscuro) independientemente de la distancia
            base_brightness = 10
            torch_brightness = min(130, torch_count * 31)
            brightness = max(0, base_brightness + torch_brightness)
            floor_color = (brightness, brightness, brightness)
            # Calcular factor de brillo para aplicar a todos los elementos (0.0 a 1.0)
            brightness_factor = brightness / 255.0
            # Inicio es como una habitación: fondo con iluminación
            pygame.draw.rect(self.screen, floor_color, (x, y, self.cell_size, self.cell_size))
            # Marco del inicio en gris oscurecido
            marco_color = tuple(int(120 * brightness_factor) for _ in range(3))
            pygame.draw.rect(self.screen, marco_color, (x, y, self.cell_size, self.cell_size), 3)
            # Iluminación por borde según antorchas adyacentes conectadas (depuración)
            for dir, count in torch_by_dir.items():
                if count > 0:
                    if dir == Direction.N:
                        color = (255, 0, 0)
                    elif dir == Direction.S:
                        color = (0, 255, 0)
                    elif dir == Direction.E:
                        color = (0, 0, 255)
                    elif dir == Direction.O:
                        color = (255, 255, 0)
                    else:
                        color = (255, 255, 255)
                    pygame.draw.rect(self.screen, color, (
                        x if dir != Direction.E else x + self.cell_size - self.cell_size // 5,
                        y if dir != Direction.S else y + self.cell_size - self.cell_size // 5,
                        self.cell_size if dir in [Direction.N, Direction.S] else self.cell_size // 5,
                        self.cell_size // 5 if dir in [Direction.N, Direction.S] else self.cell_size
                    ))
            # Dibujar textura de piedra en las paredes
            self.effects.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor, self.count_torches)
        elif cell.cell_type == CellType.PASILLO:
            torch_count = self.count_torches(board_row, board_col, cell)
            # Calcular oscurecimiento basado en distancia desde la entrada
            start_row, start_col = self.start_position
            exit_row, exit_col = self.exit_position
            distance_from_start = abs(start_row - board_row) + abs(start_col - board_col)
            total_distance = abs(exit_row - start_row) + abs(exit_col - start_col)
            if total_distance > 0:
                progress = distance_from_start / total_distance
            else:
                progress = 0.5
            base_brightness = int(20 * (1.0 - progress))
            torch_brightness = min(130, torch_count * 31)
            brightness = max(0, base_brightness + torch_brightness)
            floor_color = (brightness, brightness, brightness)
            brightness_factor = brightness / 255.0
            pygame.draw.rect(self.screen, floor_color, (x, y, self.cell_size, self.cell_size))
            marco_color = tuple(int(120 * brightness_factor) for _ in range(3))
            pygame.draw.rect(self.screen, marco_color, (x, y, self.cell_size, self.cell_size), 3)
            for dir, count in torch_by_dir.items():
                if count > 0:
                    if dir == Direction.N:
                        color = (255, 0, 0)
                    elif dir == Direction.S:
                        color = (0, 255, 0)
                    elif dir == Direction.E:
                        color = (0, 0, 255)
                    elif dir == Direction.O:
                        color = (255, 255, 0)
                    else:
                        color = (255, 255, 255)
                    pygame.draw.rect(self.screen, color, (
                        x if dir != Direction.E else x + self.cell_size - self.cell_size // 5,
                        y if dir != Direction.S else y + self.cell_size - self.cell_size // 5,
                        self.cell_size if dir in [Direction.N, Direction.S] else self.cell_size // 5,
                        self.cell_size // 5 if dir in [Direction.N, Direction.S] else self.cell_size
                    ))
            self.effects.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor, self.count_torches)
            # Las líneas se dibujan más adelante (después de las piedras, antes de la sangre)
        elif cell.cell_type == CellType.HABITACION:
            torch_count = self.count_torches(board_row, board_col, cell)
            start_row, start_col = self.start_position
            exit_row, exit_col = self.exit_position
            distance_from_start = abs(start_row - board_row) + abs(start_col - board_col)
            total_distance = abs(exit_row - start_row) + abs(exit_col - start_col)
            if total_distance > 0:
                progress = distance_from_start / total_distance
            else:
                progress = 0.5
            base_brightness = int(20 * (1.0 - progress))
            torch_brightness = min(130, torch_count * 31)
            brightness = max(0, base_brightness + torch_brightness)
            floor_color = (brightness, brightness, brightness)
            brightness_factor = brightness / 255.0
            pygame.draw.rect(self.screen, floor_color, (x, y, self.cell_size, self.cell_size))
            marco_color = tuple(int(120 * brightness_factor) for _ in range(3))
            pygame.draw.rect(self.screen, marco_color, (x, y, self.cell_size, self.cell_size), 3)
            for dir, count in torch_by_dir.items():
                if count > 0:
                    if dir == Direction.N:
                        color = (255, 0, 0)
                    elif dir == Direction.S:
                        color = (0, 255, 0)
                    elif dir == Direction.E:
                        color = (0, 0, 255)
                    elif dir == Direction.O:
                        color = (255, 255, 0)
                    else:
                        color = (255, 255, 255)
                    pygame.draw.rect(self.screen, color, (
                        x if dir != Direction.E else x + self.cell_size - self.cell_size // 5,
                        y if dir != Direction.S else y + self.cell_size - self.cell_size // 5,
                        self.cell_size if dir in [Direction.N, Direction.S] else self.cell_size // 5,
                        self.cell_size // 5 if dir in [Direction.N, Direction.S] else self.cell_size
                    ))
            self.effects.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor, self.count_torches)
            # Las líneas se dibujan más adelante (después de las piedras, antes de la sangre)
        elif cell.cell_type == CellType.SALIDA:
            torch_count = self.count_torches(board_row, board_col, cell)
            base_brightness = 0
            torch_brightness = min(130, torch_count * 31)
            brightness = max(0, base_brightness + torch_brightness)
            room_color = (brightness, brightness, brightness)
            brightness_factor = brightness / 255.0
            pygame.draw.rect(self.screen, room_color, (x, y, self.cell_size, self.cell_size))
            for dir, count in torch_by_dir.items():
                if count > 0:
                    if dir == Direction.N:
                        color = (255, 0, 0)
                    elif dir == Direction.S:
                        color = (0, 255, 0)
                    elif dir == Direction.E:
                        color = (0, 0, 255)
                    elif dir == Direction.O:
                        color = (255, 255, 0)
                    else:
                        color = (255, 255, 255)
                    pygame.draw.rect(self.screen, color, (
                        x if dir != Direction.E else x + self.cell_size - self.cell_size // 5,
                        y if dir != Direction.S else y + self.cell_size - self.cell_size // 5,
                        self.cell_size if dir in [Direction.N, Direction.S] else self.cell_size // 5,
                        self.cell_size // 5 if dir in [Direction.N, Direction.S] else self.cell_size
                    ))
            self.effects.draw_stone_in_walls(board_row, board_col, x, y, cell, brightness_factor, self.count_torches)
            # Dibuja una losa más estrecha, más oscura y con rayitas negras
            losa_w = int(self.cell_size * 0.28)
            losa_h = int(self.cell_size * 0.16)
            losa_x = x + (self.cell_size - losa_w) // 2
            losa_y = y + self.cell_size // 2 + int(self.cell_size * 0.13)
            losa_color = (90, 90, 90)
            borde_color = (60, 60, 60)
            pygame.draw.rect(self.screen, losa_color, (losa_x, losa_y, losa_w, losa_h))
            pygame.draw.rect(self.screen, borde_color, (losa_x, losa_y, losa_w, losa_h), 2)
            # Rayitas negras simulando inscripción
            n_rayas = 4
            for i in range(n_rayas):
                ry = losa_y + int(losa_h * (0.25 + 0.15 * i))
                pygame.draw.line(self.screen, (20, 20, 20), (losa_x + 6, ry), (losa_x + losa_w - 6, ry), 1)
        
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
            if self.lighting.lines_darkening_enabled:
                lines_brightness_factor = base_brightness / 255.0
            else:
                lines_brightness_factor = 1.0  # Sin oscurecimiento
        elif cell.cell_type == CellType.INICIO:
            # En inicio, usar el mismo brillo base que tendría si estuviera en el camino (50)
            # porque está en la posición más alejada de la salida
            if self.lighting.lines_darkening_enabled:
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
                if self.lighting.lines_darkening_enabled:
                    self.effects.draw_broken_line(inner_color, (mid_x_L, center_y_D), (mid_x_L, y + 0.1*self.cell_size), 3, board_row, board_col, 1)
                    self.effects.draw_broken_line(inner_color, (mid_x_R, center_y_D), (mid_x_R, y + 0.1*self.cell_size), 3, board_row, board_col, 2)
                else:
                    pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_D), (mid_x_L, y + 0.1*self.cell_size), 3)
                    pygame.draw.line(self.screen, inner_color, (mid_x_R, center_y_D), (mid_x_R, y + 0.1*self.cell_size), 3)
            else:
                # Cerrar el norte si no hay salida (siempre gris oscuro)
                if self.lighting.lines_darkening_enabled:
                    self.effects.draw_broken_line(inner_color, (mid_x_L, center_y_D), (mid_x_R, center_y_D), 3, board_row,  board_col, 3)
                else:
                    pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_D), (mid_x_R, center_y_D), 3)
            
            # South
            if Direction.S in cell.exits:
                if self.lighting.lines_darkening_enabled:
                    self.effects.draw_broken_line(inner_color, (mid_x_L, center_y_U), (mid_x_L, y + 0.9*self.cell_size), 3, board_row, board_col, 4)
                    self.effects.draw_broken_line(inner_color, (mid_x_R, center_y_U), (mid_x_R, y + 0.9*self.cell_size), 3, board_row, board_col, 5)
                else:
                    pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_U), (mid_x_L, y + 0.9*self.cell_size), 3)
                    pygame.draw.line(self.screen, inner_color, (mid_x_R, center_y_U), (mid_x_R, y + 0.9*self.cell_size), 3)
            else:
                # Cerrar el sur si no hay salida (siempre gris oscuro)
                if self.lighting.lines_darkening_enabled:
                    self.effects.draw_broken_line(inner_color, (mid_x_L, center_y_U), (mid_x_R, center_y_U), 3, board_row, board_col, 6)
                else:
                    pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_U), (mid_x_R, center_y_U), 3)
            
            # East
            if Direction.E in cell.exits:
                if self.lighting.lines_darkening_enabled:
                    self.effects.draw_broken_line(inner_color, (center_x_R, mid_y_D), (x + 0.9*self.cell_size, mid_y_D), 3, board_row, board_col, 7)
                    self.effects.draw_broken_line(inner_color, (center_x_R, mid_y_U), (x + 0.9*self.cell_size, mid_y_U), 3, board_row, board_col, 8)
                else:
                    pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_D), (x + 0.9*self.cell_size, mid_y_D), 3)
                    pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_U), (x + 0.9*self.cell_size, mid_y_U), 3)
            else:
                # Cerrar el este si no hay salida (siempre gris oscuro)
                if self.lighting.lines_darkening_enabled:
                    self.effects.draw_broken_line(inner_color, (center_x_R, mid_y_D), (center_x_R, mid_y_U), 3, board_row, board_col, 9)
                else:
                    pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_D), (center_x_R, mid_y_U), 3)
            
            # West
            if Direction.O in cell.exits:
                if self.lighting.lines_darkening_enabled:
                    self.effects.draw_broken_line(inner_color, (center_x_L, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 3, board_row, board_col, 10)
                    self.effects.draw_broken_line(inner_color, (center_x_L, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 3, board_row, board_col, 11)
                else:
                    pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 3)
                    pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 3)
            else:
                # Cerrar el oeste si no hay salida (siempre gris oscuro)
                if self.lighting.lines_darkening_enabled:
                    self.effects.draw_broken_line(inner_color, (center_x_L, mid_y_D), (center_x_L, mid_y_U), 3, board_row, board_col, 12)
                else:
                    pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_D), (center_x_L, mid_y_U), 3)
        
        # Draw exits
        if cell.cell_type != CellType.EMPTY:
            self.draw_exits(board_row, board_col, x, y, cell.exits, cell.cell_type, lines_brightness_factor)
        
        # Dibujar manchas de sangre después de las líneas
        if cell.cell_type in [CellType.PASILLO, CellType.HABITACION]:
            self.decorations.draw_blood_stains(board_row, board_col, x, y, brightness_factor, self.exit_position)
        elif cell.cell_type == CellType.SALIDA:
            self.decorations.draw_blood_stains(board_row, board_col, x, y, brightness_factor, self.exit_position)
        
        # Dibujar fuente y escaleras después de la sangre
        if cell.cell_type == CellType.INICIO:
            self.decorations.draw_fountain(x, y)
        elif cell.cell_type == CellType.SALIDA:
            self.decorations.draw_spiral_stairs(x, y)
            
        # Dibujar antorchas al final (encima de todo)
        # SOLO en celdas visitadas (no en celdas reveladas pero no visitadas)
        if (board_row, board_col) in self.visited_cells:
            if cell.cell_type in [CellType.INICIO, CellType.PASILLO, CellType.HABITACION, CellType.SALIDA]:
                num_torches = self.count_torches(board_row, board_col, cell)
                self.decorations.draw_torches(board_row, board_col, x, y, cell, num_torches)
    
    def draw_exits(self, row,  col, x, y, exits, cell_type, brightness_factor: float = 1.0):

        # --- Variables y funciones auxiliares internas ---
        delta = {
            Direction.N: (-1, 0),
            Direction.S: (1, 0),
            Direction.E: (0, 1),
            Direction.O: (0, -1),
        }

        def neighbor_coords(dir_: Direction):
            dr, dc = delta[dir_]
            return row + dr, col + dc

        def get_floor_color_for_cell(board_row, board_col):
            cell = self.board[board_row][board_col]
            if cell.cell_type == CellType.EMPTY:
                return (0, 0, 0)
            elif cell.cell_type == CellType.INICIO:
                torch_count = self.count_torches(board_row, board_col, cell)
                base_brightness = 10
                torch_brightness = min(130, torch_count * 31)
                brightness = max(0, base_brightness + torch_brightness)
                return (brightness, brightness, brightness)
            elif cell.cell_type in [CellType.PASILLO, CellType.HABITACION]:
                torch_count = self.count_torches(board_row, board_col, cell)
                start_row, start_col = self.start_position
                exit_row, exit_col = self.exit_position
                distance_from_start = abs(start_row - board_row) + abs(start_col - board_col)
                total_distance = abs(exit_row - start_row) + abs(exit_col - start_col)
                if total_distance > 0:
                    progress = distance_from_start / total_distance
                else:
                    progress = 0.5
                base_brightness = int(20 * (1.0 - progress))
                torch_brightness = min(130, torch_count * 31)
                brightness = max(0, base_brightness + torch_brightness)
                return (brightness, brightness, brightness)
            elif cell.cell_type == CellType.SALIDA:
                torch_count = self.count_torches(board_row, board_col, cell)
                base_brightness = 0
                torch_brightness = min(130, torch_count * 31)
                brightness = max(0, base_brightness + torch_brightness)
                return (brightness, brightness, brightness)
            else:
                return (0, 0, 0)

        def draw_floor_connection(direction):
            nr, nc = neighbor_coords(direction)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY and self.get_opposite_direction(direction) in neighbor.exits:
                    color1 = get_floor_color_for_cell(row, col)
                    color2 = get_floor_color_for_cell(nr, nc)
                    avg_color = tuple((c1 + c2) // 2 for c1, c2 in zip(color1, color2))
                    rect_thickness = int(self.cell_size * 0.22)
                    if direction == Direction.N:
                        rect = (x + self.cell_size * 0.28, y, self.cell_size * 0.44, rect_thickness)
                    elif direction == Direction.S:
                        rect = (x + self.cell_size * 0.28, y + self.cell_size - rect_thickness, self.cell_size * 0.44, rect_thickness)
                    elif direction == Direction.E:
                        rect = (x + self.cell_size - rect_thickness, y + self.cell_size * 0.28, rect_thickness, self.cell_size * 0.44)
                    elif direction == Direction.O:
                        rect = (x, y + self.cell_size * 0.28, rect_thickness, self.cell_size * 0.44)
                    else:
                        return
                    pygame.draw.rect(self.screen, avg_color, rect)

        side_circle_radius = int(self.cell_size * 0.08)
        side_circle_offset = int(self.cell_size * 0.03)
        side_circle_color = (220, 220, 220)

        def draw_side_circle(direction):
            if direction == Direction.N:
                pos = (x + self.cell_size // 2, y + side_circle_offset)
            elif direction == Direction.S:
                pos = (x + self.cell_size // 2, y + self.cell_size - side_circle_offset)
            elif direction == Direction.E:
                pos = (x + self.cell_size - side_circle_offset, y + self.cell_size // 2)
            elif direction == Direction.O:
                pos = (x + side_circle_offset, y + self.cell_size // 2)
            else:
                return
            pygame.draw.circle(self.screen, side_circle_color, pos, side_circle_radius)

        # --- Dibujo de conexiones y círculos de borde ---
        for direction in [Direction.N, Direction.S, Direction.E, Direction.O]:
            if direction in exits:
                draw_floor_connection(direction)
                draw_side_circle(direction)

        # --- Dibujo de líneas y agujeros de salida (resto de la función original) ---
        exit_size = 5
        mid_x_L = x + 0.8*self.cell_size // 2
        mid_x_R = x + 1.2*self.cell_size // 2
        mid_y_D = y + 0.8*self.cell_size // 2
        mid_y_U = y + 1.2*self.cell_size // 2
        exit_color = (0, 0, 0)
        exit_thickness = 8
        hole_radius = int(self.cell_size * 0.13)
        hole_centers = {
            Direction.N: (x + self.cell_size // 2, y + int(0.07 * self.cell_size)),
            Direction.S: (x + self.cell_size // 2, y + int(0.93 * self.cell_size)),
            Direction.E: (x + int(0.93 * self.cell_size), y + self.cell_size // 2),
            Direction.O: (x + int(0.07 * self.cell_size), y + self.cell_size // 2),
        }

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

            # Dibuja la línea negra gruesa
            if self.lighting.lines_darkening_enabled and cell_type != CellType.SALIDA:
                self.effects.draw_broken_line(exit_color, (mid_x_L, y), (mid_x_L, y + 0.1*self.cell_size), exit_thickness, row, col, 20)
                self.effects.draw_broken_line(exit_color, (mid_x_R, y), (mid_x_R, y + 0.1*self.cell_size), exit_thickness, row, col, 21)
            else:
                pygame.draw.line(self.screen, exit_color, (mid_x_L, y), (mid_x_L, y + 0.1*self.cell_size), exit_thickness)
                pygame.draw.line(self.screen, exit_color, (mid_x_R, y), (mid_x_R, y + 0.1*self.cell_size), exit_thickness)
            # Dibuja el círculo con el color promedio si conecta dos celdas, negro si da al vacío
            nr, nc = neighbor_coords(Direction.N)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY and self.get_opposite_direction(Direction.N) in neighbor.exits:
                    color1 = get_floor_color_for_cell(row, col)
                    color2 = get_floor_color_for_cell(nr, nc)
                    avg_color = tuple((c1 + c2) // 2 for c1, c2 in zip(color1, color2))
                    pygame.draw.circle(self.screen, avg_color, hole_centers[Direction.N], hole_radius)
                else:
                    pygame.draw.circle(self.screen, (0, 0, 0), hole_centers[Direction.N], hole_radius)
            else:
                pygame.draw.circle(self.screen, (0, 0, 0), hole_centers[Direction.N], hole_radius)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar la salida en negro
            if is_at_edge(Direction.N) or (not connected and not neighbor_empty):
                if self.lighting.lines_darkening_enabled and cell_type != CellType.SALIDA:
                    self.effects.draw_broken_line((0, 0, 0), (mid_x_L, y + 0.05*self.cell_size), (mid_x_R, y + 0.05*self.cell_size), exit_thickness, row, col, 22)
                else:
                    pygame.draw.line(self.screen, (0, 0, 0), (mid_x_L, y + 0.05*self.cell_size), (mid_x_R, y + 0.05*self.cell_size), exit_thickness)

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

            # Dibuja la línea negra gruesa
            if self.lighting.lines_darkening_enabled and cell_type != CellType.SALIDA:
                self.effects.draw_broken_line(exit_color, (mid_x_L, y + self.cell_size), (mid_x_L, y + 0.8*self.cell_size), exit_thickness, row, col, 30)
                self.effects.draw_broken_line(exit_color, (mid_x_R, y + self.cell_size), (mid_x_R, y + 0.8*self.cell_size), exit_thickness, row, col, 31)
            else:
                pygame.draw.line(self.screen, exit_color, (mid_x_L, y + self.cell_size), (mid_x_L, y + 0.8*self.cell_size), exit_thickness)
                pygame.draw.line(self.screen, exit_color, (mid_x_R, y + self.cell_size), (mid_x_R, y + 0.8*self.cell_size), exit_thickness)
            # Dibuja el círculo con el color promedio si conecta dos celdas, negro si da al vacío
            nr, nc = neighbor_coords(Direction.S)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY and self.get_opposite_direction(Direction.S) in neighbor.exits:
                    color1 = get_floor_color_for_cell(row, col)
                    color2 = get_floor_color_for_cell(nr, nc)
                    avg_color = tuple((c1 + c2) // 2 for c1, c2 in zip(color1, color2))
                    pygame.draw.circle(self.screen, avg_color, hole_centers[Direction.S], hole_radius)
                else:
                    pygame.draw.circle(self.screen, (0, 0, 0), hole_centers[Direction.S], hole_radius)
            else:
                pygame.draw.circle(self.screen, (0, 0, 0), hole_centers[Direction.S], hole_radius)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.S) or (not connected and not neighbor_empty):
                if self.lighting.lines_darkening_enabled and cell_type != CellType.SALIDA:
                    self.effects.draw_broken_line((0, 0, 0), (mid_x_L, y + self.cell_size - 0.05*self.cell_size), (mid_x_R, y + self.cell_size - 0.05*self.cell_size), exit_thickness, row, col, 32)
                else:
                    pygame.draw.line(self.screen, (0, 0, 0), (mid_x_L, y + self.cell_size - 0.05*self.cell_size), (mid_x_R, y + self.cell_size - 0.05*self.cell_size), exit_thickness)

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

            # Dibuja la línea negra gruesa
            if self.lighting.lines_darkening_enabled and cell_type != CellType.SALIDA:
                self.effects.draw_broken_line(exit_color, (x + self.cell_size, mid_y_D), (x + 0.8*self.cell_size, mid_y_D), exit_thickness, row, col, 40)
                self.effects.draw_broken_line(exit_color, (x + self.cell_size, mid_y_U), (x + 0.8*self.cell_size, mid_y_U), exit_thickness, row, col, 41)
            else:
                pygame.draw.line(self.screen, exit_color, (x + self.cell_size, mid_y_D), (x + 0.8*self.cell_size, mid_y_D), exit_thickness)
                pygame.draw.line(self.screen, exit_color, (x + self.cell_size, mid_y_U), (x + 0.8*self.cell_size, mid_y_U), exit_thickness)
            # Dibuja el círculo con el color promedio si conecta dos celdas, negro si da al vacío
            nr, nc = neighbor_coords(Direction.E)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY and self.get_opposite_direction(Direction.E) in neighbor.exits:
                    color1 = get_floor_color_for_cell(row, col)
                    color2 = get_floor_color_for_cell(nr, nc)
                    avg_color = tuple((c1 + c2) // 2 for c1, c2 in zip(color1, color2))
                    pygame.draw.circle(self.screen, avg_color, hole_centers[Direction.E], hole_radius)
                else:
                    pygame.draw.circle(self.screen, (0, 0, 0), hole_centers[Direction.E], hole_radius)
            else:
                pygame.draw.circle(self.screen, (0, 0, 0), hole_centers[Direction.E], hole_radius)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.E) or (not connected and not neighbor_empty):
                if self.lighting.lines_darkening_enabled and cell_type != CellType.SALIDA:
                    self.effects.draw_broken_line((0, 0, 0), (x + self.cell_size - 0.05*self.cell_size, mid_y_D), (x + self.cell_size - 0.05*self.cell_size, mid_y_U), exit_thickness, row, col, 42)
                else:
                    pygame.draw.line(self.screen, (0, 0, 0), (x + self.cell_size - 0.05*self.cell_size, mid_y_D), (x + self.cell_size - 0.05*self.cell_size, mid_y_U), exit_thickness)

        # East (complementaria)
        if Direction.E not in exits:
            nr, nc = neighbor_coords(Direction.E)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.E)
                    if opposite in neighbor.exits:
                        neighbor_x = nc * self.cell_size
                        neighbor_mid_y_D = nr * selfcell_size + 0.8*self.cell_size // 2
                        neighbor_mid_y_U = nr * selfcell_size + 1.2*self.cell_size // 2
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

            # Dibuja la línea negra gruesa
            if self.lighting.lines_darkening_enabled and cell_type != CellType.SALIDA:
                self.effects.draw_broken_line(exit_color, (x, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), exit_thickness, row, col, 50)
                self.effects.draw_broken_line(exit_color, (x, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), exit_thickness, row, col, 51)
            else:
                pygame.draw.line(self.screen, exit_color, (x, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), exit_thickness)
                pygame.draw.line(self.screen, exit_color, (x, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), exit_thickness)
            # Dibuja el círculo con el color promedio si conecta dos celdas, negro si da al vacío
            nr, nc = neighbor_coords(Direction.O)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY and self.get_opposite_direction(Direction.O) in neighbor.exits:
                    color1 = get_floor_color_for_cell(row, col)
                    color2 = get_floor_color_for_cell(nr, nc)
                    avg_color = tuple((c1 + c2) // 2 for c1, c2 in zip(color1, color2))
                    pygame.draw.circle(self.screen, avg_color, hole_centers[Direction.O], hole_radius)
                else:
                    pygame.draw.circle(self.screen, (0, 0, 0), hole_centers[Direction.O], hole_radius)
            else:
                pygame.draw.circle(self.screen, (0, 0, 0), hole_centers[Direction.O], hole_radius)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.O) or (not connected and not neighbor_empty):
                if self.lighting.lines_darkening_enabled and cell_type != CellType.SALIDA:
                    self.effects.draw_broken_line((0, 0, 0), (x + 0.05*self.cell_size, mid_y_D), (x + 0.05*self.cell_size, mid_y_U), exit_thickness, row, col, 52)
                else:
                    pygame.draw.line(self.screen, (0, 0, 0), (x + 0.05*self.cell_size, mid_y_D), (x + 0.05*self.cell_size, mid_y_U), exit_thickness)

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

    def place_cell_in_direction(self, direction: Direction):
        """Coloca en la celda en la dirección `direction` desde la posición actual
        una celda aleatoria de tipo PASILLO o HABITACION (50/50) con salidas
        aleatorias (25% cada una) excepto la salida por la que se llegó.
        Si la celda ya existe (no es EMPTY), no la modifica.
        Si la celda destino está fuera del tablero o no existe salida en la celda
        actual, no hace nada.
        """
        # Bloquear movimiento durante pensamientos que bloquean movimiento
        if self.audio.thought_active and self.audio.thought_blocks_movement:
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
                # Calcular antorchas adyacentes conectadas por dirección
                cell = self.board[target_row][target_col]
                adj_torch_count_by_dir = {}
                for dir in [Direction.N, Direction.S, Direction.E, Direction.O]:
                    dr, dc = {Direction.N: (-1, 0), Direction.S: (1, 0), Direction.E: (0, 1), Direction.O: (0, -1)}[dir]
                    adj_row, adj_col = target_row + dr, target_col + dc
                    count = 0
                    if 0 <= adj_row < self.size and 0 <= adj_col < self.size:
                        adj_cell = self.board[adj_row][adj_col]
                        if dir in cell.exits and self.get_opposite_direction(dir) in adj_cell.exits:
                            count = self.count_torches(adj_row, adj_col, adj_cell)
                    adj_torch_count_by_dir[dir] = count
                print(f"[DEBUG] ({target_row},{target_col}) adj_torch_count_by_dir={adj_torch_count_by_dir}")
                self.adjacent_torch_counts_by_dir[(target_row, target_col)] = adj_torch_count_by_dir
                self.reveal_adjacent_cells(target_row, target_col)
                
                # POST-CHECK: Activar pensamientos DESPUÉS de entrar en la celda
                # Verificar si hay manchas de sangre en la celda actual
                if not self.blood_thought_triggered and self.blood_sound and self.has_blood_stains(target_row, target_col):
                    self.blood_thought_triggered = True

                    self.audio.thought_active = True
                    self.audio.thought_blocks_movement = True
                    
                    async def delayed_blood_thought():
                        await asyncio.sleep(1.0)  # Esperar 1 segundo
                        self.audio.trigger_thought(
                            sounds=[(self.blood_sound, 0)],
                            images=[(self.blood_image, 0)] if self.blood_image else None,
                            subtitles=[("¿Es eso... sangre?!?", 6000)],
                            blocks_movement=True
                        )
                    asyncio.create_task(delayed_blood_thought())
                    return  # BLOQUEAR ahora que ya entró
                
                # Verificar si hay antorchas en la celda actual
                # IMPORTANTE: Verificar tanto has_torches() como count_torches() > 0
                cell = self.board[target_row][target_col]
                if not self.torch_thought_triggered and self.torch_sound and self.has_torches(target_row, target_col) and self.count_torches(target_row, target_col, cell) > 0:
                    self.torch_thought_triggered = True

                    self.audio.thought_active = True
                    self.audio.thought_blocks_movement = True
                    
                    async def delayed_torch_thought():
                        await asyncio.sleep(1.0)  # Esperar 1 segundo
                        self.audio.trigger_thought(
                            sounds=[(self.torch_sound, 0)],
                            images=[(self.torch_image, 0)] if self.torch_image else None,
                            subtitles=[("Una antorcha encendida... ¡Interesante!", 6000)],
                            blocks_movement=True
                        )
                    asyncio.create_task(delayed_torch_thought())
                    return  # BLOQUEAR ahora que ya entró
                
                # Verificar si entró en la celda final
                if (target_row, target_col) == self.exit_position and not self.exit_image_shown:
                    self.exit_image_shown = True
                    self.exit_image_start_time = pygame.time.get_ticks()
                    self.exit_thought_active = True  # Marcar que estamos en pensamiento de salida

                    async def delayed_exit_thought():
                        await asyncio.sleep(1.0)  # Esperar 1 segundo
                        if self.abominacion_sound:
                            # Calcular duración total: audio + 2 segundos
                            audio_duration = int(self.abominacion_sound.get_length() * 1000)
                            image_duration = audio_duration + 2000  # +2 segundos después del audio
                            self.audio.trigger_thought(
                                sounds=[(self.abominacion_sound, 0)],
                                images=[(self.exit_image, image_duration)] if self.exit_image else None,
                                subtitles=[("¿Qué es esta abominación?", image_duration)],
                                blocks_movement=True
                            )
                            print(f"[DEBUG] Pensamiento de salida activado - exit_thought_active={self.exit_thought_active}")
                    asyncio.create_task(delayed_exit_thought())
                    return  # BLOQUEAR ahora que ya entró
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
        # Calcular antorchas adyacentes conectadas por dirección
        cell = self.board[target_row][target_col]
        adj_torch_count_by_dir = {}
        for dir in [Direction.N, Direction.S, Direction.E, Direction.O]:
            dr, dc = {Direction.N: (-1, 0), Direction.S: (1, 0), Direction.E: (0, 1), Direction.O: (0, -1)}[dir]
            adj_row, adj_col = target_row + dr, target_col + dc
            count = 0
            if 0 <= adj_row < self.size and 0 <= adj_col < self.size:
                adj_cell = self.board[adj_row][adj_col]
                if dir in cell.exits and self.get_opposite_direction(dir) in adj_cell.exits:
                    count = self.count_torches(adj_row, adj_col, adj_cell)
            adj_torch_count_by_dir[dir] = count
        self.adjacent_torch_counts_by_dir[(target_row, target_col)] = adj_torch_count_by_dir
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
            
            # Después de 3 segundos, hacer zoom out 3 veces (una vez)
            if elapsed >= 3000 and not self.zoom_out_triggered:
                print("[DEBUG] Haciendo zoom out 3 veces")
                for _ in range(3):
                    self.zoom_out()
                self.zoom_out_triggered = True
            
            # Si ya pasó la duración del parpadeo (5 segundos), apagar definitivamente
            if elapsed >= self.flicker_duration:
                self.torches_flickering = False
                self.torches_extinguished = True
                print("[DEBUG] Antorchas apagadas definitivamente")
                
                # Restaurar el zoom original
                if hasattr(self, 'original_zoom_index'):
                    self.current_zoom_index = self.original_zoom_index
                    self.view_size = self.zoom_levels[self.current_zoom_index]
                    self.cell_size = self.fixed_window_size // self.view_size
                    self.update_camera_target()
                    print(f"[DEBUG] Zoom restaurado a nivel {self.original_zoom_index}")
                
                return 0
            
            # Parpadeo: alternar entre visible/invisible cada vez más rápido
            # Primeros 3 segundos: parpadeo lento (500ms)
            # Últimos 2 segundos: parpadeo rápido (100ms)
            if elapsed < 3000:
                flicker_interval = 500  # Parpadeo lento
            else:
                flicker_interval = 100  # Parpadeo rápido
            
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
        
        # VERIFICAR DISTANCIA MÍNIMA DESDE LA ENTRADA
        entrance_row, entrance_col = self.start_position
        distance_from_entrance = abs(entrance_row - board_row) + abs(entrance_col - board_col)
        if distance_from_entrance < 5:
            return 0  # No hay antorchas si está muy cerca de la entrada
        
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
    
    def has_torches(self, board_row, board_col):
        """Verifica si una celda tiene antorchas."""
        cell = self.board[board_row][board_col]
        
        # Las antorchas aparecen en pasillos, habitaciones y salida
        if cell.cell_type not in (CellType.PASILLO, CellType.HABITACION, CellType.SALIDA):
            return False
        
        # Solo en celdas a distancia mínima de 5 de la entrada
        entrance_row, entrance_col = self.start_position
        distance = abs(entrance_row - board_row) + abs(entrance_col - board_col)
        return distance >= 5
    
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
        
        # Definir posiciones para cada pared (N, S, E, O)
        wall_positions = {
            'N': [
                (x + int(self.cell_size * 0.18), y + wall_thickness // 2),  # esquina izq
                (x + int(self.cell_size * 0.82), y + wall_thickness // 2),  # esquina der
                (x + self.cell_size // 2, y + wall_thickness // 2)           # centro
            ],
            'S': [
                (x + int(self.cell_size * 0.18), y + self.cell_size - wall_thickness // 2),
                (x + int(self.cell_size * 0.82), y + self.cell_size - wall_thickness // 2),
                (x + self.cell_size // 2, y + self.cell_size - wall_thickness // 2)
            ],
            'E': [
                (x + self.cell_size - wall_thickness // 2, y + int(self.cell_size * 0.18)),
                (x + self.cell_size - wall_thickness // 2, y + int(self.cell_size * 0.82)),
                (x + self.cell_size - wall_thickness // 2, y + self.cell_size // 2)
            ],
            'O': [
                (x + wall_thickness // 2, y + int(self.cell_size * 0.18)),
                (x + wall_thickness // 2, y + int(self.cell_size * 0.82)),
                (x + wall_thickness // 2, y + self.cell_size // 2)
            ]
        }

        # Para cada pared, decidir si tiene salida o no
        torch_positions = []
        for dir_, dir_enum in zip(['N', 'S', 'E', 'O'], [Direction.N, Direction.S, Direction.E, Direction.O]):
            has_exit = dir_enum in cell.exits
            # Si tiene salida: solo esquinas
            if has_exit:
                # Elegir aleatoriamente una de las dos esquinas
                idx = rnd.choice([0, 1])
                torch_positions.append(wall_positions[dir_][idx])
            else:
                # Puede ir en una de las dos esquinas o en el centro
                idx = rnd.choice([0, 1, 2])
                torch_positions.append(wall_positions[dir_][idx])

        # Barajar las posiciones para que no siempre salgan en el mismo orden
        rnd.shuffle(torch_positions)
        # Dibujar antorchas en las últimas N posiciones (siempre las últimas)
        for i in range(-num_torches, 0):
            torch_x, torch_y = torch_positions[i]
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
        flame_radius = max(8, int(size * 0.6 * flicker))
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
            
            # Color del escalón (gris piedra)
            step_color = (150, 150, 150)
            pygame.draw.line(self.screen, step_color, (x1, y1), (x2, y2), 3)
    
    def update_music_volume_by_distance(self):
        """Actualizar volumen de música según distancia al inicio y al final"""
        # Calcular distancias
        start_row, start_col = self.start_position
        exit_row, exit_col = self.exit_position
        curr_row, curr_col = self.current_position
        distance_from_start = ((curr_row - start_row)**2 + (curr_col - start_col)**2)**0.5
        distance_to_exit = ((curr_row - exit_row)**2 + (curr_col - exit_col)**2)**0.5
        
        if self.audio.current_music == 'adagio' and not self.audio.cthulhu_played:  # Solo para adagio
            # Volumen de adagio disminuye con la distancia al inicio
            # Volumen máximo (0.5) en el inicio, mínimo (0.05) a distancia 5 o más
            max_volume = 0.5
            min_volume = 0.05
            max_distance = 5.0
            
            # Interpolación lineal desde el inicio
            volume = max_volume - (distance_from_start / max_distance) * (max_volume - min_volume)
            volume = max(min_volume, min(max_volume, volume))  # Clamp entre min y max
            
            self.audio.music_channel.set_volume(volume)
            
            # Si estamos cerca de la salida, cambiar a cthulhu
            if distance_to_exit <= 5.0 and not self.audio.cthulhu_played and 'cthulhu' in self.audio.music_sounds:
                self.audio.music_channel.stop()
                self.audio.current_music = 'cthulhu'
                self.audio.music_channel.play(self.audio.music_sounds['cthulhu'], loops=-1)
                self.audio.music_channel.set_volume(min_volume)  # Empezar con volumen bajo
                self.cthulhu_played = True
        
        elif self.cthulhu_played:  # Volumen de cthulhu aumenta al acercarse a la salida
            # Si estamos en la celda de salida, volumen máximo (1.0) y mostrar subtítulo
            if (curr_row, curr_col) == self.exit_position:
                # Solo configurar volumen de Cthulhu si el viento aún no está sonando
                if not self.wind_fading_in and self.audio.current_music == 'cthulhu':
                    self.audio.music_channel.set_volume(1.0)
                
            # Si volvemos cerca del inicio, regresar a adagio
            elif distance_from_start <= 5.0 and 'adagio' in self.audio.music_sounds:
                self.audio.music_channel.stop()
                self.audio.current_music = 'adagio'
                self.audio.music_channel.play(self.audio.music_sounds['adagio'], loops=-1)
                # Volumen según distancia al inicio
                max_volume = 0.5
                min_volume = 0.05
                max_distance = 5.0
                volume = max_volume - (distance_from_start / max_distance) * (max_volume - min_volume)
                volume = max(min_volume, min(max_volume, volume))
                self.audio.music_channel.set_volume(volume)
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
                
                self.audio.music_channel.set_volume(volume)
    
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
            self.audio.update_fades()
            

            # Eliminar fade-in del viento: nada que hacer aquí
            
            # Actualizar sistema de pensamientos
            
            self.audio.update_thoughts()
            # Sincronizar imagen del pensamiento (sin sobrescribir exit_image)
            self.thought_image_shown = self.audio.showing_image
            if self.audio.showing_image:
                self.thought_image = self.audio.image_surface
                self.thought_image_start_time = self.audio.image_start_time
            else:
                self.thought_image = None
            
            # Si el pensamiento de intro acaba de terminar, marcar flag
            if self.was_active and not self.audio.thought_active and self.intro_thought_triggered and not self.intro_thought_finished:
                self.intro_thought_finished = True
                print("[DEBUG] Pensamiento de intro terminado - antorchas ahora disponibles")
            
            # Si el pensamiento de salida acaba de terminar, activar ráfaga
            if self.was_active and not self.audio.thought_active and self.exit_thought_active and not self.rafaga_thought_triggered:
                print("[DEBUG] Pensamiento de salida terminado - activando ráfaga inmediatamente")
                if self.rafaga_sound:
                    # Parar la música de Cthulhu
                    self.audio.music_channel.stop()
                    
                    # Activar pensamiento de ráfaga (bloquea movimiento)
                    self.audio.trigger_thought(
                        sounds=[(self.rafaga_sound, 0)],
                        blocks_movement=True
                    )
                    self.rafaga_thought_triggered = True
                    self.torches_flickering = True
                    self.flicker_start_time = pygame.time.get_ticks()
                    # Las antorchas parpadean durante 5 segundos
                    self.flicker_duration = 5000  #  5 segundos
                    
                    # Hacer zoom in máximo al empezar el parpadeo
                    self.current_zoom_index = 0  # Zoom máximo (7x7)
                    self.view_size = self.zoom_levels[self.current_zoom_index]
                    self.cell_size = self.fixed_window_size // self.view_size
                    self.update_camera_target()
                    print("[DEBUG] Zoom in máximo aplicado")
                    
                    # Inicializar contadores para zoom out
                    self.zoom_out_count = 0
                    self.zoom_out_triggered = False
                    
                    # Iniciar música de viento inmediatamente con volumen máximo
                    if 'viento' in self.audio.music_sounds:
                        self.audio.current_music = 'viento'
                        self.audio.music_channel.play(self.audio.music_sounds['viento'], loops=-1)
                        self.audio.music_channel.set_volume(1.0)  # Volumen máximo desde el inicio
            
            # Guardar estado anterior de thought_active
            self.was_active = self.audio.thought_active

            # Actualizar volumen de música según distancia (solo durante el juego, no durante fade)
            if not self.showing_title and not self.intro_anim_active and not self.audio.fading_out and not self.audio.fading_in and not self.wind_fading_in:
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
                            self.audio.stop_music()
                            # Cancelar cualquier pensamiento activo
                            if self.audio.thought_active:
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
                        if self.audio.thought_active:
                            self.audio.cancel_thought()
                        # Si no hay pensamiento, preguntar si volver al menú principal
                        else:
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
                        self.lighting.toggle_lines_darkening()
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
            await asyncio.sleep(0) # Yield control to browser
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    dungeon = DungeonBoard()
    asyncio.run(dungeon.run())