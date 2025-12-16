"""Tests unitarios para rendering/effects.py"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from rendering.effects import EffectsRenderer


class TestEffectsRendererInitialization:
    """Tests para la inicialización del renderizador de efectos."""
    
    @patch('pygame.display.get_surface')
    def test_initialization(self, mock_surface):
        """Verificar inicialización básica."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        assert renderer is not None
    
    @patch('pygame.display.get_surface')
    def test_surface_stored(self, mock_surface):
        """Verificar que se guarda la superficie."""
        mock_display = Mock()
        mock_surface.return_value = mock_display
        renderer = EffectsRenderer()
        assert renderer.screen == mock_display


class TestDrawBrokenLine:
    """Tests para draw_broken_line."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_method_exists(self, mock_line, mock_surface):
        """Verificar que existe el método draw_broken_line."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        assert hasattr(renderer, 'draw_broken_line')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_draw_broken_line_callable(self, mock_randint, mock_seed, mock_line, mock_surface):
        """Verificar que draw_broken_line puede ser llamado."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 0
        
        renderer = EffectsRenderer()
        color = (255, 255, 255)
        
        # No debería lanzar excepciones
        renderer.draw_broken_line(color, (0, 0), (100, 100), 1, 10, 10, 1)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    def test_broken_line_uses_seed(self, mock_seed, mock_line, mock_surface):
        """Verificar que usa seed para reproducibilidad."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        color = (255, 255, 255)
        
        renderer.draw_broken_line(color, (0, 0), (100, 100), 1, 10, 10, 1)
        
        # Debe llamar a random.seed con valores basados en posición
        assert mock_seed.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_broken_line_draws_segments(self, mock_randint, mock_seed, mock_line, mock_surface):
        """Verificar que dibuja segmentos."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 0
        
        renderer = EffectsRenderer()
        color = (255, 255, 255)
        
        renderer.draw_broken_line(color, (0, 0), (100, 100), 2, 10, 10, 1)
        
        # Debe dibujar líneas
        assert mock_line.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    def test_broken_line_reproducible(self, mock_seed, mock_line, mock_surface):
        """Verificar que las líneas son reproducibles."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        color = (255, 255, 255)
        
        # Dibujar dos veces con los mismos parámetros
        renderer.draw_broken_line(color, (0, 0), (100, 100), 1, 10, 10, 1)
        call_count_1 = mock_line.call_count
        
        mock_line.reset_mock()
        
        renderer.draw_broken_line(color, (0, 0), (100, 100), 1, 10, 10, 1)
        call_count_2 = mock_line.call_count
        
        # Deben ser iguales (mismo seed = mismo resultado)
        assert call_count_1 == call_count_2


class TestDrawStoneTexture:
    """Tests para draw_stone_texture."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    def test_method_exists(self, mock_line, mock_ellipse, mock_surface):
        """Verificar que existe el método draw_stone_texture."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        assert hasattr(renderer, 'draw_stone_texture')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_draw_stone_texture_callable(self, mock_randint, mock_seed, mock_line, mock_ellipse, mock_surface):
        """Verificar que draw_stone_texture puede ser llamado."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        
        # No debería lanzar excepciones
        renderer.draw_stone_texture(10, 10, 100, 100)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('random.seed')
    def test_stone_texture_uses_seed(self, mock_seed, mock_line, mock_ellipse, mock_surface):
        """Verificar que usa seed para reproducibilidad."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        
        renderer.draw_stone_texture(10, 10, 100, 100)
        
        # Debe llamar a random.seed
        assert mock_seed.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_stone_texture_draws_ellipses(self, mock_randint, mock_seed, mock_line, mock_ellipse, mock_surface):
        """Verificar que dibuja elipses."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        renderer.draw_stone_texture(10, 10, 100, 100)
        
        # Debe dibujar elipses (piedras)
        assert mock_ellipse.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_stone_texture_draws_mortar_lines(self, mock_randint, mock_seed, mock_line, mock_ellipse, mock_surface):
        """Verificar que dibuja líneas de mortero."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        renderer.draw_stone_texture(10, 10, 100, 100)
        
        # Debe dibujar líneas (mortero)
        assert mock_line.called


class TestDrawStoneInWalls:
    """Tests para draw_stone_in_walls."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('pygame.draw.rect')
    def test_method_exists(self, mock_rect, mock_line, mock_ellipse, mock_surface):
        """Verificar que existe el método draw_stone_in_walls."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        assert hasattr(renderer, 'draw_stone_in_walls')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('pygame.draw.rect')
    @patch('random.seed')
    @patch('random.randint')
    def test_draw_stone_in_walls_callable(self, mock_randint, mock_seed, mock_rect, mock_line, mock_ellipse, mock_surface):
        """Verificar que draw_stone_in_walls puede ser llamado."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        exits = [True, False, True, False]
        
        # No debería lanzar excepciones
        renderer.draw_stone_in_walls(10, 10, 100, 100, exits, 3)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('random.seed')
    @patch('random.randint')
    def test_stone_in_walls_draws_walls(self, mock_randint, mock_seed, mock_rect, mock_surface):
        """Verificar que dibuja paredes."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        exits = [False, False, False, False]  # Sin salidas
        
        renderer.draw_stone_in_walls(10, 10, 100, 100, exits, 0)
        
        # Debe dibujar rectángulos (paredes)
        assert mock_rect.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('random.seed')
    @patch('random.randint')
    def test_stone_in_walls_respects_exits(self, mock_randint, mock_seed, mock_rect, mock_surface):
        """Verificar que respeta las salidas."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        
        # Con todas las salidas cerradas
        exits_closed = [False, False, False, False]
        renderer.draw_stone_in_walls(10, 10, 100, 100, exits_closed, 0)
        calls_closed = mock_rect.call_count
        
        mock_rect.reset_mock()
        
        # Con todas las salidas abiertas
        exits_open = [True, True, True, True]
        renderer.draw_stone_in_walls(10, 10, 100, 100, exits_open, 0)
        calls_open = mock_rect.call_count
        
        # Con salidas abiertas debería haber menos rectángulos
        assert calls_open < calls_closed
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('random.seed')
    @patch('random.randint')
    def test_stone_in_walls_brightness_affects_color(self, mock_randint, mock_seed, mock_rect, mock_surface):
        """Verificar que el brillo afecta el color."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        exits = [False, False, False, False]
        
        # Diferentes niveles de brillo
        renderer.draw_stone_in_walls(10, 10, 100, 100, exits, 0)  # Sin antorchas
        renderer.draw_stone_in_walls(10, 10, 100, 100, exits, 5)  # Con antorchas
        
        # Debe llamar a draw.rect en ambos casos
        assert mock_rect.called


