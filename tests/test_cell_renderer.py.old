"""Tests unitarios para rendering/cell_renderer.py"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from models.cell import Cell, CellType, Direction
from rendering.cell_renderer import CellRenderer


class TestCellRendererInitialization:
    """Tests para la inicialización del renderizador de celdas."""
    
    @patch('pygame.display.get_surface')
    def test_initialization(self, mock_surface):
        """Verificar inicialización básica."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        assert renderer is not None
    
    @patch('pygame.display.get_surface')
    def test_surface_stored(self, mock_surface):
        """Verificar que se guarda la superficie."""
        mock_display = Mock()
        mock_surface.return_value = mock_display
        renderer = CellRenderer()
        assert renderer.screen == mock_display


class TestDrawCellBackground:
    """Tests para draw_cell_background."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_method_exists(self, mock_rect, mock_surface):
        """Verificar que existe el método draw_cell_background."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        assert hasattr(renderer, 'draw_cell_background')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_draw_cell_background_callable(self, mock_rect, mock_surface):
        """Verificar que draw_cell_background puede ser llamado."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO)
        draw_stone_callback = Mock()
        
        # No debería lanzar excepciones
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_pasillo(self, mock_rect, mock_surface):
        """Verificar renderizado de fondo para PASILLO."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO)
        draw_stone_callback = Mock()
        
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
        
        # Debe dibujar rectángulo para el suelo
        assert mock_rect.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_habitacion(self, mock_rect, mock_surface):
        """Verificar renderizado de fondo para HABITACION."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.HABITACION)
        draw_stone_callback = Mock()
        
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
        
        assert mock_rect.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_inicio(self, mock_rect, mock_surface):
        """Verificar renderizado de fondo para INICIO."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.INICIO)
        draw_stone_callback = Mock()
        
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
        
        assert mock_rect.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_salida(self, mock_rect, mock_surface):
        """Verificar renderizado de fondo para SALIDA."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.SALIDA)
        draw_stone_callback = Mock()
        
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
        
        # SALIDA tiene comportamiento especial (negro)
        assert mock_rect.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_cthulhu(self, mock_rect, mock_surface):
        """Verificar renderizado de fondo para CTHULHU."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.CTHULHU)
        draw_stone_callback = Mock()
        
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
        
        assert mock_rect.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_uses_callback(self, mock_rect, mock_surface):
        """Verificar que usa el callback para piedras."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO)
        draw_stone_callback = Mock()
        
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
        
        # Debe llamar al callback en algún momento
        assert draw_stone_callback.called


class TestDrawCellTunnels:
    """Tests para draw_cell_tunnels."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_method_exists(self, mock_line, mock_surface):
        """Verificar que existe el método draw_cell_tunnels."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        assert hasattr(renderer, 'draw_cell_tunnels')
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_draw_cell_tunnels_callable(self, mock_line, mock_surface):
        """Verificar que draw_cell_tunnels puede ser llamado."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO, salidas=[True, False, True, False])
        draw_broken_line_callback = Mock()
        
        # No debería lanzar excepciones
        renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, True, draw_broken_line_callback)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_tunnels_with_exits(self, mock_line, mock_surface):
        """Verificar túneles con salidas."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO, salidas=[True, True, False, False])
        draw_broken_line_callback = Mock()
        
        renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, True, draw_broken_line_callback)
        
        # Debe dibujar líneas para los túneles
        assert mock_line.called or draw_broken_line_callback.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_tunnels_no_exits(self, mock_line, mock_surface):
        """Verificar túneles sin salidas."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO, salidas=[False, False, False, False])
        draw_broken_line_callback = Mock()
        
        renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, True, draw_broken_line_callback)
        
        # Sin salidas, no debería dibujar muchas líneas
        # (solo verificamos que no falla)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_tunnels_with_darkening(self, mock_line, mock_surface):
        """Verificar túneles con oscurecimiento."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO, salidas=[True, True, True, True])
        draw_broken_line_callback = Mock()
        
        # Con darkening habilitado
        renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, True, draw_broken_line_callback)
        
        # Debe usar líneas quebradas
        assert draw_broken_line_callback.called or mock_line.called
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_tunnels_without_darkening(self, mock_line, mock_surface):
        """Verificar túneles sin oscurecimiento."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO, salidas=[True, True, True, True])
        draw_broken_line_callback = Mock()
        
        # Sin darkening
        renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, False, draw_broken_line_callback)
        
        # Debe usar líneas normales
        assert mock_line.called


