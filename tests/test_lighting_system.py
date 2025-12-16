"""Tests unitarios para services/lighting_system.py"""
import pytest
from models.cell import Cell, CellType
from services.lighting_system import LightingSystem


class TestLightingSystemInitialization:
    """Tests para la inicialización del sistema de iluminación."""
    
    def test_initialization(self):
        """Verificar inicialización básica."""
        lighting = LightingSystem()
        assert lighting is not None
    
    def test_initial_state(self):
        """Verificar estado inicial."""
        lighting = LightingSystem()
        # El sistema debe estar listo para calcular iluminación
        assert hasattr(lighting, 'calculate_brightness')
        assert hasattr(lighting, 'calculate_lines_brightness')


class TestCalculateBrightness:
    """Tests para calculate_brightness."""
    
    @pytest.fixture
    def lighting(self):
        """Fixture para crear instancia de LightingSystem."""
        return LightingSystem()
    
    def test_entrance_brightness(self, lighting):
        """Verificar brillo en la entrada."""
        cell = Cell(tipo=CellType.INICIO)
        distance = 0  # En la entrada
        exit_pos = (50, 50)
        
        brightness = lighting.calculate_brightness(0, 0, exit_pos, cell)
        assert brightness >= 20  # BASE_BRIGHTNESS_ENTRANCE
    
    def test_exit_brightness_zero(self, lighting):
        """Verificar brillo en la salida es 0."""
        cell = Cell(tipo=CellType.SALIDA)
        exit_pos = (10, 10)
        
        brightness = lighting.calculate_brightness(10, 10, exit_pos, cell)
        assert brightness == 0
    
    def test_brightness_decreases_with_distance(self, lighting):
        """Verificar que el brillo disminuye con la distancia."""
        cell = Cell(tipo=CellType.PASILLO)
        exit_pos = (50, 50)
        
        brightness_near = lighting.calculate_brightness(51, 50, exit_pos, cell)
        brightness_far = lighting.calculate_brightness(60, 50, exit_pos, cell)
        
        assert brightness_near > brightness_far
    
    def test_torches_increase_brightness(self, lighting):
        """Verificar que las antorchas aumentan el brillo."""
        exit_pos = (50, 50)
        cell_no_torches = Cell(num_antorchas=0)
        cell_with_torches = Cell(num_antorchas=3)
        
        brightness_no_torches = lighting.calculate_brightness(10, 10, exit_pos, cell_no_torches)
        brightness_with_torches = lighting.calculate_brightness(10, 10, exit_pos, cell_with_torches)
        
        assert brightness_with_torches > brightness_no_torches
    
    def test_max_brightness_capped(self, lighting):
        """Verificar que el brillo máximo está limitado."""
        cell = Cell(num_antorchas=10)  # Muchas antorchas
        exit_pos = (50, 50)
        
        brightness = lighting.calculate_brightness(0, 0, exit_pos, cell)
        assert brightness <= 255  # Máximo RGB
    
    def test_brightness_non_negative(self, lighting):
        """Verificar que el brillo nunca es negativo."""
        cell = Cell()
        exit_pos = (0, 0)
        
        # Probar varias distancias
        for i in range(0, 100, 10):
            brightness = lighting.calculate_brightness(i, i, exit_pos, cell)
            assert brightness >= 0
    
    def test_brightness_at_different_positions(self, lighting):
        """Verificar brillo en diferentes posiciones."""
        cell = Cell()
        exit_pos = (50, 50)
        
        positions = [(50, 50), (51, 50), (45, 45), (55, 55), (0, 0)]
        brightnesses = []
        
        for row, col in positions:
            brightness = lighting.calculate_brightness(row, col, exit_pos, cell)
            brightnesses.append(brightness)
            assert 0 <= brightness <= 255


class TestCalculateLinesBrightness:
    """Tests para calculate_lines_brightness."""
    
    @pytest.fixture
    def lighting(self):
        """Fixture para crear instancia de LightingSystem."""
        return LightingSystem()
    
    def test_lines_entrance_brightness(self, lighting):
        """Verificar brillo de líneas en la entrada."""
        distance = 0
        exit_pos = (50, 50)
        
        brightness = lighting.calculate_lines_brightness(0, 0, exit_pos)
        assert brightness >= 50  # BASE_BRIGHTNESS_LINES_ENTRANCE
    
    def test_lines_exit_brightness_zero(self, lighting):
        """Verificar brillo de líneas en la salida es 0."""
        exit_pos = (10, 10)
        
        brightness = lighting.calculate_lines_brightness(10, 10, exit_pos)
        assert brightness == 0
    
    def test_lines_brightness_decreases_with_distance(self, lighting):
        """Verificar que el brillo de líneas disminuye con la distancia."""
        exit_pos = (50, 50)
        
        brightness_near = lighting.calculate_lines_brightness(51, 50, exit_pos)
        brightness_far = lighting.calculate_lines_brightness(60, 50, exit_pos)
        
        assert brightness_near >= brightness_far
    
    def test_lines_brightness_non_negative(self, lighting):
        """Verificar que el brillo de líneas nunca es negativo."""
        exit_pos = (0, 0)
        
        for i in range(0, 100, 10):
            brightness = lighting.calculate_lines_brightness(i, i, exit_pos)
            assert brightness >= 0
    
    def test_lines_brightness_range(self, lighting):
        """Verificar que el brillo de líneas está en rango válido."""
        exit_pos = (50, 50)
        
        positions = [(50, 50), (51, 50), (45, 45), (55, 55), (0, 0), (99, 99)]
        
        for row, col in positions:
            brightness = lighting.calculate_lines_brightness(row, col, exit_pos)
            assert 0 <= brightness <= 255


