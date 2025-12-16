"""Tests simplificados para rendering/effects.py"""
import pytest
from unittest.mock import Mock
from rendering.effects import EffectsRenderer


class TestEffectsRendererBasics:
    """Tests básicos del renderizador de efectos."""
    
    def test_initialization(self):
        """Verificar inicialización básica."""
        mock_screen = Mock()
        renderer = EffectsRenderer(mock_screen, 90)
        assert renderer is not None
    
    def test_stores_screen(self):
        """Verificar que guarda la referencia a screen."""
        mock_screen = Mock()
        renderer = EffectsRenderer(mock_screen, 90)
        assert renderer.screen == mock_screen
    
    def test_stores_cell_size(self):
        """Verificar que guarda el tamaño de celda."""
        mock_screen = Mock()
        renderer = EffectsRenderer(mock_screen, 90)
        assert renderer.cell_size == 90
    
    def test_has_draw_broken_line(self):
        """Verificar que tiene método draw_broken_line."""
        mock_screen = Mock()
        renderer = EffectsRenderer(mock_screen, 90)
        assert hasattr(renderer, 'draw_broken_line')
        assert callable(renderer.draw_broken_line)
    
    def test_has_draw_stone_texture(self):
        """Verificar que tiene método draw_stone_texture."""
        mock_screen = Mock()
        renderer = EffectsRenderer(mock_screen, 90)
        assert hasattr(renderer, 'draw_stone_texture')
        assert callable(renderer.draw_stone_texture)
    
    def test_has_draw_stone_in_walls(self):
        """Verificar que tiene método draw_stone_in_walls."""
        mock_screen = Mock()
        renderer = EffectsRenderer(mock_screen, 90)
        assert hasattr(renderer, 'draw_stone_in_walls')
        assert callable(renderer.draw_stone_in_walls)
    
    def test_different_cell_sizes(self):
        """Verificar que acepta diferentes tamaños de celda."""
        mock_screen = Mock()
        sizes = [50, 90, 100, 120]
        
        for size in sizes:
            renderer = EffectsRenderer(mock_screen, size)
            assert renderer.cell_size == size
