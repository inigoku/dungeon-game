"""Tests unitarios para models/cell.py"""
import pytest
from models.cell import Cell, CellType, Direction


class TestDirection:
    """Tests para la clase Direction."""
    
    def test_direction_values(self):
        """Verificar que las direcciones tienen los valores correctos."""
        assert Direction.N.value == "N"
        assert Direction.E.value == "E"
        assert Direction.S.value == "S"
        assert Direction.O.value == "O"
    
    def test_direction_count(self):
        """Verificar que hay exactamente 4 direcciones."""
        directions = list(Direction)
        assert len(directions) == 4


class TestCellType:
    """Tests para la clase CellType."""
    
    def test_celltype_values(self):
        """Verificar que los tipos de celda existen."""
        assert CellType.EMPTY.value == 0
        assert CellType.INICIO.value == 1
        assert CellType.PASILLO.value == 2
        assert CellType.HABITACION.value == 3
        assert CellType.SALIDA.value == 4
    
    def test_celltype_count(self):
        """Verificar que hay exactamente 5 tipos de celda."""
        cell_types = list(CellType)
        assert len(cell_types) == 5


class TestCell:
    """Tests para la clase Cell."""
    
    def test_cell_initialization_default(self):
        """Verificar inicialización de Cell con tipo."""
        cell = Cell(cell_type=CellType.PASILLO)
        assert cell.cell_type == CellType.PASILLO
        assert cell.exits == set()
    
    def test_cell_initialization_custom_type(self):
        """Verificar inicialización con tipo personalizado."""
        cell = Cell(cell_type=CellType.HABITACION)
        assert cell.cell_type == CellType.HABITACION
        assert cell.exits == set()
    
    def test_cell_initialization_with_exits(self):
        """Verificar inicialización con salidas."""
        exits = {Direction.N, Direction.S}
        cell = Cell(cell_type=CellType.PASILLO, exits=exits)
        assert cell.exits == exits
        assert cell.cell_type == CellType.PASILLO
    
    def test_cell_exits_mutable(self):
        """Verificar que las salidas son mutables."""
        cell = Cell(cell_type=CellType.PASILLO)
        assert Direction.N not in cell.exits
        cell.exits.add(Direction.N)
        assert Direction.N in cell.exits
    
    def test_cell_type_change(self):
        """Verificar que el tipo de celda puede cambiar."""
        cell = Cell(cell_type=CellType.PASILLO)
        assert cell.cell_type == CellType.PASILLO
        cell.cell_type = CellType.HABITACION
        assert cell.cell_type == CellType.HABITACION
    
    def test_multiple_cells_independent(self):
        """Verificar que múltiples celdas son independientes."""
        cell1 = Cell(cell_type=CellType.PASILLO)
        cell2 = Cell(cell_type=CellType.HABITACION)
        
        cell1.exits.add(Direction.N)
        
        # cell2 no debe verse afectada
        assert Direction.N not in cell2.exits
        assert cell2.cell_type == CellType.HABITACION
    
    def test_cell_all_exits_open(self):
        """Verificar celda con todas las salidas abiertas."""
        all_exits = {Direction.N, Direction.E, Direction.S, Direction.O}
        cell = Cell(cell_type=CellType.PASILLO, exits=all_exits)
        assert len(cell.exits) == 4
    
    def test_cell_no_exits_open(self):
        """Verificar celda sin salidas."""
        cell = Cell(cell_type=CellType.PASILLO)
        assert len(cell.exits) == 0
    
    def test_cell_special_types(self):
        """Verificar tipos especiales de celdas."""
        inicio = Cell(cell_type=CellType.INICIO)
        salida = Cell(cell_type=CellType.SALIDA)
        empty = Cell(cell_type=CellType.EMPTY)
        
        assert inicio.cell_type == CellType.INICIO
        assert salida.cell_type == CellType.SALIDA
        assert empty.cell_type == CellType.EMPTY
    
    def test_cell_exits_set_operations(self):
        """Verificar operaciones con el conjunto de salidas."""
        cell = Cell(cell_type=CellType.PASILLO)
        cell.exits.add(Direction.N)
        cell.exits.add(Direction.S)
        
        assert len(cell.exits) == 2
        assert Direction.N in cell.exits
        assert Direction.S in cell.exits
        assert Direction.E not in cell.exits
        
        cell.exits.remove(Direction.N)
        assert len(cell.exits) == 1
        assert Direction.N not in cell.exits