class TestLightingConsistency:
    """Tests para consistencia del sistema de iluminación."""
    
    @pytest.fixture
    def lighting(self):
        """Fixture para crear instancia de LightingSystem."""
        return LightingSystem()
    
    def test_same_position_same_brightness(self, lighting):
        """Verificar que la misma posición da el mismo brillo."""
        cell = Cell(num_antorchas=2)
        exit_pos = (50, 50)
        
        brightness1 = lighting.calculate_brightness(10, 10, exit_pos, cell)
        brightness2 = lighting.calculate_brightness(10, 10, exit_pos, cell)
        
        assert brightness1 == brightness2
    
    def test_lines_same_position_same_brightness(self, lighting):
        """Verificar que la misma posición da el mismo brillo de líneas."""
        exit_pos = (50, 50)
        
        brightness1 = lighting.calculate_lines_brightness(10, 10, exit_pos)
        brightness2 = lighting.calculate_lines_brightness(10, 10, exit_pos)
        
        assert brightness1 == brightness2
    
    def test_symmetric_positions(self, lighting):
        """Verificar que posiciones equidistantes tienen brillo similar."""
        cell = Cell()
        exit_pos = (50, 50)
        
        # Posiciones a misma distancia de la salida
        brightness_north = lighting.calculate_brightness(45, 50, exit_pos, cell)
        brightness_south = lighting.calculate_brightness(55, 50, exit_pos, cell)
        brightness_east = lighting.calculate_brightness(50, 55, exit_pos, cell)
        brightness_west = lighting.calculate_brightness(50, 45, exit_pos, cell)
        
        # Deben ser iguales (misma distancia)
        assert brightness_north == brightness_south == brightness_east == brightness_west


class TestEdgeCases:
    """Tests para casos especiales."""
    
    @pytest.fixture
    def lighting(self):
        """Fixture para crear instancia de LightingSystem."""
        return LightingSystem()
    
    def test_zero_torches(self, lighting):
        """Verificar comportamiento con 0 antorchas."""
        cell = Cell(num_antorchas=0)
        exit_pos = (50, 50)
        
        brightness = lighting.calculate_brightness(10, 10, exit_pos, cell)
        assert brightness >= 0
    
    def test_many_torches(self, lighting):
        """Verificar comportamiento con muchas antorchas."""
        cell = Cell(num_antorchas=100)  # Cantidad irreal
        exit_pos = (50, 50)
        
        brightness = lighting.calculate_brightness(10, 10, exit_pos, cell)
        assert brightness <= 255  # No debe exceder límite RGB
    
    def test_exit_at_origin(self, lighting):
        """Verificar comportamiento cuando la salida está en (0,0)."""
        cell = Cell()
        exit_pos = (0, 0)
        
        brightness = lighting.calculate_brightness(0, 0, exit_pos, cell)
        assert brightness == 0  # En la salida
        
        brightness_near = lighting.calculate_brightness(1, 0, exit_pos, cell)
        assert brightness_near > 0  # Fuera de la salida
    
    def test_far_from_exit(self, lighting):
        """Verificar comportamiento muy lejos de la salida."""
        cell = Cell()
        exit_pos = (0, 0)
        
        brightness = lighting.calculate_brightness(100, 100, exit_pos, cell)
        assert brightness >= 0
    
    def test_special_cell_types(self, lighting):
        """Verificar comportamiento con tipos especiales de celdas."""
        exit_pos = (50, 50)
        
        inicio = Cell(tipo=CellType.INICIO)
        habitacion = Cell(tipo=CellType.HABITACION)
        cthulhu = Cell(tipo=CellType.CTHULHU)
        
        # Todos deben calcular brillo sin errores
        b1 = lighting.calculate_brightness(10, 10, exit_pos, inicio)
        b2 = lighting.calculate_brightness(10, 10, exit_pos, habitacion)
        b3 = lighting.calculate_brightness(10, 10, exit_pos, cthulhu)
        
        assert all(0 <= b <= 255 for b in [b1, b2, b3])
