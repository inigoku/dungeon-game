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
        
        # --- Dibujo de elementos decorativos finales (escalera y losa en salida) ---
        if cell.cell_type == CellType.SALIDA:
            # Dibuja la escalera (si existe) aquí
            # ...aquí iría el código de la escalera...
            # Dibuja una losa más estrecha, más oscura y con rayitas negras
            losa_w = int(self.cell_size * 0.28)
            losa_h = int(self.cell_size * 0.16)
            losa_x = x + (self.cell_size - losa_w) // 2
            losa_y = y + self.cell_size // 2 + int(self.cell_size * 0.13)
            losa_color = (90, 90, 90)
            borde_color = (60, 60, 60)
            pygame.draw.rect(self.screen, losa_color, (losa_x, losa_y, losa_w, losa_h))
            pygame.draw.rect(self.screen, borde_color, (losa_x, losa_y, losa_w, losa_h), 2)
            n_rayas = 4
            for i in range(n_rayas):
                ry = losa_y + int(losa_h * (0.25 + 0.15 * i))
                pygame.draw.line(self.screen, (20, 20, 20), (losa_x + 6, ry), (losa_x + losa_w - 6, ry), 1)
        # ...existing code...