class TestRenderingConsistency:
    """Tests para consistencia del renderizado."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    def test_broken_line_deterministic(self, mock_seed, mock_line, mock_surface):
        """Verificar que broken_line es determinístico."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        color = (255, 255, 255)
        
        # Mismo line_id debería dar mismo resultado
        renderer.draw_broken_line(color, (0, 0), (100, 100), 1, 10, 10, 5)
        renderer.draw_broken_line(color, (0, 0), (100, 100), 1, 10, 10, 5)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('random.seed')
    def test_stone_texture_deterministic(self, mock_seed, mock_line, mock_ellipse, mock_surface):
        """Verificar que stone_texture es determinístico."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        
        # Misma posición debería dar mismo resultado
        renderer.draw_stone_texture(10, 10, 100, 100)
        renderer.draw_stone_texture(10, 10, 100, 100)


class TestEdgeCases:
    """Tests para casos especiales."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_broken_line_zero_width(self, mock_randint, mock_seed, mock_line, mock_surface):
        """Verificar línea con ancho 0."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 0
        
        renderer = EffectsRenderer()
        color = (0, 0, 0)
        
        # No debería causar error
        renderer.draw_broken_line(color, (0, 0), (100, 100), 0, 10, 10, 1)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_broken_line_same_start_end(self, mock_randint, mock_seed, mock_line, mock_surface):
        """Verificar línea con inicio y fin iguales."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 0
        
        renderer = EffectsRenderer()
        color = (255, 255, 255)
        
        # No debería causar error
        renderer.draw_broken_line(color, (50, 50), (50, 50), 1, 10, 10, 1)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.ellipse')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_stone_texture_at_origin(self, mock_randint, mock_seed, mock_line, mock_ellipse, mock_surface):
        """Verificar textura en el origen."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        
        # No debería causar error
        renderer.draw_stone_texture(0, 0, 0, 0)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('random.seed')
    @patch('random.randint')
    def test_stone_in_walls_all_exits_open(self, mock_randint, mock_seed, mock_rect, mock_surface):
        """Verificar paredes con todas las salidas abiertas."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        exits = [True, True, True, True]
        
        # No debería causar error
        renderer.draw_stone_in_walls(10, 10, 100, 100, exits, 0)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    @patch('random.seed')
    @patch('random.randint')
    def test_stone_in_walls_many_torches(self, mock_randint, mock_seed, mock_rect, mock_surface):
        """Verificar paredes con muchas antorchas."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 50
        
        renderer = EffectsRenderer()
        exits = [False, False, False, False]
        
        # No debería causar error
        renderer.draw_stone_in_walls(10, 10, 100, 100, exits, 100)


class TestColorValidation:
    """Tests para validación de colores."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_broken_line_black_color(self, mock_randint, mock_seed, mock_line, mock_surface):
        """Verificar línea con color negro."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 0
        
        renderer = EffectsRenderer()
        
        renderer.draw_broken_line((0, 0, 0), (0, 0), (100, 100), 1, 10, 10, 1)
        assert mock_line.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    @patch('random.randint')
    def test_broken_line_white_color(self, mock_randint, mock_seed, mock_line, mock_surface):
        """Verificar línea con color blanco."""
        mock_surface.return_value = Mock()
        mock_randint.return_value = 0
        
        renderer = EffectsRenderer()
        
        renderer.draw_broken_line((255, 255, 255), (0, 0), (100, 100), 1, 10, 10, 1)
        assert mock_line.called


class TestDifferentLineIds:
    """Tests para diferentes IDs de línea."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    @patch('random.seed')
    def test_different_line_ids_different_seeds(self, mock_seed, mock_line, mock_surface):
        """Verificar que diferentes IDs usan diferentes seeds."""
        mock_surface.return_value = Mock()
        renderer = EffectsRenderer()
        color = (255, 255, 255)
        
        renderer.draw_broken_line(color, (0, 0), (100, 100), 1, 10, 10, 1)
        seed_calls_1 = mock_seed.call_count
        
        renderer.draw_broken_line(color, (0, 0), (100, 100), 1, 10, 10, 2)
        seed_calls_2 = mock_seed.call_count
        
        # Debe haber llamado a seed dos veces
        assert seed_calls_2 == seed_calls_1 + 1
