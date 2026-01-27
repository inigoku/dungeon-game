"""Board generation service."""
import random
import math
from collections import deque
from typing import List, Tuple, Dict, Set
from models import Cell, CellType, Direction
from config import MAX_GENERATION_ATTEMPTS


class BoardGenerator:
    """Handles dungeon board generation and pathfinding."""
    
    def __init__(self, size: int) -> None:
        self.size: int = size
    
    def check_connectivity(self, board: List[List[Cell]], start: Tuple[int, int], end: Tuple[int, int]) -> bool:
        """Verifica si hay un camino posible entre start y end usando BFS.
        Verifica que las celdas adyacentes tengan salidas enfrentadas.
        """
        queue: deque[Tuple[int, int]] = deque([start])
        visited: Set[Tuple[int, int]] = {start}
        
        direction_deltas: Dict[Direction, Tuple[int, int]] = {
            Direction.N: (-1, 0),
            Direction.S: (1, 0),
            Direction.E: (0, 1),
            Direction.O: (0, -1),
        }
        
        opposite_directions: Dict[Direction, Direction] = {
            Direction.N: Direction.S,
            Direction.S: Direction.N,
            Direction.E: Direction.O,
            Direction.O: Direction.E,
        }
        
        while queue:
            curr_row, curr_col = queue.popleft()
            
            if (curr_row, curr_col) == end:
                return True
            
            curr_cell = board[curr_row][curr_col]
            
            for direction, (dr, dc) in direction_deltas.items():
                if direction not in curr_cell.exits:
                    continue
                
                next_row = curr_row + dr
                next_col = curr_col + dc
                next_pos = (next_row, next_col)
                
                if not (0 <= next_row < self.size and 0 <= next_col < self.size):
                    continue
                if next_pos in visited:
                    continue
                
                next_cell = board[next_row][next_col]
                
                if next_cell.cell_type == CellType.EMPTY:
                    continue
                
                opposite = opposite_directions[direction]
                if opposite not in next_cell.exits:
                    continue
                
                visited.add(next_pos)
                queue.append(next_pos)
        
        return False
    
    def generate_exit_position(self, center: int) -> Tuple[int, int]:
        """Genera una posición aleatoria para la celda de salida, alejada del centro."""
        max_distance_to_edge = center - 5
        min_distance = int(max_distance_to_edge * 0.75)
        max_distance = max_distance_to_edge
        
        attempts = 0
        while attempts < 100:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(min_distance, max_distance)
            
            row = center + int(distance * math.cos(angle))
            col = center + int(distance * math.sin(angle))
            
            if 5 <= row < self.size - 5 and 5 <= col < self.size - 5:
                return (row, col)
            attempts += 1
        
        for fallback_distance in range(max_distance, min_distance - 1, -5):
            for fallback_angle in [0, math.pi/4, math.pi/2, 3*math.pi/4, 
                                   math.pi, 5*math.pi/4, 3*math.pi/2, 7*math.pi/4]:
                row = center + int(fallback_distance * math.cos(fallback_angle))
                col = center + int(fallback_distance * math.sin(fallback_angle))
                
                row = max(5, min(self.size - 6, row))
                col = max(5, min(self.size - 6, col))
                
                if 5 <= row < self.size - 5 and 5 <= col < self.size - 5:
                    return (row, col)
        
        return (center + max_distance, center)
    
    def calculate_main_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Calcula un camino tortuoso sin lazos desde start hasta end."""
        path = [start]
        current = start
        visited = {start}
        
        max_attempts = 10000
        attempts = 0
        
        while current != end and attempts < max_attempts:
            attempts += 1
            current_row, current_col = current
            end_row, end_col = end
            
            directions = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                next_row = current_row + dr
                next_col = current_col + dc
                next_pos = (next_row, next_col)
                
                if (0 <= next_row < self.size and 0 <= next_col < self.size 
                    and next_pos not in visited):
                    dist = abs(end_row - next_row) + abs(end_col - next_col)
                    directions.append((next_pos, dist))
            
            if not directions:
                if len(path) > 1:
                    path.pop()
                    current = path[-1]
                else:
                    break
                continue
            
            # 80% probabilidad hacia objetivo, 20% aleatorio
            if random.random() < 0.80:
                directions.sort(key=lambda x: x[1])
                next_pos = directions[0][0]
            else:
                next_pos = random.choice(directions)[0]
            
            visited.add(next_pos)
            path.append(next_pos)
            current = next_pos
            
        return path
