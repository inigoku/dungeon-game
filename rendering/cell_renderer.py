"""Renderizado de celdas individuales del dungeon."""
import pygame
from models.cell import Cell, CellType, Direction


class CellRenderer:
    """Renderiza celdas individuales del dungeon con todos sus elementos."""
    
    def __init__(self, screen, cell_size, size):
        """
        Args:
            screen: Superficie de pygame donde dibujar
            cell_size: Tamaño de cada celda en píxeles
            size: Tamaño del tablero (número de celdas por lado)
        """
        self.screen = screen
        self.cell_size = cell_size
        self.size = size
    
    def get_opposite_direction(self, direction):
        """Retorna la dirección opuesta."""
        opposite_map = {
            Direction.N: Direction.S,
            Direction.S: Direction.N,
            Direction.E: Direction.O,
            Direction.O: Direction.E,
        }
        return opposite_map.get(direction)
    
    def draw_cell_background(self, x, y, cell, board_row, board_col, 
                            brightness_factor, draw_stone_callback):
        """Dibuja el fondo de una celda según su tipo.
        
        Args:
            x, y: Coordenadas en pantalla
            cell: Objeto Cell
            board_row, board_col: Posición en el tablero
            brightness_factor: Factor de brillo (0.0 a 1.0)
            draw_stone_callback: Función para dibujar texturas de piedra
        """
        brightness = int(255 * brightness_factor)
        floor_color = (brightness, brightness, brightness)
        
        if cell.cell_type == CellType.EMPTY:
            # Pared negra
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, self.cell_size, self.cell_size))
            pygame.draw.rect(self.screen, (90, 90, 90), (x, y, self.cell_size, self.cell_size), 3)
        else:
            # Suelo iluminado
            pygame.draw.rect(self.screen, floor_color, (x, y, self.cell_size, self.cell_size))
            # Marco
            marco_color = tuple(int(120 * brightness_factor) for _ in range(3))
            pygame.draw.rect(self.screen, marco_color, (x, y, self.cell_size, self.cell_size), 3)
            # Piedras en paredes
            if cell.cell_type != CellType.EMPTY:
                draw_stone_callback(board_row, board_col, x, y, cell, brightness_factor)
    
    def draw_cell_tunnels(self, x, y, cell, board_row, board_col, 
                         lines_brightness_factor, lines_darkening_enabled,
                         draw_broken_line_callback):
        """Dibuja los túneles/pasillos internos de una celda.
        
        Args:
            x, y: Coordenadas en pantalla
            cell: Objeto Cell
            board_row, board_col: Posición en el tablero
            lines_brightness_factor: Factor de brillo para las líneas
            lines_darkening_enabled: Si el oscurecimiento está activado
            draw_broken_line_callback: Función para dibujar líneas quebradas
        """
        if cell.cell_type not in [CellType.PASILLO, CellType.HABITACION, CellType.INICIO, CellType.SALIDA]:
            return
        
        # Calcular posiciones según tipo de celda
        if cell.cell_type in [CellType.HABITACION, CellType.INICIO]:
            center_x_L = x + 0.15 * self.cell_size
            center_x_R = x + 0.85 * self.cell_size
            center_y_D = y + 0.15 * self.cell_size
            center_y_U = y + 0.85 * self.cell_size
            mid_x_L = x + 0.15 * self.cell_size
            mid_x_R = x + 0.85 * self.cell_size
            mid_y_D = y + 0.15 * self.cell_size
            mid_y_U = y + 0.85 * self.cell_size
        else:  # PASILLO
            center_x_L = x + 0.8 * self.cell_size // 2
            center_x_R = x + 1.2 * self.cell_size // 2
            center_y_D = y + 0.8 * self.cell_size // 2
            center_y_U = y + 1.2 * self.cell_size // 2
            mid_x_L = x + 0.8 * self.cell_size // 2
            mid_x_R = x + 1.2 * self.cell_size // 2
            mid_y_D = y + 0.8 * self.cell_size // 2
            mid_y_U = y + 1.2 * self.cell_size // 2
        
        # Color de las líneas internas
        base_line_color = 150
        darkened_value = int(base_line_color * lines_brightness_factor)
        inner_color = (darkened_value, darkened_value, darkened_value)
        
        # North
        if Direction.N in cell.exits:
            if lines_darkening_enabled:
                draw_broken_line_callback(inner_color, (mid_x_L, center_y_D), (mid_x_L, y + 0.1 * self.cell_size), 3, board_row, board_col, 1)
                draw_broken_line_callback(inner_color, (mid_x_R, center_y_D), (mid_x_R, y + 0.1 * self.cell_size), 3, board_row, board_col, 2)
            else:
                pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_D), (mid_x_L, y + 0.1 * self.cell_size), 3)
                pygame.draw.line(self.screen, inner_color, (mid_x_R, center_y_D), (mid_x_R, y + 0.1 * self.cell_size), 3)
        else:
            if lines_darkening_enabled:
                draw_broken_line_callback(inner_color, (mid_x_L, center_y_D), (mid_x_R, center_y_D), 3, board_row, board_col, 3)
            else:
                pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_D), (mid_x_R, center_y_D), 3)
        
        # South
        if Direction.S in cell.exits:
            if lines_darkening_enabled:
                draw_broken_line_callback(inner_color, (mid_x_L, center_y_U), (mid_x_L, y + 0.9 * self.cell_size), 3, board_row, board_col, 4)
                draw_broken_line_callback(inner_color, (mid_x_R, center_y_U), (mid_x_R, y + 0.9 * self.cell_size), 3, board_row, board_col, 5)
            else:
                pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_U), (mid_x_L, y + 0.9 * self.cell_size), 3)
                pygame.draw.line(self.screen, inner_color, (mid_x_R, center_y_U), (mid_x_R, y + 0.9 * self.cell_size), 3)
        else:
            if lines_darkening_enabled:
                draw_broken_line_callback(inner_color, (mid_x_L, center_y_U), (mid_x_R, center_y_U), 3, board_row, board_col, 6)
            else:
                pygame.draw.line(self.screen, inner_color, (mid_x_L, center_y_U), (mid_x_R, center_y_U), 3)
        
        # East
        if Direction.E in cell.exits:
            if lines_darkening_enabled:
                draw_broken_line_callback(inner_color, (center_x_R, mid_y_D), (x + 0.9 * self.cell_size, mid_y_D), 3, board_row, board_col, 7)
                draw_broken_line_callback(inner_color, (center_x_R, mid_y_U), (x + 0.9 * self.cell_size, mid_y_U), 3, board_row, board_col, 8)
            else:
                pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_D), (x + 0.9 * self.cell_size, mid_y_D), 3)
                pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_U), (x + 0.9 * self.cell_size, mid_y_U), 3)
        else:
            if lines_darkening_enabled:
                draw_broken_line_callback(inner_color, (center_x_R, mid_y_D), (center_x_R, mid_y_U), 3, board_row, board_col, 9)
            else:
                pygame.draw.line(self.screen, inner_color, (center_x_R, mid_y_D), (center_x_R, mid_y_U), 3)
        
        # West
        if Direction.O in cell.exits:
            if lines_darkening_enabled:
                draw_broken_line_callback(inner_color, (center_x_L, mid_y_D), (x + 0.1 * self.cell_size, mid_y_D), 3, board_row, board_col, 10)
                draw_broken_line_callback(inner_color, (center_x_L, mid_y_U), (x + 0.1 * self.cell_size, mid_y_U), 3, board_row, board_col, 11)
            else:
                pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_D), (x + 0.1 * self.cell_size, mid_y_D), 3)
                pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_U), (x + 0.1 * self.cell_size, mid_y_U), 3)
        else:
            if lines_darkening_enabled:
                draw_broken_line_callback(inner_color, (center_x_L, mid_y_D), (center_x_L, mid_y_U), 3, board_row, board_col, 12)
            else:
                pygame.draw.line(self.screen, inner_color, (center_x_L, mid_y_D), (center_x_L, mid_y_U), 3)
