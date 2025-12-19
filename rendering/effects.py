"""Efectos visuales del dungeon (líneas quebradas, texturas de piedra)."""
import pygame  # type: ignore
import random
from typing import Tuple, Callable
from models.cell import Cell, Direction


class EffectsRenderer:
    """Renderiza efectos visuales como líneas quebradas y texturas de piedra."""
    
    def __init__(self, screen: pygame.Surface, cell_size: int) -> None:
        self.screen: pygame.Surface = screen
        self.cell_size: int = cell_size
    
    def draw_broken_line(self, color: Tuple[int, int, int], start_pos: Tuple[int, int], 
                        end_pos: Tuple[int, int], width: int, board_row: int, 
                        board_col: int, line_id: int) -> None:
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
        # Asegurar que el color tiene valores enteros
        if isinstance(color, (int, float)):
            # Si color es un solo número, convertir a tupla gris
            int_color: Tuple[int, int, int] = (int(color), int(color), int(color))
        else:
            # Si color es una tupla, convertir cada componente a int
            int_color = tuple(int(c) for c in color)  # type: ignore
        
        # Usar posición + line_id como semilla para reproducibilidad
        seed = board_row * 100000 + board_col * 100 + line_id
        rnd = random.Random(seed)
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calcular longitud de la línea
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        if length < 5:
            # Línea muy corta, dibujar directamente
            pygame.draw.line(self.screen, int_color, start_pos, end_pos, width)
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
            pygame.draw.line(self.screen, int_color, points[i], points[i + 1], width)
    
    def draw_stone_texture(self, board_row: int, board_col: int, x: int, y: int) -> None:
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

    def draw_stone_in_walls(self, board_row: int, board_col: int, x: int, y: int, 
                           cell: Cell, brightness_factor: float, 
                           count_torches_callback: Callable[[int, int, Cell], int]) -> None:
        """Dibuja textura de piedra únicamente en las zonas de pared dentro
        de una celda de tipo PASILLO (entre el suelo/centro y los bordes).

        Se respeta la presencia de salidas: si existe una salida N/S/E/O, se deja
        un hueco en la pared correspondiente para el pasaje.
        
        Args:
            board_row: Fila en el tablero
            board_col: Columna en el tablero
            x: Coordenada x en pantalla
            y: Coordenada y en pantalla
            cell: Objeto Cell
            brightness_factor: Factor de brillo (0.0 a 1.0) para oscurecer todos los colores
            count_torches_callback: Función para contar antorchas en la celda
        """
        seed = board_row * 100000 + board_col
        rnd = random.Random(seed + 7)

        # Calcular brillo base según número de antorchas, pero aplicando el factor de oscuridad
        torch_count = count_torches_callback(board_row, board_col, cell)
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
