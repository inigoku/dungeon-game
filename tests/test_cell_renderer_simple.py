"""Tests simplificados para rendering/cell_renderer.py"""
import pytest
from unittest.mock import Mock
from rendering.cell_renderer import CellRenderer
from models.cell import Direction


class TestCellRendererBasics:
    """Tests básicos del renderizador de celdas."""
    
    def test_initialization(self):
        """Verificar inicialización básica."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        assert renderer is not None
    
    def test_stores_screen(self):
        """Verificar que guarda la referencia a screen."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        assert renderer.screen == mock_screen
    
    def test_stores_cell_size(self):
        """Verificar que guarda el tamaño de celda."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        assert renderer.cell_size == 90
    
    def test_stores_size(self):
        """Verificar que guarda el tamaño del tablero."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        assert renderer.size == 11
    
    def test_has_draw_cell_background(self):
        """Verificar que tiene método draw_cell_background."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        assert hasattr(renderer, 'draw_cell_background')
        assert callable(renderer.draw_cell_background)
    
    def test_has_draw_cell_tunnels(self):
        """Verificar que tiene método draw_cell_tunnels."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        assert hasattr(renderer, 'draw_cell_tunnels')
        assert callable(renderer.draw_cell_tunnels)
    
    def test_has_get_opposite_direction(self):
        """Verificar que tiene método get_opposite_direction."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        assert hasattr(renderer, 'get_opposite_direction')
        assert callable(renderer.get_opposite_direction)
    
    def test_get_opposite_direction_north(self):
        """Verificar dirección opuesta de NORTH."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        opposite = renderer.get_opposite_direction(Direction.N)
        assert opposite == Direction.S
    
    def test_get_opposite_direction_south(self):
        """Verificar dirección opuesta de SOUTH."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        opposite = renderer.get_opposite_direction(Direction.S)
        assert opposite == Direction.N
    
    def test_get_opposite_direction_east(self):
        """Verificar dirección opuesta de EAST."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        opposite = renderer.get_opposite_direction(Direction.E)
        assert opposite == Direction.O
    
    def test_get_opposite_direction_west(self):
        """Verificar dirección opuesta de WEST."""
        mock_screen = Mock()
        renderer = CellRenderer(mock_screen, 90, 11)
        opposite = renderer.get_opposite_direction(Direction.O)
        assert opposite == Direction.E
    
    def test_different_board_sizes(self):
        """Verificar que acepta diferentes tamaños de tablero."""
        mock_screen = Mock()
        sizes = [7, 9, 11, 13, 15]
        
        for size in sizes:
            renderer = CellRenderer(mock_screen, 90, size)
            assert renderer.size == size
