"""Decoraciones visuales del dungeon (antorchas, sangre, fuente, escaleras)."""
import pygame
import random
import math
from models.cell import Direction


class DecorationRenderer:
    """Renderiza decoraciones como antorchas, manchas de sangre, fuente y escaleras."""
    
    def __init__(self, screen, cell_size):
        self.screen = screen
        self.cell_size = cell_size
    
    def draw_blood_stains(self, board_row, board_col, x, y, brightness_factor, exit_position):
        """Dibuja manchas de sangre en celdas cercanas a la salida.
        
        Args:
            board_row: Fila en el tablero
            board_col: Columna en el tablero
            x: Coordenada x en pantalla
            y: Coordenada y en pantalla
            brightness_factor: Factor de brillo (0.0 a 1.0)
            exit_position: Tupla (row, col) de la posición de salida
        """
        # Aplicar 50% del oscurecimiento a la sangre
        blood_brightness_factor = 1.0 - 0.5 * (1.0 - brightness_factor)
        
        exit_row, exit_col = exit_position
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
            tuple(int(c * blood_brightness_factor) for c in (80, 0, 0)),
            tuple(int(c * blood_brightness_factor) for c in (100, 10, 10)),
            tuple(int(c * blood_brightness_factor) for c in (70, 5, 5)),
        ]
        
        # Generar 2-5 manchas por celda
        num_stains = rnd.randint(2, 5)
        for i in range(num_stains):
            stain_x = x + int(rnd.uniform(0.2, 0.8) * self.cell_size)
            stain_y = y + int(rnd.uniform(0.2, 0.8) * self.cell_size)
            size = rnd.randint(4, 12)
            color = rnd.choice(blood_colors)
            
            # Dibujar mancha irregular
            num_circles = rnd.randint(2, 4)
            for j in range(num_circles):
                offset_x = rnd.randint(-size//2, size//2)
                offset_y = rnd.randint(-size//2, size//2)
                circle_size = rnd.randint(size//2, size)
                pygame.draw.circle(self.screen, color,
                                 (stain_x + offset_x, stain_y + offset_y),
                                 circle_size)
    
    def draw_torches(self, board_row, board_col, x, y, cell, num_torches):
        """Dibuja antorchas animadas en las paredes sin salida.
        
        Args:
            board_row: Fila en el tablero
            board_col: Columna en el tablero
            x: Coordenada x en pantalla
            y: Coordenada y en pantalla
            cell: Objeto Cell
            num_torches: Número de antorchas a dibujar
        """
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed)
        
        # Animación de la llama
        t = pygame.time.get_ticks()
        flicker = abs(math.sin(t * 0.003 + seed)) * 0.3 + 0.7
        
        torch_size = max(8, int(self.cell_size * 0.15))
        wall_thickness = int(self.cell_size * 0.28)
        
        # Posibles ubicaciones (paredes sin salidas)
        possible_positions = []
        
        if Direction.N not in cell.exits:
            possible_positions.append(('N', x + self.cell_size // 2 + rnd.randint(-20, 20),
                                      y + wall_thickness // 2))
        if Direction.S not in cell.exits:
            possible_positions.append(('S', x + self.cell_size // 2 + rnd.randint(-20, 20),
                                      y + self.cell_size - wall_thickness // 2))
        if Direction.E not in cell.exits:
            possible_positions.append(('E', x + self.cell_size - wall_thickness // 2,
                                      y + self.cell_size // 2 + rnd.randint(-20, 20)))
        if Direction.O not in cell.exits:
            possible_positions.append(('O', x + wall_thickness // 2,
                                      y + self.cell_size // 2 + rnd.randint(-20, 20)))
        
        # Dibujar antorchas
        for i in range(min(num_torches, len(possible_positions))):
            _, torch_x, torch_y = possible_positions[i]
            self._draw_single_torch(torch_x, torch_y, torch_size, flicker)
    
    def _draw_single_torch(self, x, y, size, flicker):
        """Dibuja una antorcha individual con llama animada."""
        # Mango de madera
        wood_color = (101, 67, 33)
        handle_width = max(3, size // 4)
        handle_height = size
        pygame.draw.rect(self.screen, wood_color,
                        (x - handle_width // 2, y, handle_width, handle_height))
        
        # Llama exterior (naranja)
        flame_color = (255, 140, 0)
        flame_radius = int(size * flicker * 0.6)
        pygame.draw.circle(self.screen, flame_color, (x, y), flame_radius)
        
        # Llama interior (amarilla brillante)
        inner_flame_color = (255, 220, 100)
        inner_radius = int(flame_radius * 0.5)
        pygame.draw.circle(self.screen, inner_flame_color, (x, y), inner_radius)
    
    def draw_fountain(self, x, y):
        """Dibuja una fuente en la esquina superior izquierda de una celda."""
        fountain_size = max(20, int(self.cell_size * 0.3))
        fountain_x = x + fountain_size // 2 + 5
        fountain_y = y + fountain_size // 2 + 5
        
        # Base de piedra
        base_color = (100, 100, 100)
        pygame.draw.rect(self.screen, base_color,
                        (fountain_x - fountain_size // 2,
                         fountain_y - fountain_size // 2,
                         fountain_size, fountain_size))
        
        # Borde de la base
        border_color = (150, 150, 150)
        pygame.draw.rect(self.screen, border_color,
                        (fountain_x - fountain_size // 2,
                         fountain_y - fountain_size // 2,
                         fountain_size, fountain_size), 2)
        
        # Agua (círculo azul)
        water_color = (100, 180, 255)
        water_radius = fountain_size // 3
        pygame.draw.circle(self.screen, water_color,
                          (fountain_x, fountain_y), water_radius)
        
        # Borde del agua
        water_border_color = (150, 200, 255)
        pygame.draw.circle(self.screen, water_border_color,
                          (fountain_x, fountain_y), water_radius, 2)
    
    def draw_spiral_stairs(self, x, y):
        """Dibuja una escalera de caracol en una esquina de la celda."""
        stairs_size = max(20, int(self.cell_size * 0.35))
        stairs_x = x + self.cell_size - stairs_size // 2 - 5
        stairs_y = y + self.cell_size - stairs_size // 2 - 5
        
        # Poste central
        post_color = (100, 80, 60)
        post_radius = max(3, stairs_size // 8)
        pygame.draw.circle(self.screen, post_color,
                          (stairs_x, stairs_y), post_radius)
        
        # Escalones en espiral
        num_steps = 8
        for i in range(num_steps):
            angle = (i / num_steps) * 2 * math.pi
            radius = stairs_size // 2
            step_x = stairs_x + int(radius * math.cos(angle))
            step_y = stairs_y + int(radius * math.sin(angle))
            
            # Color del escalón (gradiente de oscuro a claro)
            brightness = 120 + int(30 * (i / num_steps))
            step_color = (brightness, brightness - 20, brightness - 40)
            
            # Línea del escalón
            inner_x = stairs_x + int((radius * 0.3) * math.cos(angle))
            inner_y = stairs_y + int((radius * 0.3) * math.sin(angle))
            pygame.draw.line(self.screen, step_color,
                           (inner_x, inner_y), (step_x, step_y), 3)
        
        # Borde del poste
        border_color = (80, 60, 40)
        pygame.draw.circle(self.screen, border_color,
                          (stairs_x, stairs_y), post_radius, 1)
