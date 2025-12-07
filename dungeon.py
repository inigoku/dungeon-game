import pygame
import random
import math
import sys
from enum import Enum
from dataclasses import dataclass

class CellType(Enum):
    EMPTY = 0
    INICIO = 1
    PASILLO = 2
    HABITACION = 3

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

class DungeonBoard:
    def __init__(self, size=100, view_size=10, cell_size=60):
        self.size = size
        self.view_size = view_size  # Vista de 10x10
        self.cell_size = cell_size
        self.board = [[Cell(CellType.EMPTY) for _ in range(size)] for _ in range(size)]
        
        # Set central cell as INICIO
        center = size // 2
        self.board[center][center] = Cell(CellType.INICIO , {Direction.N, Direction.E, Direction.S, Direction.O})
        # Guardar centro y estado de interacción
        self.current_position = (center, center)
        
        # Scroll suave: cámara flotante que se interpola hacia la posición del jugador
        self.camera_offset_row = float(center - view_size // 2)
        self.camera_offset_col = float(center - view_size // 2)
        self.camera_speed = 0.05  # Factor de interpolación (0-1), mayor = más rápido
        
        pygame.init()
        self.width = view_size * cell_size
        self.height = view_size * cell_size
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Dungeon 2D")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
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
        
        # Retornar redondeado para usarlo en índices
        return int(round(self.camera_offset_row)), int(round(self.camera_offset_col))
    
    def center_camera_instantly(self, target_row, target_col):
        """Centra la cámara instantáneamente en la posición objetivo (sin interpolación)."""
        target_offset_row = max(0, min(target_row - self.view_size // 2, self.size - self.view_size))
        target_offset_col = max(0, min(target_col - self.view_size // 2, self.size - self.view_size))
        
        self.camera_offset_row = float(target_offset_row)
        self.camera_offset_col = float(target_offset_col)
    
    def draw(self):
        self.screen.fill((255, 255, 255))
        
        # Primero: actualizar el viewport (mueve la cámara)
        offset_row, offset_col = self.get_view_offset()
        
        # Segundo: dibujar solo la vista de 10x10
        for row in range(self.view_size):
            for col in range(self.view_size):
                board_row = offset_row + row
                board_col = offset_col + col
                if 0 <= board_row < self.size and 0 <= board_col < self.size:
                    self.draw_cell(board_row, board_col, row, col)

        # Dibujar aberturas (pasajes) conectadas en negro entre celdas.
        # Se hace después de dibujar todas las celdas para sobreescribir bordes.
        self.draw_openings(offset_row, offset_col)

        # Tercero: dibujar monigote en la posición actual (después del viewport)
        self.draw_player(offset_row, offset_col)
        
        pygame.display.flip()
    
    def draw_player(self, offset_row, offset_col):
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
        
        # Coordenadas relativas a la vista
        view_row = player_row - offset_row
        view_col = player_col - offset_col
        
        # Dibujar siempre (incluso si está entre celdas durante la animación)
        x = view_col * self.cell_size
        y = view_row * self.cell_size

        center_x = x + self.cell_size // 2
        center_y = y + self.cell_size // 2

        # Dibujar un sprite de guerrero procedimental escalable
        sprite_size = int(self.cell_size * 0.6)
        self.draw_warrior_sprite(center_x, center_y, sprite_size)

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
        head_x = cx
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
    
    def draw_cell(self, board_row, board_col, view_row, view_col):
        """Dibuja una celda del tablero en las coordenadas de la vista."""
        cell = self.board[board_row][board_col]
        x = view_col * self.cell_size
        y = view_row * self.cell_size
        
        # Color / textura based on type
        if cell.cell_type == CellType.EMPTY:
            # Pared negra (EMPTY debe verse negra)
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size))
            # Borde visible en gris para las celdas vacías
            pygame.draw.rect(self.screen, (90, 90, 90), (x, y, self.cell_size, self.cell_size), 3)
        elif cell.cell_type == CellType.INICIO:
            # Inicio es como una habitación: fondo negro con piedra
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size))
            # Marco del inicio en gris
            pygame.draw.rect(self.screen, (120, 120, 120), (x, y, self.cell_size, self.cell_size), 3)
            # Dibujar textura de piedra en las paredes
            self.draw_stone_in_walls(board_row, board_col, x, y, cell)
            # Dibujar fuente en la esquina superior izquierda
            self.draw_fountain(x, y)
        elif cell.cell_type == CellType.PASILLO:
            # Suelo del pasillo: el área entre las líneas y el centro debe ser negra
            floor_color = (0, 0, 0)
            pygame.draw.rect(self.screen, floor_color, (x, y, self.cell_size, self.cell_size))
            # Marco del pasillo ligeramente grueso
            pygame.draw.rect(self.screen, (120, 120, 120), (x, y, self.cell_size, self.cell_size), 3)
            # Dibujar textura de piedra solo en las 'paredes' dentro de la celda
            self.draw_stone_in_walls(board_row, board_col, x, y, cell)
        elif cell.cell_type == CellType.HABITACION:
            # Habitación como mazmorra: fondo negro con piedra en las paredes
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size))
            # Marco de la habitación en gris
            pygame.draw.rect(self.screen, (120, 120, 120), (x, y, self.cell_size, self.cell_size), 3)
            # Dibujar textura de piedra en las paredes
            self.draw_stone_in_walls(board_row, board_col, x, y, cell)
        
        # Para pasillos, habitaciones e inicio: dibujar camino desde el centro hacia las salidas
        if cell.cell_type in [CellType.PASILLO, CellType.HABITACION, CellType.INICIO]:
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
            
            # Las líneas internas serán siempre gris oscuro
            inner_color = (150, 150, 150)
            
            # North
            if Direction.N in cell.exits:
                pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_D), (mid_x_L, y + 0.1*self.cell_size), 3)
                pygame.draw.line(self.screen, inner_color, (mid_x_R, center_y_D), (mid_x_R, y + 0.1*self.cell_size), 3)
            else:
                # Cerrar el norte si no hay salida (siempre gris oscuro)
                pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_D), (mid_x_R, center_y_D), 3)
            
            # South
            if Direction.S in cell.exits:
                pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_U), (mid_x_L, y + 0.9*self.cell_size), 3)
                pygame.draw.line(self.screen, inner_color, (mid_x_R, center_y_U), (mid_x_R, y + 0.9*self.cell_size), 3)
            else:
                # Cerrar el sur si no hay salida (siempre gris oscuro)
                pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_U), (mid_x_R, center_y_U), 3)
            
            # East
            if Direction.E in cell.exits:
                pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_D), (x + 0.9*self.cell_size, mid_y_D), 3)
                pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_U), (x + 0.9*self.cell_size, mid_y_U), 3)
            else:
                # Cerrar el este si no hay salida (siempre gris oscuro)
                pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_D), (center_x_R, mid_y_U), 3)
            
            # West
            if Direction.O in cell.exits:
                pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 3)
                pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 3)
            else:
                # Cerrar el oeste si no hay salida (siempre gris oscuro)
                pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_D), (center_x_L, mid_y_U), 3)
        
        # Draw exits
        if cell.cell_type != CellType.EMPTY:
            self.draw_exits(board_row, board_col, x, y, cell.exits, cell.cell_type)
    
    def draw_exits(self, row, col, x, y, exits, cell_type):
        exit_size = 5
        # Las coordenadas son iguales para PASILLO, HABITACION e INICIO
        mid_x_L = x + 0.8*self.cell_size // 2
        mid_x_R = x + 1.2*self.cell_size // 2
        mid_y_D = y + 0.8*self.cell_size // 2
        mid_y_U = y + 1.2*self.cell_size // 2

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

            # Las salidas son rojo si apuntan a EMPTY, gris oscuro si no conectadas
            if neighbor_empty:
                exit_color = (255, 0, 0)
            else:
                exit_color = (150, 150, 150)

            pygame.draw.line(self.screen, exit_color, (mid_x_L, y), (mid_x_L, y + 0.1*self.cell_size), 4)
            pygame.draw.line(self.screen, exit_color, (mid_x_R, y), (mid_x_R, y + 0.1*self.cell_size), 4)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar la salida en negro
            if is_at_edge(Direction.N) or (not connected and not neighbor_empty):
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

            # Las salidas son rojo si apuntan a EMPTY, gris oscuro si no conectadas
            if neighbor_empty:
                exit_color = (255, 0, 0)
            else:
                exit_color = (150, 150, 150)

            pygame.draw.line(self.screen, exit_color, (mid_x_L, y + self.cell_size), (mid_x_L, y + 0.8*self.cell_size), 4)
            pygame.draw.line(self.screen, exit_color, (mid_x_R, y + self.cell_size), (mid_x_R, y + 0.8*self.cell_size), 4)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.S) or (not connected and not neighbor_empty):
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

            # Las salidas son rojo si apuntan a EMPTY, gris oscuro si no conectadas
            if neighbor_empty:
                exit_color = (255, 0, 0)
            else:
                exit_color = (150, 150, 150)

            pygame.draw.line(self.screen, exit_color, (x + self.cell_size, mid_y_D), (x + 0.8*self.cell_size, mid_y_D), 4)
            pygame.draw.line(self.screen, exit_color, (x + self.cell_size, mid_y_U), (x + 0.8*self.cell_size, mid_y_U), 4)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.E) or (not connected and not neighbor_empty):
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

            # Las salidas son rojo si apuntan a EMPTY, gris oscuro si no conectadas
            if neighbor_empty:
                exit_color = (255, 0, 0)
            else:
                exit_color = (150, 150, 150)

            pygame.draw.line(self.screen, exit_color, (x, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 4)
            pygame.draw.line(self.screen, exit_color, (x, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 4)
            # Si está al borde o la vecina no tiene la salida complementaria, tachar
            if is_at_edge(Direction.O) or (not connected and not neighbor_empty):
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

    def draw_openings(self, offset_row: int, offset_col: int):
        """Dibuja las aberturas negras entre celdas conectadas (sobre los bordes).

        Se limita el área de la apertura entre las dos 'líneas' de la salida,
        más ancha y más corta para no solapa las líneas de salida.
        """
        for view_r in range(self.view_size):
            for view_c in range(self.view_size):
                board_r = offset_row + view_r
                board_c = offset_col + view_c
                if not (0 <= board_r < self.size and 0 <= board_c < self.size):
                    continue
                cell = self.board[board_r][board_c]
                if cell.cell_type == CellType.EMPTY:
                    continue

                x = view_c * self.cell_size
                y = view_r * self.cell_size

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

                    # Conectada: dibujar apertura negra más ancha y corta
                    # Los rects deben respetar las líneas perpendiculares para que sea invisible la transición
                    if dir_ == Direction.N:
                        # Norte: rect horizontal entre mid_x_L y mid_x_R, pero respetando las líneas verticales
                        rx = int(mid_x_L) + 2
                        ry = int(y - open_thickness // 2)
                        rw = int(mid_x_R - mid_x_L) - 4
                        rh = int(open_thickness)
                        pygame.draw.rect(self.screen, (0, 0, 0), (rx, ry, rw, rh))
                    elif dir_ == Direction.S:
                        # Sur: rect horizontal entre mid_x_L y mid_x_R, respetando líneas verticales
                        rx = int(mid_x_L) + 2
                        ry = int(y + self.cell_size - open_thickness // 2)
                        rw = int(mid_x_R - mid_x_L) - 4
                        rh = int(open_thickness)
                        pygame.draw.rect(self.screen, (0, 0, 0), (rx, ry, rw, rh))
                    elif dir_ == Direction.E:
                        # Este: rect vertical entre mid_y_D y mid_y_U, respetando líneas horizontales
                        rx = int(x + self.cell_size - open_thickness // 2)
                        ry = int(mid_y_D) + 2
                        rw = int(open_thickness)
                        rh = int(mid_y_U - mid_y_D) - 4
                        pygame.draw.rect(self.screen, (0, 0, 0), (rx, ry, rw, rh))
                    elif dir_ == Direction.O:
                        # Oeste: rect vertical entre mid_y_D y mid_y_U, respetando líneas horizontales
                        rx = int(x - open_thickness // 2)
                        ry = int(mid_y_D) + 2
                        rw = int(open_thickness)
                        rh = int(mid_y_U - mid_y_D) - 4
                        pygame.draw.rect(self.screen, (0, 0, 0), (rx, ry, rw, rh))

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

    def draw_stone_in_walls(self, board_row: int, board_col: int, x: int, y: int, cell: Cell):
        """Dibuja textura de piedra únicamente en las zonas de pared dentro
        de una celda de tipo PASILLO (entre el suelo/centro y los bordes).

        Se respeta la presencia de salidas: si existe una salida N/S/E/O, se deja
        un hueco en la pared correspondiente para el pasaje.
        """
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed + 7)

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

        base_stone = (120, 120, 120)
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
    
    def generate_random_exits(self, exclude_direction: Direction, cell_type: CellType) -> set:
        """Genera salidas aleatorias según el tipo de celda, excepto la dirección de entrada.
        
        PASILLO: 1 salida 10%, 2 salidas 30%, 3 salidas 40%, 4 salidas 20%
        HABITACION: 1 salida 50%, 2 salidas 30%, 3 salidas 15%, 4 salidas 5%
        """
        exits = set()
        # La dirección opuesta a la de entrada siempre está (es por donde se llegó)
        opposite = self.get_opposite_direction(exclude_direction)
        exits.add(opposite)
        
        # Las otras tres direcciones
        all_directions = {Direction.N, Direction.E, Direction.S, Direction.O}
        other_directions = list(all_directions - {exclude_direction, opposite})
        
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
                # Primero: centrar cámara instantáneamente en la nueva posición
                self.center_camera_instantly(target_row, target_col)
                
                # Segundo: iniciar animación suave del muñeco desde posición antigua a nueva
                self.player_anim_from_pos = self.current_position
                self.player_anim_to_pos = (target_row, target_col)
                self.player_animating = True
                self.player_anim_start_time = pygame.time.get_ticks()
                self.player_walk_until = pygame.time.get_ticks() + self.player_walk_duration
                
                # Actualizar posición lógica
                self.current_position = (target_row, target_col)
            # si existe pero no tiene la salida complementaria, no se puede mover
            return

        # Si la celda es EMPTY, crearla
        # 75% PASILLO, 25% HABITACION
        cell_type = CellType.PASILLO if random.random() < 0.75 else CellType.HABITACION
        exits = self.generate_random_exits(direction, cell_type)
        
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
                    opposite = self.get_opposite_direction(dir_)
                    # Si la vecina tiene salida hacia aquí, mantener esa salida en la nueva celda
                    if opposite in neighbor.exits:
                        exits.add(dir_)
        
        self.board[target_row][target_col] = Cell(cell_type, exits)
        
        # Primero: centrar cámara instantáneamente en la nueva posición
        self.center_camera_instantly(target_row, target_col)
        
        # Segundo: iniciar animación suave del muñeco desde posición antigua a nueva
        self.player_anim_from_pos = self.current_position
        self.player_anim_to_pos = (target_row, target_col)
        self.player_animating = True
        self.player_anim_start_time = pygame.time.get_ticks()
        self.player_walk_until = pygame.time.get_ticks() + self.player_walk_duration
        
        # Actualizar posición lógica
        self.current_position = (target_row, target_col)
    
    def draw_fountain(self, x: int, y: int):
        """Dibuja una fuente en la esquina superior izquierda de una celda."""
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
    
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
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
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    dungeon = DungeonBoard()
    dungeon.run()