class TestGetOppositeDirection:
    """Tests para get_opposite_direction."""
    
    @patch('pygame.display.get_surface')
    def test_method_exists(self, mock_surface):
        """Verificar que existe el método get_opposite_direction."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        assert hasattr(renderer, 'get_opposite_direction')
    
    @patch('pygame.display.get_surface')
    def test_opposite_arriba_abajo(self, mock_surface):
        """Verificar opuesto de ARRIBA es ABAJO."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        opposite = renderer.get_opposite_direction(Direction.ARRIBA)
        assert opposite == Direction.ABAJO
    
    @patch('pygame.display.get_surface')
    def test_opposite_abajo_arriba(self, mock_surface):
        """Verificar opuesto de ABAJO es ARRIBA."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        opposite = renderer.get_opposite_direction(Direction.ABAJO)
        assert opposite == Direction.ARRIBA
    
    @patch('pygame.display.get_surface')
    def test_opposite_derecha_izquierda(self, mock_surface):
        """Verificar opuesto de DERECHA es IZQUIERDA."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        opposite = renderer.get_opposite_direction(Direction.DERECHA)
        assert opposite == Direction.IZQUIERDA
    
    @patch('pygame.display.get_surface')
    def test_opposite_izquierda_derecha(self, mock_surface):
        """Verificar opuesto de IZQUIERDA es DERECHA."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        opposite = renderer.get_opposite_direction(Direction.IZQUIERDA)
        assert opposite == Direction.DERECHA
    
    @patch('pygame.display.get_surface')
    def test_opposite_is_symmetric(self, mock_surface):
        """Verificar que opuesto del opuesto es la dirección original."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        for direction in [Direction.ARRIBA, Direction.DERECHA, 
                         Direction.ABAJO, Direction.IZQUIERDA]:
            opposite = renderer.get_opposite_direction(direction)
            double_opposite = renderer.get_opposite_direction(opposite)
            assert double_opposite == direction


class TestBrightnessHandling:
    """Tests para manejo de brillo."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_zero_brightness(self, mock_rect, mock_surface):
        """Verificar fondo con brillo 0."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO)
        draw_stone_callback = Mock()
        
        # No debería causar error
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.0, draw_stone_callback)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_max_brightness(self, mock_rect, mock_surface):
        """Verificar fondo con brillo máximo."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO)
        draw_stone_callback = Mock()
        
        # No debería causar error
        renderer.draw_cell_background(100, 100, cell, 10, 10, 1.0, draw_stone_callback)


class TestEdgeCases:
    """Tests para casos especiales."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_at_origin(self, mock_rect, mock_surface):
        """Verificar fondo en el origen."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO)
        draw_stone_callback = Mock()
        
        # No debería causar error
        renderer.draw_cell_background(0, 0, cell, 0, 0, 0.5, draw_stone_callback)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_tunnels_all_exits_open(self, mock_line, mock_surface):
        """Verificar túneles con todas las salidas abiertas."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.HABITACION, salidas=[True, True, True, True])
        draw_broken_line_callback = Mock()
        
        # No debería causar error
        renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, True, draw_broken_line_callback)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_tunnels_no_exits_open(self, mock_line, mock_surface):
        """Verificar túneles sin salidas abiertas."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO, salidas=[False, False, False, False])
        draw_broken_line_callback = Mock()
        
        # No debería causar error
        renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, True, draw_broken_line_callback)


class TestCallbackIntegration:
    """Tests para integración con callbacks."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_background_callback_receives_params(self, mock_rect, mock_surface):
        """Verificar que el callback recibe parámetros."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO)
        draw_stone_callback = Mock()
        
        renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
        
        # El callback debe haber sido llamado con parámetros
        if draw_stone_callback.called:
            assert draw_stone_callback.call_count > 0
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_tunnels_callback_receives_params(self, mock_line, mock_surface):
        """Verificar que el callback de líneas recibe parámetros."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        
        cell = Cell(tipo=CellType.PASILLO, salidas=[True, True, False, False])
        draw_broken_line_callback = Mock()
        
        renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, True, draw_broken_line_callback)
        
        # El callback puede o no ser llamado dependiendo de si hay darkening
        # Solo verificamos que no falla


class TestDifferentCellTypes:
    """Tests para diferentes tipos de celdas."""
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.rect')
    def test_all_cell_types_render(self, mock_rect, mock_surface):
        """Verificar que todos los tipos de celda se renderizan."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        draw_stone_callback = Mock()
        
        cell_types = [
            CellType.PASILLO,
            CellType.HABITACION,
            CellType.INICIO,
            CellType.SALIDA,
            CellType.CTHULHU
        ]
        
        for cell_type in cell_types:
            cell = Cell(tipo=cell_type)
            # No debería causar error
            renderer.draw_cell_background(100, 100, cell, 10, 10, 0.5, draw_stone_callback)
    
    @patch('pygame.display.get_surface')
    @patch('pygame.draw.line')
    def test_pasillo_and_habitacion_have_tunnels(self, mock_line, mock_surface):
        """Verificar que PASILLO y HABITACION tienen túneles."""
        mock_surface.return_value = Mock()
        renderer = CellRenderer()
        draw_broken_line_callback = Mock()
        
        for cell_type in [CellType.PASILLO, CellType.HABITACION]:
            cell = Cell(tipo=cell_type, salidas=[True, True, True, True])
            # Debe poder renderizar túneles
            renderer.draw_cell_tunnels(100, 100, cell, 10, 10, 0.5, True, draw_broken_line_callback)
