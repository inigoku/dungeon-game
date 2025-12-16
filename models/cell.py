"""Cell and related enums for the dungeon."""
from enum import Enum
from dataclasses import dataclass


class CellType(Enum):
    """Types of cells in the dungeon."""
    EMPTY = 0
    INICIO = 1
    PASILLO = 2
    HABITACION = 3
    SALIDA = 4


class Direction(Enum):
    """Cardinal directions for exits."""
    N = "N"
    E = "E"
    S = "S"
    O = "O"


@dataclass
class Cell:
    """Represents a single cell in the dungeon."""
    cell_type: CellType
    exits: set = None
    
    def __post_init__(self):
        if self.exits is None:
            self.exits = set()
