"""Decoraciones visuales del dungeon (antorchas, sangre, fuente, escaleras)."""
import pygame  # type: ignore
import random
import math
from typing import Tuple
from models.cell import Cell, Direction


class DecorationRenderer:
    """Renderiza decoraciones como antorchas, manchas de sangre, fuente y escaleras."""
    
    def __init__(self, screen: pygame.Surface, cell_size: int) -> None:
        self.screen: pygame.Surface = screen
        self.cell_size: int = cell_size
    
    def draw_wet_footprints(self, x: int, y: int, footprints: list) -> None:
        """Dibuja huellas húmedas en la celda que se desvanecen con el tiempo.
        
        Args:
            x, y: Coordenadas en pantalla de la celda
            footprints: Lista de diccionarios con datos de huellas
        """
        current_time = pygame.time.get_ticks()
        
        for fp in footprints:
            age = current_time - fp['time']
            # Duración de 15 segundos
            if age > 15000:
                continue
            
            # Calcular opacidad (fade out)
            alpha = int(120 * (1.0 - age / 15000))
            
            # Dibujar huella (elipse oscura verdosa/azulada para simular humedad)
            surf = pygame.Surface((14, 10), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (20, 40, 40, alpha), (0, 0, 14, 10))
            
            fp_x = x + fp['rel_x']
            fp_y = y + fp['rel_y']
            self.screen.blit(surf, (fp_x - 7, fp_y - 5))
    
    def draw_blood_stains(self, board_row: int, board_col: int, x: int, y: int, 
                         brightness_factor: float, exit_position: Tuple[int, int]) -> None:
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
    
    def draw_torches(self, board_row: int, board_col: int, x: int, y: int, 
                    cell: Cell, num_torches: int) -> None:
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
    
    def _draw_single_torch(self, x: int, y: int, size: int, flicker: float) -> None:
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
    
    def draw_fountain(self, x: int, y: int, brightness_factor: float = 1.0) -> None:
        """Dibuja una fuente en la esquina superior izquierda de una celda."""
        fountain_size = max(20, int(self.cell_size * 0.3))
        fountain_x = x + fountain_size // 2 + 5
        fountain_y = y + fountain_size // 2 + 5
        
        # Base de piedra
        base_val = int(100 * brightness_factor)
        base_color = (base_val, base_val, base_val)
        pygame.draw.rect(self.screen, base_color,
                        (fountain_x - fountain_size // 2,
                         fountain_y - fountain_size // 2,
                         fountain_size, fountain_size))
        
        # Borde de la base
        border_val = int(150 * brightness_factor)
        border_color = (border_val, border_val, border_val)
        pygame.draw.rect(self.screen, border_color,
                        (fountain_x - fountain_size // 2,
                         fountain_y - fountain_size // 2,
                         fountain_size, fountain_size), 2)
        
        # Agua (círculo azul)
        water_color = (int(100 * brightness_factor), int(180 * brightness_factor), int(255 * brightness_factor))
        water_radius = fountain_size // 3
        pygame.draw.circle(self.screen, water_color,
                          (fountain_x, fountain_y), water_radius)
        
        # Animación de ondas y brillo
        t = pygame.time.get_ticks()
        
        # Ondas concéntricas
        for i in range(3):
            progress = ((t + i * 800) % 2400) / 2400.0
            current_radius = int(water_radius * progress)
            if current_radius > 0:
                ripple_val = int(255 * brightness_factor)
                ripple_color = (int(150 * brightness_factor), int(220 * brightness_factor), ripple_val)
                pygame.draw.circle(self.screen, ripple_color, (fountain_x, fountain_y), current_radius, 1)
        
        # Brillo especular pulsante
        shine_x = fountain_x - water_radius // 3
        shine_y = fountain_y - water_radius // 3
        shine_radius = max(2, int(water_radius * 0.2))
        pulse = (math.sin(t * 0.005) + 1) * 0.5
        shine_alpha = int((100 + 100 * pulse) * brightness_factor)
        shine_surf = pygame.Surface((shine_radius * 2, shine_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(shine_surf, (255, 255, 255, shine_alpha), (shine_radius, shine_radius), shine_radius)
        self.screen.blit(shine_surf, (shine_x - shine_radius, shine_y - shine_radius))
        
        # Borde del agua
        water_border_color = (int(150 * brightness_factor), int(200 * brightness_factor), int(255 * brightness_factor))
        pygame.draw.circle(self.screen, water_border_color,
                          (fountain_x, fountain_y), water_radius, 2)
    
    def draw_dust_particles(self, x: int, y: int, board_row: int, board_col: int, brightness_factor: float = 1.0) -> None:
        """Dibuja partículas de polvo flotando en el aire."""
        t = pygame.time.get_ticks()
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed)
        
        num_particles = 40
        
        for i in range(num_particles):
            # Posición inicial aleatoria
            start_x = rnd.randint(0, self.cell_size)
            start_y = rnd.randint(0, self.cell_size)
            
            # Movimiento
            # X: oscilación sinusoidal suave
            offset_x = math.sin(t * 0.0005 + i) * 15
            
            # Y: movimiento ascendente constante con wrap-around (suben y reaparecen abajo)
            speed_y = rnd.uniform(0.01, 0.03)
            offset_y = (t * speed_y) % self.cell_size
            
            # Coordenadas finales
            px = x + int((start_x + offset_x) % self.cell_size)
            py = y + int((start_y - offset_y) % self.cell_size)
            
            # Tamaño y color
            size = rnd.randint(1, 2)
            # Brillo pulsante (parpadeo lento)
            pulse = (math.sin(t * 0.003 + i) + 1) * 0.5
            alpha = int((50 + 100 * pulse) * brightness_factor)
            
            if alpha > 0:
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 255, 200, alpha), (size//2, size//2), size//2)
                self.screen.blit(surf, (px, py))
    
    def draw_cobwebs(self, x: int, y: int, board_row: int, board_col: int, brightness_factor: float = 1.0) -> None:
        """Dibuja telarañas en las esquinas de las habitaciones."""
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed)
        
        # Probabilidad de tener telarañas en esta habitación (30%)
        if rnd.random() > 0.3:
            return

        # Esquinas posibles: (cx_offset, cy_offset, dx, dy)
        corners = [
            (0, 0, 1, 1),                                     # Top-Left
            (self.cell_size, 0, -1, 1),                       # Top-Right
            (0, self.cell_size, 1, -1),                       # Bottom-Left
            (self.cell_size, self.cell_size, -1, -1)          # Bottom-Right
        ]
        
        # Elegir 1 a 3 esquinas
        num_webs = rnd.randint(1, 3)
        selected_corners = rnd.sample(corners, num_webs)
        
        # Color blanco grisáceo muy transparente, afectado por brillo
        alpha = int(80 * brightness_factor)
        if alpha < 5:
            return
        web_color = (220, 220, 220, alpha)
        
        # Crear superficie temporal para las telarañas
        web_surf = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        
        for cx_off, cy_off, dx, dy in selected_corners:
            cx = cx_off
            cy = cy_off
            
            size = rnd.randint(int(self.cell_size * 0.15), int(self.cell_size * 0.25))
            
            points = []
            num_radials = rnd.randint(3, 5)
            
            for i in range(num_radials):
                angle = (i / (num_radials - 1)) * (math.pi / 2)
                
                ox = math.cos(angle) * size
                oy = math.sin(angle) * size
                
                px = cx + ox * dx
                py = cy + oy * dy
                
                points.append((px, py))
                pygame.draw.line(web_surf, web_color, (cx, cy), (px, py), 1)
            
            # Conexiones transversales
            num_cross = rnd.randint(2, 4)
            for j in range(1, num_cross + 1):
                factor = j / (num_cross + 1)
                for k in range(len(points) - 1):
                    p1 = points[k]
                    p2 = points[k+1]
                    
                    start_x = cx + (p1[0] - cx) * factor
                    start_y = cy + (p1[1] - cy) * factor
                    
                    end_x = cx + (p2[0] - cx) * factor
                    end_y = cy + (p2[1] - cy) * factor
                    
                    pygame.draw.line(web_surf, web_color, (start_x, start_y), (end_x, end_y), 1)
        
        self.screen.blit(web_surf, (x, y))

    def draw_spiral_stairs(self, x: int, y: int) -> None:
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
