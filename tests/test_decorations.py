"""Tests unitarios para rendering/decorations.py"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from models.cell import Cell, CellType, Direction
from rendering.decorations import DecorationRenderer


class TestDecorationRendererInitialization:
    """Tests para la inicialización del renderizador."""
    
    @patch('pygame.display.get_surface')
    def test_initialization(self, mock_surface):
        """Verificar inicialización básica."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        assert renderer is not None
    
    @patch('pygame.display.get_surface')
    def test_surface_stored(self, mock_surface):
        """Verificar que se guarda la superficie."""
        mock_display = Mock()
        mock_surface.return_value = mock_display
        renderer = DecorationRenderer()
        assert renderer.screen == mock_display


class TestDrawBloodStains:
    """Tests para draw_blood_stains."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    def test_method_exists(self, mock_circle, mock_surface):
        """Verificar que existe el método draw_blood_stains."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        assert hasattr(renderer, 'draw_blood_stains')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('random.seed')
    @patch('random.randint')
    def test_draw_blood_stains_callable(self, mock_randint, mock_seed, mock_circle, mock_surface):
        """Verificar que draw_blood_stains puede ser llamado."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 3
        
        renderer = DecorationRenderer()
        exit_pos = (50, 50)
        
        # No debería lanzar excepciones
        renderer.draw_blood_stains(10, 10, 100, 100, 0.5, exit_pos)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('random.seed')
    def test_blood_stains_uses_seed(self, mock_seed, mock_circle, mock_surface):
        """Verificar que usa seed para reproducibilidad."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        exit_pos = (50, 50)
        
        renderer.draw_blood_stains(10, 10, 100, 100, 0.5, exit_pos)
        
        # Debe llamar a random.seed
        assert mock_seed.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    def test_blood_stains_distance_based(self, mock_circle, mock_surface):
        """Verificar que las manchas dependen de la distancia."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        exit_pos = (50, 50)
        
        # Cerca de la salida - pocas manchas
        renderer.draw_blood_stains(50, 51, 100, 100, 0.5, exit_pos)
        
        # Lejos de la salida - más manchas
        renderer.draw_blood_stains(10, 10, 100, 100, 0.5, exit_pos)
        
        # Debe llamar a pygame.draw.circle
        assert mock_circle.called


class TestDrawTorches:
    """Tests para draw_torches."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('pygame.time.get_ticks')
    def test_method_exists(self, mock_ticks, mock_circle, mock_surface):
        """Verificar que existe el método draw_torches."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        assert hasattr(renderer, 'draw_torches')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('pygame.time.get_ticks')
    def test_draw_torches_callable(self, mock_ticks, mock_circle, mock_surface):
        """Verificar que draw_torches puede ser llamado."""
        mock_surface.return_value = Mock()
        mock_ticks.return_value = 1000
        
        renderer = DecorationRenderer()
        cell = Cell(salidas=[True, False, True, False])
        
        # No debería lanzar excepciones
        renderer.draw_torches(10, 10, 100, 100, cell, 2)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('pygame.time.get_ticks')
    def test_torches_animated(self, mock_ticks, mock_circle, mock_surface):
        """Verificar que las antorchas están animadas."""
        mock_surface.return_value = Mock()
        mock_ticks.return_value = 1000
        
        renderer = DecorationRenderer()
        cell = Cell(salidas=[True, False, True, False])
        
        renderer.draw_torches(10, 10, 100, 100, cell, 2)
        
        # Debe usar el tiempo para animación
        mock_ticks.assert_called()
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('pygame.time.get_ticks')
    def test_torches_respect_exits(self, mock_ticks, mock_circle, mock_surface):
        """Verificar que las antorchas respetan las salidas."""
        mock_surface.return_value = Mock()
        mock_ticks.return_value = 1000
        
        renderer = DecorationRenderer()
        cell = Cell(salidas=[True, True, True, True])  # Todas las salidas
        
        # Con todas las salidas abiertas, no debería haber antorchas
        renderer.draw_torches(10, 10, 100, 100, cell, 0)


class TestDrawFountain:
    """Tests para draw_fountain."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('pygame.draw.circle')
    def test_method_exists(self, mock_circle, mock_rect, mock_surface):
        """Verificar que existe el método draw_fountain."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        assert hasattr(renderer, 'draw_fountain')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('pygame.draw.circle')
    def test_draw_fountain_callable(self, mock_circle, mock_rect, mock_surface):
        """Verificar que draw_fountain puede ser llamado."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        
        # No debería lanzar excepciones
        renderer.draw_fountain(100, 100)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('pygame.draw.circle')
    def test_fountain_draws_shapes(self, mock_circle, mock_rect, mock_surface):
        """Verificar que la fuente dibuja formas."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        
        renderer.draw_fountain(100, 100)
        
        # Debe dibujar al menos un círculo (agua)
        assert mock_circle.called


class TestDrawSpiralStairs:
    """Tests para draw_spiral_stairs."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_method_exists(self, mock_rect, mock_surface):
        """Verificar que existe el método draw_spiral_stairs."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        assert hasattr(renderer, 'draw_spiral_stairs')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_draw_spiral_stairs_callable(self, mock_rect, mock_surface):
        """Verificar que draw_spiral_stairs puede ser llamado."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        
        # No debería lanzar excepciones
        renderer.draw_spiral_stairs(100, 100)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_spiral_stairs_draws_steps(self, mock_rect, mock_surface):
        """Verificar que las escaleras dibujan escalones."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        
        renderer.draw_spiral_stairs(100, 100)
        
        # Debe dibujar rectángulos para los escalones
        assert mock_rect.called
        # Debería haber 8 escalones
        assert mock_rect.call_count >= 8


class TestRenderingConsistency:
    """Tests para consistencia del renderizado."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('random.seed')
    def test_blood_stains_reproducible(self, mock_seed, mock_circle, mock_surface):
        """Verificar que las manchas son reproducibles con seed."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        exit_pos = (50, 50)
        
        # Dibujar dos veces con los mismos parámetros
        renderer.draw_blood_stains(10, 10, 100, 100, 0.5, exit_pos)
        call_count_1 = mock_circle.call_count
        
        mock_circle.reset_mock()
        
        renderer.draw_blood_stains(10, 10, 100, 100, 0.5, exit_pos)
        call_count_2 = mock_circle.call_count
        
        # Deben ser iguales (mismo seed = mismo resultado)
        assert call_count_1 == call_count_2


class TestEdgeCases:
    """Tests para casos especiales."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    def test_blood_stains_zero_brightness(self, mock_circle, mock_surface):
        """Verificar manchas con brillo 0."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        exit_pos = (50, 50)
        
        # No debería causar error
        renderer.draw_blood_stains(10, 10, 100, 100, 0.0, exit_pos)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    def test_blood_stains_max_brightness(self, mock_circle, mock_surface):
        """Verificar manchas con brillo máximo."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        exit_pos = (50, 50)
        
        # No debería causar error
        renderer.draw_blood_stains(10, 10, 100, 100, 1.0, exit_pos)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('pygame.time.get_ticks')
    def test_torches_zero_count(self, mock_ticks, mock_circle, mock_surface):
        """Verificar antorchas con cuenta 0."""
        mock_surface.return_value = Mock()
        mock_ticks.return_value = 1000
        
        renderer = DecorationRenderer()
        cell = Cell()
        
        # No debería causar error
        renderer.draw_torches(10, 10, 100, 100, cell, 0)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('pygame.time.get_ticks')
    def test_torches_many_count(self, mock_ticks, mock_circle, mock_surface):
        """Verificar antorchas con muchas antorchas."""
        mock_surface.return_value = Mock()
        mock_ticks.return_value = 1000
        
        renderer = DecorationRenderer()
        cell = Cell(salidas=[False, False, False, False])
        
        # No debería causar error
        renderer.draw_torches(10, 10, 100, 100, cell, 10)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('pygame.draw.circle')
    def test_fountain_at_origin(self, mock_circle, mock_rect, mock_surface):
        """Verificar fuente en el origen."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        
        # No debería causar error
        renderer.draw_fountain(0, 0)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_stairs_at_origin(self, mock_rect, mock_surface):
        """Verificar escaleras en el origen."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        
        # No debería causar error
        renderer.draw_spiral_stairs(0, 0)


