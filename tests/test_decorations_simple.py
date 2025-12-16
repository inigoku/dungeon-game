"""Tests simplificados para rendering/decorations.py"""
import pytest
from unittest.mock import Mock
from rendering.decorations import DecorationRenderer


class TestDecorationRendererBasics:
    """Tests básicos del renderizador de decoraciones."""
    
    def test_initialization(self):
        """Verificar inicialización básica."""
        mock_screen = Mock()
        renderer = DecorationRenderer(mock_screen, 90)
        assert renderer is not None
    
    def test_stores_screen(self):
        """Verificar que guarda la referencia a screen."""
        mock_screen = Mock()
        renderer = DecorationRenderer(mock_screen, 90)
        assert renderer.screen == mock_screen
    
    def test_stores_cell_size(self):
        """Verificar que guarda el tamaño de celda."""
        mock_screen = Mock()
        renderer = DecorationRenderer(mock_screen, 90)
        assert renderer.cell_size == 90
    
    def test_has_draw_blood_stains(self):
        """Verificar que tiene método draw_blood_stains."""
        mock_screen = Mock()
        renderer = DecorationRenderer(mock_screen, 90)
        assert hasattr(renderer, 'draw_blood_stains')
        assert callable(renderer.draw_blood_stains)
    
    def test_has_draw_torches(self):
        """Verificar que tiene método draw_torches."""
        mock_screen = Mock()
        renderer = DecorationRenderer(mock_screen, 90)
        assert hasattr(renderer, 'draw_torches')
        assert callable(renderer.draw_torches)
    
    def test_has_draw_fountain(self):
        """Verificar que tiene método draw_fountain."""
        mock_screen = Mock()
        renderer = DecorationRenderer(mock_screen, 90)
        assert hasattr(renderer, 'draw_fountain')
        assert callable(renderer.draw_fountain)
    
    def test_has_draw_spiral_stairs(self):
        """Verificar que tiene método draw_spiral_stairs."""
        mock_screen = Mock()
        renderer = DecorationRenderer(mock_screen, 90)
        assert hasattr(renderer, 'draw_spiral_stairs')
        assert callable(renderer.draw_spiral_stairs)
    
    def test_different_cell_sizes(self):
        """Verificar que acepta diferentes tamaños de celda."""
        mock_screen = Mock()
        sizes = [50, 90, 100, 120]
        
        for size in sizes:
            renderer = DecorationRenderer(mock_screen, size)
            assert renderer.cell_size == size
