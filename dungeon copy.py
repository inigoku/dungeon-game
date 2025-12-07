import pygame
import random
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
    def __init__(self, size=9, cell_size=60):
        self.size = size
        self.cell_size = cell_size
        self.board = [[Cell(CellType.EMPTY) for _ in range(size)] for _ in range(size)]
        
        # Set central cell as INICIO
        center = size // 2
        self.board[center][center] = Cell(CellType.INICIO , {Direction.N, Direction.E, Direction.S, Direction.O})
        # Guardar centro y estado de interacción
        self.current_position = (center, center)
        
        pygame.init()
        self.width = size * cell_size
        self.height = size * cell_size
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Dungeon 2D")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
    
    def draw(self):
        self.screen.fill((255, 255, 255))
        
        for row in range(self.size):
            for col in range(self.size):
                self.draw_cell(row, col)
        
        # Dibujar monigote en la posición actual
        self.draw_player()
        
        pygame.display.flip()
    
    def draw_player(self):
        """Dibuja un monigote en la posición actual del jugador."""
        player_row, player_col = self.current_position
        x = player_col * self.cell_size
        y = player_row * self.cell_size
        
        center_x = x + self.cell_size // 2
        center_y = y + self.cell_size // 2
        
        # Cabeza
        pygame.draw.circle(self.screen, (0, 0, 255), (center_x, center_y - 12), 6)
        # Cuerpo
        pygame.draw.line(self.screen, (0, 0, 255), (center_x, center_y - 6), (center_x, center_y + 6), 2)
        # Brazos
        pygame.draw.line(self.screen, (0, 0, 255), (center_x - 8, center_y), (center_x + 8, center_y), 2)
        # Piernas
        pygame.draw.line(self.screen, (0, 0, 255), (center_x, center_y + 6), (center_x - 5, center_y + 12), 2)
        pygame.draw.line(self.screen, (0, 0, 255), (center_x, center_y + 6), (center_x + 5, center_y + 12), 2)
    
    def draw_cell(self, row, col):
        cell = self.board[row][col]
        x = col * self.cell_size
        y = row * self.cell_size
        
        # Color based on type
        if cell.cell_type == CellType.EMPTY:
            color = (0, 0, 0)
        elif cell.cell_type == CellType.INICIO:
            color = (0, 255, 0)
        elif cell.cell_type == CellType.PASILLO:
            color = (100, 100, 100)
        else:  # HABITACION
            color = (255, 165, 0)
        
        pygame.draw.rect(self.screen, color, (x, y, self.cell_size, self.cell_size))
        pygame.draw.rect(self.screen, (200, 200, 200), (x, y, self.cell_size, self.cell_size), 2)
        
        # Draw exits
        if cell.cell_type != CellType.EMPTY:
            self.draw_exits(row, col, x, y, cell.exits)
    
    def draw_exits(self, row, col, x, y, exits):
        exit_size = 5
        mid_x_L = x + 0.9*self.cell_size // 2
        mid_x_R = x + 1.1*self.cell_size // 2
        mid_y_D = y + 0.9*self.cell_size // 2
        mid_y_U = y + 1.1*self.cell_size // 2

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
            pygame.draw.line(self.screen, (255, 0, 0), (mid_x_L, y), (mid_x_L, y + 0.1*self.cell_size), 2)
            pygame.draw.line(self.screen, (255, 0, 0), (mid_x_R, y), (mid_x_R, y + 0.1*self.cell_size), 2)
            # Si está al borde, tachar la salida
            if is_at_edge(Direction.N):
                pygame.draw.line(self.screen, (0, 0, 0), (mid_x_L, y + 0.05*self.cell_size), (mid_x_R, y + 0.05*self.cell_size), 2)
            else:
                nr, nc = neighbor_coords(Direction.N)
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.N)
                    if opposite not in neighbor.exits:
                        pygame.draw.line(self.screen, (0, 0, 0), (mid_x_L, y + 0.05*self.cell_size), (mid_x_R, y + 0.05*self.cell_size), 2)

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
                        neighbor_mid_x_L = nc * self.cell_size + 0.9*self.cell_size // 2
                        neighbor_mid_x_R = nc * self.cell_size + 1.1*self.cell_size // 2
                        pygame.draw.line(self.screen, (0, 0, 0), (neighbor_mid_x_L, neighbor_y + self.cell_size - 0.05*self.cell_size), (neighbor_mid_x_R, neighbor_y + self.cell_size - 0.05*self.cell_size), 2)

        # South
        if Direction.S in exits:
            pygame.draw.line(self.screen, (255, 0, 0), (mid_x_L, y + self.cell_size), (mid_x_L, y + 0.9*self.cell_size), 2)
            pygame.draw.line(self.screen, (255, 0, 0), (mid_x_R, y + self.cell_size), (mid_x_R, y + 0.9*self.cell_size), 2)
            # Si está al borde, tachar
            if is_at_edge(Direction.S):
                pygame.draw.line(self.screen, (0, 0, 0), (mid_x_L, y + self.cell_size - 0.05*self.cell_size), (mid_x_R, y + self.cell_size - 0.05*self.cell_size), 2)
            else:
                nr, nc = neighbor_coords(Direction.S)
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.S)
                    if opposite not in neighbor.exits:
                        pygame.draw.line(self.screen, (0, 0, 0), (mid_x_L, y + self.cell_size - 0.05*self.cell_size), (mid_x_R, y + self.cell_size - 0.05*self.cell_size), 2)

        # South (complementaria)
        if Direction.S not in exits:
            nr, nc = neighbor_coords(Direction.S)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.S)
                    if opposite in neighbor.exits:
                        neighbor_y = nr * self.cell_size
                        neighbor_mid_x_L = nc * self.cell_size + 0.9*self.cell_size // 2
                        neighbor_mid_x_R = nc * self.cell_size + 1.1*self.cell_size // 2
                        pygame.draw.line(self.screen, (0, 0, 0), (neighbor_mid_x_L, neighbor_y + 0.05*self.cell_size), (neighbor_mid_x_R, neighbor_y + 0.05*self.cell_size), 2)

        # East
        if Direction.E in exits:
            pygame.draw.line(self.screen, (255, 0, 0), (x + self.cell_size, mid_y_D), (x + 0.9*self.cell_size, mid_y_D), 2)
            pygame.draw.line(self.screen, (255, 0, 0), (x + self.cell_size, mid_y_U), (x + 0.9*self.cell_size, mid_y_U), 2)
            # Si está al borde, tachar
            if is_at_edge(Direction.E):
                pygame.draw.line(self.screen, (0, 0, 0), (x + self.cell_size - 0.05*self.cell_size, mid_y_D), (x + self.cell_size - 0.05*self.cell_size, mid_y_U), 2)
            else:
                nr, nc = neighbor_coords(Direction.E)
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.E)
                    if opposite not in neighbor.exits:
                        pygame.draw.line(self.screen, (0, 0, 0), (x + self.cell_size - 0.05*self.cell_size, mid_y_D), (x + self.cell_size - 0.05*self.cell_size, mid_y_U), 2)

        # East (complementaria)
        if Direction.E not in exits:
            nr, nc = neighbor_coords(Direction.E)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.E)
                    if opposite in neighbor.exits:
                        neighbor_x = nc * self.cell_size
                        neighbor_mid_y_D = nr * self.cell_size + 0.9*self.cell_size // 2
                        neighbor_mid_y_U = nr * self.cell_size + 1.1*self.cell_size // 2
                        pygame.draw.line(self.screen, (0, 0, 0), (neighbor_x + 0.05*self.cell_size, neighbor_mid_y_D), (neighbor_x + 0.05*self.cell_size, neighbor_mid_y_U), 2)

        # West
        if Direction.O in exits:
            pygame.draw.line(self.screen, (255, 0, 0), (x, mid_y_D), (x + 0.1*self.cell_size, mid_y_D), 2)
            pygame.draw.line(self.screen, (255, 0, 0), (x, mid_y_U), (x + 0.1*self.cell_size, mid_y_U), 2)
            # Si está al borde, tachar
            if is_at_edge(Direction.O):
                pygame.draw.line(self.screen, (0, 0, 0), (x + 0.05*self.cell_size, mid_y_D), (x + 0.05*self.cell_size, mid_y_U), 2)
            else:
                nr, nc = neighbor_coords(Direction.O)
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.O)
                    if opposite not in neighbor.exits:
                        pygame.draw.line(self.screen, (0, 0, 0), (x + 0.05*self.cell_size, mid_y_D), (x + 0.05*self.cell_size, mid_y_U), 2)

        # West (complementaria)
        if Direction.O not in exits:
            nr, nc = neighbor_coords(Direction.O)
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbor = self.board[nr][nc]
                if neighbor.cell_type != CellType.EMPTY:
                    opposite = self.get_opposite_direction(Direction.O)
                    if opposite in neighbor.exits:
                        neighbor_x = nc * self.cell_size
                        neighbor_mid_y_D = nr * self.cell_size + 0.9*self.cell_size // 2
                        neighbor_mid_y_U = nr * self.cell_size + 1.1*self.cell_size // 2
                        pygame.draw.line(self.screen, (0, 0, 0), (neighbor_x + self.cell_size - 0.05*self.cell_size, neighbor_mid_y_D), (neighbor_x + self.cell_size - 0.05*self.cell_size, neighbor_mid_y_U), 2)

    def get_opposite_direction(self, direction: Direction) -> Direction:
        """Retorna la dirección opuesta."""
        opposites = {
            Direction.N: Direction.S,
            Direction.S: Direction.N,
            Direction.E: Direction.O,
            Direction.O: Direction.E,
        }
        return opposites.get(direction, direction)
    
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
                self.current_position = (target_row, target_col)
            # si existe pero no tiene la salida complementaria, no se puede mover
            return

        # Si la celda es EMPTY, crearla
        # 75% PASILLO, 25% HABITACION
        cell_type = CellType.PASILLO if random.random() < 0.75 else CellType.HABITACION
        exits = self.generate_random_exits(direction, cell_type)
        self.board[target_row][target_col] = Cell(cell_type, exits)
        self.current_position = (target_row, target_col)
    
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