"""Tests simplificados para services/lighting_system.py"""
import pytest
from services.lighting_system import LightingSystem


class TestLightingSystemBasics:
    """Tests básicos del sistema de iluminación."""
    
    def test_initialization(self):
        """Verificar que el sistema se inicializa correctamente."""
        lighting = LightingSystem()
        assert lighting is not None
        assert hasattr(lighting, 'lines_darkening_enabled')
    
    def test_calculate_brightness_exists(self):
        """Verificar que el método calculate_brightness existe."""
        lighting = LightingSystem()
        assert hasattr(lighting, 'calculate_brightness')
        assert callable(lighting.calculate_brightness)
    
    def test_calculate_brightness_with_zero_torches(self):
        """Verificar cálculo de brillo sin antorchas."""
        lighting = LightingSystem()
        base = 50
        torches = 0
        brightness = lighting.calculate_brightness(base, torches)
        assert brightness >= 0
        assert brightness <= 255
    
    def test_calculate_brightness_with_torches(self):
        """Verificar que las antorchas aumentan el brillo."""
        lighting = LightingSystem()
        base = 50
        
        brightness_no_torches = lighting.calculate_brightness(base, 0)
        brightness_with_torches = lighting.calculate_brightness(base, 3)
        
        assert brightness_with_torches > brightness_no_torches
    
    def test_lines_darkening_enabled_by_default(self):
        """Verificar que lines_darkening está habilitado por defecto."""
        lighting = LightingSystem()
        assert lighting.lines_darkening_enabled == True
    
    def test_brightness_non_negative(self):
        """Verificar que el brillo nunca es negativo."""
        lighting = LightingSystem()
        
        test_cases = [
            (0, 0),
            (10, 0),
            (50, 2),
            (100, 5),
            (20, 1)
        ]
        
        for base, torches in test_cases:
            brightness = lighting.calculate_brightness(base, torches)
            assert brightness >= 0, f"Brightness negativo para base={base}, torches={torches}"
