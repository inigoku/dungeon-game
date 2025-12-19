"""Tests extendidos para services/lighting_system.py - Cobertura 75%+"""
import pytest
from services.lighting_system import LightingSystem
from models.cell import CellType


class TestLightingSystemExtended:
    """Tests adicionales para alcanzar 75% de cobertura."""
    
    def test_calculate_base_brightness_start(self):
        """Test brillo base al inicio."""
        lighting = LightingSystem()
        brightness = lighting.calculate_base_brightness(0, 100)
        assert brightness == 20  # BASE_BRIGHTNESS_ENTRANCE
    
    def test_calculate_base_brightness_end(self):
        """Test brillo base al final."""
        lighting = LightingSystem()
        brightness = lighting.calculate_base_brightness(100, 100)
        assert brightness == 0
    
    def test_calculate_base_brightness_middle(self):
        """Test brillo base en el medio."""
        lighting = LightingSystem()
        brightness = lighting.calculate_base_brightness(50, 100)
        assert brightness == 10
    
    def test_calculate_base_brightness_zero_distance(self):
        """Test con distancia total cero."""
        lighting = LightingSystem()
        brightness = lighting.calculate_base_brightness(0, 0)
        assert brightness == 10  # progress = 0.5
    
    def test_calculate_brightness_factor(self):
        """Test conversión de brillo a factor."""
        lighting = LightingSystem()
        assert lighting.calculate_brightness_factor(0) == 0.0
        assert lighting.calculate_brightness_factor(255) == 1.0
        assert lighting.calculate_brightness_factor(127.5) == pytest.approx(0.5)
    
    def test_calculate_lines_brightness_pasillo(self):
        """Test brillo de líneas para pasillo."""
        lighting = LightingSystem()
        factor = lighting.calculate_lines_brightness_factor(CellType.PASILLO, 0, 100)
        assert 0 <= factor <= 1.0
    
    def test_calculate_lines_brightness_habitacion(self):
        """Test brillo de líneas para habitación."""
        lighting = LightingSystem()
        factor = lighting.calculate_lines_brightness_factor(CellType.HABITACION, 50, 100)
        assert 0 <= factor <= 1.0
    
    def test_calculate_lines_brightness_salida(self):
        """Test brillo de líneas para salida."""
        lighting = LightingSystem()
        factor = lighting.calculate_lines_brightness_factor(CellType.SALIDA, 100, 100)
        assert factor >= 0
    
    def test_calculate_lines_brightness_inicio(self):
        """Test brillo de líneas para inicio."""
        lighting = LightingSystem()
        factor = lighting.calculate_lines_brightness_factor(CellType.INICIO)
        assert factor > 0
    
    def test_calculate_lines_brightness_empty(self):
        """Test brillo de líneas para celda vacía."""
        lighting = LightingSystem()
        factor = lighting.calculate_lines_brightness_factor(CellType.EMPTY)
        assert factor == 1.0
    
    def test_calculate_lines_brightness_zero_distance(self):
        """Test brillo de líneas con distancia cero."""
        lighting = LightingSystem()
        factor = lighting.calculate_lines_brightness_factor(CellType.PASILLO, 0, 0)
        assert 0 <= factor <= 1.0
    
    def test_calculate_lines_brightness_darkening_disabled(self):
        """Test brillo de líneas con oscurecimiento desactivado."""
        lighting = LightingSystem()
        lighting.lines_darkening_enabled = False
        
        factor = lighting.calculate_lines_brightness_factor(CellType.PASILLO, 50, 100)
        assert factor == 1.0
    
    def test_calculate_lines_brightness_inicio_no_darkening(self):
        """Test brillo de líneas en inicio sin oscurecimiento."""
        lighting = LightingSystem()
        lighting.lines_darkening_enabled = False
        
        factor = lighting.calculate_lines_brightness_factor(CellType.INICIO)
        assert factor == 1.0
    
    def test_apply_blood_darkening_min(self):
        """Test oscurecimiento de sangre con brillo mínimo."""
        lighting = LightingSystem()
        darkened = lighting.apply_blood_darkening(0.0)
        assert darkened == 0.5  # 50% darkening
    
    def test_apply_blood_darkening_max(self):
        """Test oscurecimiento de sangre con brillo máximo."""
        lighting = LightingSystem()
        darkened = lighting.apply_blood_darkening(1.0)
        assert darkened == 1.0
    
    def test_apply_blood_darkening_middle(self):
        """Test oscurecimiento de sangre con brillo medio."""
        lighting = LightingSystem()
        darkened = lighting.apply_blood_darkening(0.5)
        assert 0.5 <= darkened <= 1.0
    
    def test_toggle_lines_darkening(self):
        """Test toggle del oscurecimiento de líneas."""
        lighting = LightingSystem()
        initial = lighting.lines_darkening_enabled
        
        result = lighting.toggle_lines_darkening()
        assert result != initial
        
        result2 = lighting.toggle_lines_darkening()
        assert result2 == initial
    
    def test_toggle_lines_darkening_returns_state(self):
        """Test que toggle retorna el nuevo estado."""
        lighting = LightingSystem()
        lighting.lines_darkening_enabled = True
        
        result = lighting.toggle_lines_darkening()
        assert result == False
        assert lighting.lines_darkening_enabled == False