class TestParameterValidation:
    """Tests para validación de parámetros."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    def test_blood_stains_accepts_valid_params(self, mock_circle, mock_surface):
        """Verificar que blood_stains acepta parámetros válidos."""
        mock_surface.return_value = Mock()
        renderer = DecorationRenderer()
        exit_pos = (50, 50)
        
        # Todos estos deben funcionar
        renderer.draw_blood_stains(0, 0, 0, 0, 0.5, exit_pos)
        renderer.draw_blood_stains(100, 100, 500, 500, 0.8, exit_pos)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.circle')
    @patch('pygame.time.get_ticks')
    def test_torches_accepts_different_cells(self, mock_ticks, mock_circle, mock_surface):
        """Verificar que torches acepta diferentes tipos de celdas."""
        mock_surface.return_value = Mock()
        mock_ticks.return_value = 1000
        renderer = DecorationRenderer()
        
        # Diferentes configuraciones de salidas
        cell1 = Cell(salidas=[True, False, False, False])
        cell2 = Cell(salidas=[True, True, False, False])
        cell3 = Cell(salidas=[True, True, True, True])
        
        # Todas deben funcionar
        renderer.draw_torches(0, 0, 100, 100, cell1, 1)
        renderer.draw_torches(0, 0, 100, 100, cell2, 2)
        renderer.draw_torches(0, 0, 100, 100, cell3, 3)
